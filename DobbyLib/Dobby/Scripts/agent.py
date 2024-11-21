import math
import re
import openai
from enum import Enum
from Dobby.Scripts.environment_state import Action, Predicate
import yaml
import os
import Dobby.Scripts.config as config
import json
import time

from functools import partial
from datetime import datetime

openai.api_key = config.OPENAI_API_KEY

# State Control
class PlannerState(Enum):
    IDLE = 1  # waiting for new user
    CONVERSING = 2
    EXECUTING = 3
    ERROR = 4
    
class Agent:
    def __init__(self, prompt, actions, predicates, cancel_actions, audio_processor, set_event_flag, send_response):
        self.planner_state = PlannerState.IDLE
        self.actions = actions
        self.predicates = predicates
        self.cancel_actions = cancel_actions
        self.current_plan = None
        self.current_action = None
        self.chat_history = []

        self.chat_log = f"{config.LOGS_DIR}{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
        open(self.chat_log, "w").close()
        
        self.audio_processor = audio_processor
        self.set_event_flag = set_event_flag
        self.send_response = send_response
        self.log = self.default_logger
        self.current_location = ""
        self.chat_initializer = prompt

        self.functions = []
        with open("Dobby/Scripts/functions.json", "r") as file:
            self.functions = json.load(file)

        self.reset()

    def default_logger(self, message, system=False, end="\n"):
        print (message, end=end)

    def set_logger(self, logger):
        self.log = logger

    def reset_chat(self):
        self.chat_history = [{"role": "system", "content": self.chat_initializer}]

    def reset_environment(self):
        for p in self.predicates:
            p.reset()

    def reset(self):
        self.reset_chat()
        self.reset_environment()

    def get_state(self):
        return self.planner_state.name

    def extract_plan(self, plan_list, options):
        steps = []
        for str_step in plan_list:
            print(str_step)
            if str_step not in options:
                myEmbedding = openai.Embedding.create(
                    input=str_step, engine="text-embedding-ada-002"
                )["data"][0]["embedding"]
                matched_action = self.compareEmbedding(myEmbedding, options)
                if matched_action[1] < 0.8:  # Vectors are not sufficiently similar
                    print("invalid action " + str_step)
                    return (False, str_step)
            else:
                matched_action = str_step    
            
            steps.append(matched_action[0])

        return (True, steps)


    def compareEmbedding(self, myEmbedding, options):
        max_similarity = (options[0], -1)
        for option in options:
            sim = self.cosine_similarity(myEmbedding, option.embedding)
            if sim > max_similarity[1]:
                max_similarity = (option, sim)
        return max_similarity

    def cosine_similarity(self, vector_a, vector_b):
        dot_product = sum(a * b for a, b in zip(vector_a, vector_b))
        magnitude_a = math.sqrt(sum(a**2 for a in vector_a))
        magnitude_b = math.sqrt(sum(b**2 for b in vector_b))
        return dot_product / (magnitude_a * magnitude_b)


    def chatGPT(self,
        user_input,
        system_messages,
        functions,
        history,
        log_file,
        expected_function="auto",
        system_first=False,
        conversational=True,
    ):

        with open(log_file, "a") as log:
            # prevent context limit
            if len(history) > 40:
                self.add_system_message("Summarize the most contextually important parts of this interaction in a few bullet points.")
                response = openai.ChatCompletion.create(
                    model="gpt-4-0613",
                    messages=history
                )
                summary = response["choices"][0]["message"]["content"]
                print(summary)
                history = [history[0]] + [{"role": "system", "content": summary}] + history[-5:-1]
                log.write("CLEARED HISTORY\n")

            # fill in history
            if not system_first and len(user_input) > 0:
                history.append({"role": "user", "content": "USER:" + user_input})
                log.write("USER:" + user_input + "\n")
            for message in system_messages:
                history.append({"role": "system", "content": message})
                log.write("SYSTEM: " + message + "\n")
            if system_first and len(user_input) > 0:
                history.append({"role": "user", "content": "USER:" + user_input})
                log.write("USER: " + user_input + "\n")

            if conversational:
                history.append({"role": "system", "content": "Keep your response under 3 sentences."}) #Include an emotion from the list in parantheses at the start."})

            # API call
            if len(functions) > 0:
                response = openai.ChatCompletion.create(
                    model="gpt-4-0613",
                    messages=history,
                    functions=functions,
                    function_call=expected_function,
                    stream=True,
                )
            else:
                response = openai.ChatCompletion.create(
                    model="gpt-4-0613",
                    messages=history,
                    stream=True,
                )
                
            del history[-1] #remove the "keep your response brief" message

            str_response = ""
            func_call = {
                "name": None,
                "arguments": "",
            }

            # iterate through the stream of events
            first_chunk = True
            for chunk in response:
                delta = chunk["choices"][0]["delta"]
                if "function_call" in delta:
                    first_chunk = False
                    if "name" in delta.function_call:
                        func_call["name"] = delta.function_call["name"]
                    if "arguments" in delta.function_call:
                        func_call["arguments"] += delta.function_call["arguments"]
                else:
                    chunk_message = delta.get("content", "")  # extract the message
                    str_response += chunk_message
                    if self.send_response is not None:
                        if first_chunk and conversational:
                            self.send_response("ROBOT: ")
                            first_chunk = False
                        self.send_response(chunk_message) #send the chunk to the callback function

            if len(str_response) > 0:
                log.write(str_response + "\n")
                if conversational:  # removes parentheticals and tags like "BOB:"
                    str_response = re.sub(r"(^[^:]*:\s)|(\(.*\))", "", str_response)
                history.append({"role": "assistant", "content": str_response})

            if func_call["name"] is None:
                log.close()
                return (str_response, None)

            history.append({'role': 'assistant', 'content': None, 'function_call': func_call})
            log.write(f"{func_call['name']}({func_call['arguments']})\n")
            log.close()
            return (str_response, func_call)

    def add_function_response(self, name, response, history, log_file):
        history.append({"role": "function", "name" : name, "content": response})
        with open(log_file, "a") as log:
            log.write(f"{name}: {response}\n")
            log.close()

    def add_system_message(self, message):
        self.chat_history.append({"role": "system", "content": message})
        with open(self.chat_log, "a") as log:
            log.write(f"SYSTEM: {message}\n")
            log.close()

    def correct_plan(self, plan):
        actions_taken = []
        while len(plan) > 0:
            # find first valid action
            next_action = None
            for option in plan:
                if option.is_valid() and (
                    len(actions_taken) == 0 or option.name != actions_taken[-1]
                ):
                    if option.name == "done":
                        actions_taken.append("done")
                        return actions_taken
                    next_action = option
                    break

            if next_action == None:
                actions_taken.append("done")
                return False

            actions_taken.append(next_action)  # append next step to plan
            next_action.result()  # change state of environment based on action
            plan.remove(next_action)

        return (True, actions_taken)


    def action_list_str(self, action_list):
        if len(action_list) == 0:
            return "none"

        action_str = "1."
        count = 2
        for action in action_list:
            if count == len(action_list) + 1:
                action_str += action.name
            else:
                action_str += f"{action.name}, {count}."
            count += 1

        return action_str


    def execute_plan(self, give_dialogue_queue=True):
        plan_str = self.action_list_str(self.current_plan)
        self.planner_state = PlannerState.EXECUTING
        self.add_system_message("Starting plan with actions: " + plan_str)
        return self.start_next_action(give_dialogue_queue)


    def start_next_action(self, give_dialogue_queue=True):
        if self.current_plan == None:
            return ""
        
        self.planner_state = PlannerState.EXECUTING

        if len(self.current_plan) > 0:
            self.current_action = self.current_plan[0]

            self.log("Executing: " + self.current_action.name, True)
            self.current_action.execute_action()
            del self.current_plan[0]

            if not give_dialogue_queue:
                return ""
            
            return self.chatGPT(
                "", ["Starting action: " + self.current_action.name + ". Briefly inform the user what you are doing and keep the conversation going. Do not assume you have completed the action without being notified."], [], self.chat_history, self.chat_log, "none"
            )[0]

        else:
            self.planner_state = PlannerState.CONVERSING
            self.current_plan = None

            return self.chatGPT(
                "", ["Completed plan"], [], self.chat_history, self.chat_log, self.send_response, "none"
            )[0]


    def finished_action(self):
        if self.current_plan == None:
            return

        if not self.current_action.require_response:
            self.start_next_action()
        
        self.planner_state = PlannerState.CONVERSING

        if not self.audio_processor.recording and not self.audio_processor.speaking:
            self.set_receiving_response(True)
            response = self.chatGPT(
                "", ["Completed Action"], [], self.chat_history, self.chat_log, "none"
            )[0]
            time.sleep(0.5)
            self.set_receiving_response(False)
        else:
            self.add_system_message("You've completed the current action. Make sure you inform the user next time you talk.")
            self.set_event_flag()

    def cancel_execution(self):
        self.planner_state = PlannerState.CONVERSING
        self.current_plan = None
        self.cancel_actions()

    def process_user_input(self, user_input):

        if user_input == "reset":
            self.reset()
            self.planner_state = PlannerState.CONVERSING
            self.log("SYSTEM RESET", True)
            return (0, "My memory has been erased.")

        try:
            response = self.chatGPT(user_input, [], self.functions if config.can_preform_actions else [], self.chat_history, self.chat_log)
        except Exception as e:
            print(e)
            self.log("")
            self.log("Rate limit error. Try again later or reduce context.", True)
            return (0, "")
        
        if response[1] is None:
            # just conversing
            if self.planner_state == PlannerState.IDLE:
                self.planner_state = PlannerState.CONVERSING
            return (0, response[0])
        else:
            # function called
            if response[1]["name"] == "end_conversation":
                self.add_function_response("end_conversation", "now ending the conversation", self.chat_history, self.chat_log)
                msg = json.loads(response[1]["arguments"]).get("goodbye_message")
                self.send_response(msg)
                return (2, msg)
            
            if response[1]["name"] == "cancel_actions":
                self.cancel_execution()
                self.add_function_response("cancel_actions", "You successfully canceled the plan", self.chat_history, self.chat_log)
                return (3, self.chatGPT("", ["make a new plan or inform the user that you canceled the plan"], self.functions, self.chat_history, self.chat_log)[0]) #now inform user plan was canceled or create a new one
            
            elif response[1]["name"] == "start_actions":
                if self.current_plan != None:
                    self.cancel_execution()

                plan = self.extract_plan(json.loads(response[1]["arguments"]).get("action_sequence"), self.actions)
                attempts = 1
                while not plan[0] and attempts < 3:
                    #invalid plan, will try to correct
                    attempts += 1
                    self.add_function_response("start_actions", f"'{plan[1]}' does not match any valid actions. Be sure to use only actions provided in the initial prompt.", self.chat_history, self.chat_log)
                    response = self.chatGPT("", [], self.functions, self.chat_history, self.chat_log)
                    if response[1] == None: #abandoned the attempt, must be invalid request
                        return (0, response[0])
                    plan = self.extract_plan(json.loads(response[1]["arguments"]).get("action_sequence"), self.actions)
                
                if not plan[0]:
                    return (0, self.chatGPT("", ["the robot is not capable of meeting this request"], self.functions, self.chat_history, self.chat_log, "none")[0])

                self.current_plan = plan[1]
                #correct_plan(self.current_plan)
                self.add_function_response("start_actions", "successfully started the plan", self.chat_history, self.chat_log)
                
                #check if dialogue was already provided with function call
                if response[0] != None and len(response[0]) > 0:
                    self.send_response("\n")
                    self.execute_plan(False)
                    return (1, response[0])
                
                return (1, self.execute_plan())
            
            elif response[1]["name"] == "continue_plan":
                if self.current_plan == None or len(self.current_plan) == 0:
                    self.add_system_message("the robot is not currently executing a plan")
                    return self.process_user_input(user_input)
                if self.planner_state == PlannerState.EXECUTING:
                    return (0, response[0])
                
                return (1, self.start_next_action())
            
            else:
                # function name does not match
                print (response[1]["name"] + " was invalid")
                self.chat_history.append({"role": "system", "content": "the provided function name is invalid"})
                return self.process_user_input("")