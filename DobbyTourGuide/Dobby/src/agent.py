import math
import re
from openai import OpenAI
from enum import Enum
from action import Action
import yaml
import os
import data as data
import json
import time
import elevator as elevator
import base64
import cv2

if data.ros_interface_on:
    import ros_interface as ros_interface
    import python_kinect
    
from functools import partial
from datetime import datetime

client = OpenAI(api_key=data.OPENAI_API_KEY)

audio_processor = None  # set later by driver
enqueue_callback = None  # set later by driver
set_receiving_response = None
set_event_flag = None # set later by driver

# Chat Setup
chat_initializer = ""
chat_log = f"{data.LOGS_DIR}{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
open(chat_log, "w").close()

actions = []
locations = {}
current_plan = None
current_room = data.STARTING_ROOM
doorway_exit = None

tour_sequence = [] if not data.linear_tour else open(data.TOUR_FILE, "r").readlines()

# State Control
class PlannerState(Enum):
    IDLE = 1  # waiting for new user
    CONVERSING = 2
    EXECUTING = 3
    ERROR = 4


global planner_state
planner_state = PlannerState.IDLE

def build_prompt():
    prompt = open(data.PROMPT_TEMPLATE).read()
    instructions = open(data.INSTRUCTIONS_FILE).read()
    background = open(data.BACKGROUND_FILE).read()
    prompt = prompt.replace("<insert instructions here>", instructions)
    prompt = prompt.replace("<insert background here>", background)
    return prompt

def reset_chat():
    global chat_history
    chat_history = [{"role": "system", "content": chat_initializer}]

def reset():
    global current_room
    if data.ros_interface_on:
        ros_interface.change_map_level(elevator.current_floor, 0)
        
    reset_chat()
    update_floor()
    
    if data.linear_tour:
        add_system_message("The planned tour destinations are: " + ", ".join(tour_sequence))


def get_state():
    return planner_state.name


log = print
def set_logger(log_fun):
    global log
    log = log_fun


send_response = None
def set_response_callback(callback_func):
    global send_response
    send_response = callback_func


def populate_locations():
    global locations
    global chat_initializer
    print("adding locations")

    info_str = ""
    with open(data.INFORMATION_FILE, "r") as file:
        infos = yaml.safe_load(file)
        for info_name in infos.keys():            
            info_str += "- " + info_name + ": " + infos[info_name] + "\n"
    chat_initializer = chat_initializer.replace("<insert information here>", info_str)

    landmarks_str = ""
    with open(data.LANDMARKS_FILE, "r") as file:
        landmarks = yaml.safe_load(file)
        for landmark in landmarks.keys():
            
            floor = landmarks[landmark]["floor"]
            if floor != data.STARTING_FLOOR and not data.switching_floors:
                continue
            if data.switching_floors:
                name = f"{landmark} (floor {floor})"
            else:
                name = landmark

            print(name)

            locations[name] = (
                (landmarks[landmark]["x"],
                landmarks[landmark]["y"],
                landmarks[landmark]["yaw"]),
                floor,
                landmarks[landmark]["room"],
                "" if "info" not in landmarks[landmark] else landmarks[landmark]["info"]
            )
            if "info" in landmarks[landmark] and not data.linear_tour:
                landmarks_str += "- " + name + ": " + landmarks[landmark]["info"] + "\n"
            else:
                landmarks_str += "- " + name + "\n"
                
    chat_initializer = chat_initializer.replace("<insert landmarks here>", landmarks_str)

    # create actions from locations
    for location_name, location in locations.items():
        goto_location = Action(
            location_name,
            action_function=delay_action
            if not data.ros_interface_on
            else partial(goto_location_action, location_name),
        )
        actions.append(goto_location)

    print("finished locations")

    reset_chat()


def change_room(room, next_pos):
    global current_room
    global action
    global doorway_exit

    print("Changing room")
    action = approach_doorway

    with open(data.DOORWAYS_FILE, "r") as file:
        doorways = yaml.safe_load(file)
        door_candidates = []
        exits = []
        for doorway in doorways.keys():
            if (doorways[doorway]["inside"]["room"] == current_room and doorways[doorway]["outside"]["room"] == room):
                door_candidates.append(doorways[doorway]["inside"])
                exits.append (doorways[doorway]["outside"])
            elif (doorways[doorway]["inside"]["room"] == room and doorways[doorway]["outside"]["room"] == current_room):
                door_candidates.append(doorways[doorway]["outside"])
                exits.append (doorways[doorway]["inside"])
        
        if len(door_candidates) == 0:
            add_system_message("There is no doorway between the current room and the destination. Please select a different destination.")
            return
        
        pos = ros_interface.get_position()
        x, y = pos["translation"]["x"], pos["translation"]["y"]
        min_dist = 1000
        closest_door = door_candidates[0]
        for door in door_candidates:
            pos = ros_interface.get_position()
            x, y = pos["translation"]["x"], pos["translation"]["y"]
            nx, ny = next_pos[0], next_pos[1]
            dist = math.sqrt((x - door["x"])**2 + (y - door["y"])**2) + math.sqrt((nx - door["x"])**2 + (ny - door["y"])**2) 

            print(dist)
            if dist < min_dist:
                min_dist = dist
                closest_door = door
        
        doorway_exit = exits[door_candidates.index(closest_door)]

        ros_interface.go_to_pos((closest_door["x"], closest_door["y"], closest_door["yaw"]), reached_goal=reached_doorway)

    current_room = room

def reached_doorway(result=None):
    global current_plan
    add_system_message("You are now at a doorway. Ask the user to open the door and let you know when to continue. When they are ready, continue the tour by calling the function.")
    current_plan.insert(0, go_through_doorway)
    enqueue_next_action()

def go_through_doorway():
    ros_interface.change_map_level(elevator.current_floor, 1)
    exit = (doorway_exit["pos_x"], doorway_exit["pos_y"], doorway_exit["rot_z"], doorway_exit["rot_w"])
    print (exit)
    ros_interface.go_to_pos(exit, reached_goal=exited_doorway, use_orientation=False)

def exited_doorway(result=None):
    ros_interface.change_map_level(elevator.current_floor, 0)
    time.sleep(1)
    enqueue_next_action()


current_location = ""
def goto_location_action(location_name):
    global current_location
    location = locations[location_name]
    current_location = location
    if elevator.current_floor != location[1]:
        try_elevator()
        current_plan.insert(0, partial(goto_location_action, location_name)) #readd this action to the front of the plan
    elif current_room != location[2]:
        change_room(location[2], location[0])
        current_plan.insert(0, partial(goto_location_action, location_name))    
    else:
        ros_interface.go_to_pos(location[0], reached_goal=enqueue_next_action)

def try_elevator():
    if elevator.current_floor == 1:
        if current_room != 1:
            change_room(1, elevator.location_of("ElevatorEntrance"))
        else:
            take_elevator(2)
    else:
        if current_room != 2:
            change_room(2, elevator.location_of("ElevatorEntrance"))
        else:
            take_elevator(1)

def take_elevator(floor):
    global action
    action = take_elevator_action
    add_system_message("Explain that you are going to control the elevator over wifi so the user does not have to touch the buttons. Tell them to let you go first on the way in and out.")
    elevator.take_elevator(floor, elevator_callback)

def elevator_callback(result=None):
    add_system_message(f"Elevator brought you to floor {elevator.current_floor}. Now going to destination.")
    global current_room
    current_room = elevator.current_floor
    enqueue_next_action()

def update_floor():
    add_system_message(f"You are currently on floor {elevator.current_floor}. Prefer destinations on this floor.")

def delay_action():
    time.sleep(6)
    enqueue_next_action()

def extract_plan(plan_list, options):
    steps = []
    for str_step in plan_list:
        if str_step not in options:
            myEmbedding = client.embeddings.create(input=[str_step], model="text-embedding-3-small").data[0].embedding
            matched_action = compareEmbedding(myEmbedding, options)
            if matched_action[1] < 0.8:  # Vectors are not sufficiently similar
                print("invalid action " + str_step)
                return (False, str_step)
        else:
            matched_action = str_step    
        
        steps.append(matched_action[0])

    return (True, steps)


def compareEmbedding(myEmbedding, options):
    max_similarity = (options[0], -1)
    for option in options:
        sim = cosine_similarity(myEmbedding, option.embedding)
        if sim > max_similarity[1]:
            max_similarity = (option, sim)
    return max_similarity

def cosine_similarity(vector_a, vector_b):
    dot_product = sum(a * b for a, b in zip(vector_a, vector_b))
    magnitude_a = math.sqrt(sum(a**2 for a in vector_a))
    magnitude_b = math.sqrt(sum(b**2 for b in vector_b))
    return dot_product / (magnitude_a * magnitude_b)


def chatGPT(
    user_input,
    system_messages,
    functions,
    log_file,
    chunk_callback=None,
    expected_function="auto",
    system_first=False,
    conversational=True,
):
    global chat_history

    with open(log_file, "a") as log:
        # Prevent context limit
        if len(chat_history) > 60:
            add_system_message("Summarize the most contextually important parts of this interaction in a few bullet points.")
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=chat_history
            )
            summary = response.choices[0].message["content"]
            print(summary)
            chat_history = [chat_history[0]] + [{"role": "system", "content": summary}] + chat_history[-5:]
            log.write("CLEARED HISTORY\n")

        # Fill in chat_history
        if not system_first and len(user_input) > 0:
            chat_history.append({"role": "user", "content": "USER: " + user_input})
            log.write("USER: " + user_input + "\n")

        for message in system_messages:
            chat_history.append({"role": "system", "content": message})
            log.write("SYSTEM: " + message + "\n")

        if system_first and len(user_input) > 0:
            chat_history.append({"role": "user", "content": "USER: " + user_input})
            log.write("USER: " + user_input + "\n")

        chat_history.append({"role": "system", "content": "Include an emotion from the list in parentheses at the start of each phrase or use neutral."})

        # API call
        if len(functions) == 0:
            response = client.chat.completions.create(model="gpt-4-turbo",
                messages=chat_history,
                stream=True)
        else:
            response = client.chat.completions.create(model="gpt-4-turbo",
                messages=chat_history,
                functions=functions,
                function_call=expected_function,
                stream=True)

        del chat_history[-1] #remove the "keep your response brief" message

        str_response = ""
        func_call = {
            "name": None,
            "arguments": "",
        }

        # iterate through the stream of events
        first_chunk = True
        for chunk in response:
            delta = chunk.choices[0].delta
            if delta.function_call:
                first_chunk = False
                if delta.function_call.name:
                    func_call["name"] = delta.function_call.name
                if delta.function_call.arguments:
                    func_call["arguments"] += delta.function_call.arguments
            else:
                chunk_message = delta.content if delta.content else ""  # extract the message
                str_response += chunk_message
                if send_response is not None:
                    if first_chunk and conversational:
                        send_response("ROBOT: ")
                        first_chunk = False
                    send_response(chunk_message) #send the chunk to the callback function

        # Log and clean up response
        if len(str_response) > 0:
            log.write(str_response + "\n")
            if conversational:
                str_response = re.sub(r"(^[^:]*:\s)|(\(.*\))", "", str_response)
            chat_history.append({"role": "assistant", "content": str_response})

        # Return the response or function call
        if func_call["name"] is None:
            log.close()
            return (str_response, None)

        func_call["arguments"] = func_call["arguments"].replace("{}", "").replace(" ", "")
        chat_history.append({'role': 'assistant', 'content': None, 'function_call': func_call})
        log.write(f"{func_call['name']}({func_call['arguments']})\n")
        log.close()
        return (str_response, func_call)

def encode_image(image):
    _, im_arr = cv2.imencode('.jpg', image)  # im_arr: image in Numpy one-dim array format.
    im_bytes = im_arr.tobytes()
    im_b64 = base64.b64encode(im_bytes).decode('utf-8')
    return im_b64

def add_image_context(image, text, history):
    image_b64 = encode_image(image)
    
    history.append({"role": "user", "content": 
        [
            {"type": "text", "text": text},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{image_b64}"
                }
            }
        ]
    })


def add_function_response(name, response, log_file):
    global chat_history
    chat_history.append({"role": "function", "name" : name, "content": response})
    with open(log_file, "a") as log:
        log.write(f"{name}: {response}\n")
        log.close()

def add_system_message(message):
    chat_history.append({"role": "system", "content": message})
    with open(chat_log, "a") as log:
        log.write(f"SYSTEM: {message}\n")
        log.close()


def action_list_str(action_list):
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

def start_linear_tour():
    global current_plan
    plan = extract_plan(tour_sequence, actions)
    if not plan[0]:
        print("invalid destinations in sequence")
        return
    
    current_plan = plan[1]
    return execute_plan()


def execute_plan(give_dialogue_queue=True):
    global planner_state
    global user_location
    plan_str = action_list_str(current_plan)
    planner_state = PlannerState.EXECUTING
    add_system_message("Starting tour with actions: " + plan_str)
    return start_next_action(give_dialogue_queue)


def start_next_action(give_dialogue_queue=True):
    global planner_state
    global current_plan
    global action

    if current_plan == None:
        return ""
    
    planner_state = PlannerState.EXECUTING

    if len(current_plan) > 0:
        action = current_plan[0]

        log("Executing: " + action.name, True)
        action.execute_action()
        del current_plan[0]

        #remove previous info message
        if data.linear_tour:
            for m in chat_history:
                if m["role"] == "system" and "Info about" in m["content"]:
                    chat_history.remove(m)
                    print ("removing info message")
                if isinstance(m["content"], list) and len(m["content"]) > 1 and m["content"][1]["type"] == "image_url":
                    print ("removing image")
                    chat_history.remove(m)

        #add context about destination
        if data.linear_tour and action.name in locations and locations[action.name][3] != "":
            add_system_message("Info about " + action.name + ": " + locations[action.name][3])

        if not give_dialogue_queue or ros_interface.distance_to_goal() < 0.5:
            return ""
        
        return chatGPT(
            "", ["Driving to: " + action.name + ". Briefly inform the user what you are doing and keep the conversation going. Try not to repeat information you already provided. Do not assume you have arrived at the location."], [],  chat_log, send_response, "none"
        )[0]

    else:
        planner_state = PlannerState.CONVERSING
        current_plan = None

        return chatGPT(
            "", ["Completed tour"], [],  chat_log, send_response, "none"
        )[0]
        
def speak_action(text):
    enqueue_callback(partial(speak, text))

def speak (text):
    set_receiving_response(True)
    send_response(text)
    set_receiving_response(False)

def finished_action(result=None):
    global planner_state

    if data.ros_interface_on:
        color_image = python_kinect.color_image
        add_image_context(color_image, "Visual context at destination.", chat_history)

    planner_state = PlannerState.CONVERSING

    if current_plan == None:
        print("no more actions in plan")
        return
    
    if data.ros_interface_on and not ros_interface.within_threshold(0.5):
        print("goal failed")
        set_receiving_response(True)
        response = chatGPT(
            "", ["Navigation Goal Failed"], [],  chat_log, send_response, "none"
        )[0]
        time.sleep(0.5)
        set_receiving_response(False)
        return 

    if not action.require_response:
        enqueue_callback(start_next_action)
        return

    if not audio_processor.speaking and not audio_processor.user_speaking:
        set_receiving_response(True)
        response = chatGPT(
            "", ["Reached Destination: " + action.name], [],  chat_log, send_response, "none"
        )[0]
        time.sleep(0.5)
        set_receiving_response(False)
    else:
        add_system_message("You've reached the destination: " + action.name + ". Inform the user next time you talk if needed")
        set_event_flag()

def enqueue_next_action(result=None):
    enqueue_callback(finished_action)

def cancel_execution():
    global planner_state
    global current_plan
    planner_state = PlannerState.CONVERSING
    current_plan = None
    if data.ros_interface_on:
        elevator.cancel_elevator()
        ros_interface.cancel_goal()


take_elevator_action = Action("Take Elevator", action_function=delay_action if not data.ros_interface_on else try_elevator, require_response=False)
approach_doorway = Action("Doorway", action_function=delay_action if not data.ros_interface_on else change_room)
go_through_doorway = Action("Go Through Doorway", action_function=delay_action if not data.ros_interface_on else go_through_doorway, require_response=False)
cancel_action = Action("Cancel", action_function=cancel_execution)

def setup():
    global actions
    global chat_initializer

    chat_initializer = build_prompt()

    if data.switching_floors:
        actions = [cancel_action, take_elevator_action]
    else:
        actions = [cancel_action]

    if data.can_preform_actions:
        populate_locations()

    reset()

functions = [
    {
        "name": "start_tour",
        "description": "Immediately begin executing the provided tour." + \
        "You should briefly confirm the general plan with the user and ask any clarifying questions before calling this function." + \
        "If the robot is not capable of meeting the user's request, explain this to the user and do not call this function." + \
        "Call this function before providing any additional information to the user, which can be discussed after you start the actions.",
        "parameters": {
            "type": "object",
            "properties": {
                "destination_sequence": {
                    "type": "array",
                    "description": "An ordered sequence of destinations on the tour",
                    "items": {
                        "type": "string"
                    },
                }
            },
            "required": ["action_sequence"],
        },
    },
    {
        "name": "continue_tour",
        "description": "Move on to the next destination in the planned sequence." + \
        "You should only call this when a tour with multiple steps is currently in progress.",
        "parameters": {
            "type": "object",
            "properties": {
                "blank": {
                    "type": "string",
                    "description": "not required",
                }
            },
            "required": [],
        },
    },
    {
        "name": "ignore_input",
        "description": "Because all audio is transcribed, the user will often be speaking to another person in a group. Use this if the user is likely not addressing you, is likely speakingand to someone else, or if a response is not required.",
        "parameters": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "reason to skip input",
                }
            },
            "required": [],
        },
    },
    {
        "name": "cancel_tour",
        "description": "Immediately cancel the action that the robot is currently executing." + \
        "You should only call this if a tour is being executed and the user would like to alter or cancel it.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Cancels the action",
                }
            },
            "required": [],
        },
    }
]

linear_functions = [
    {
        "name": "continue_tour",
        "description": "Move on to the next destination in the planned sequence or start the tour",
        "parameters": {
            "type": "object",
            "properties": {
                "blank": {
                    "type": "string",
                    "description": "not required",
                }
            },
            "required": [],
        },
    },
    {
        "name": "ignore_input",
        "description": "Because all audio is transcribed, the user will often be speaking to another person in a group. Use this if the user is likely not addressing you, is likely speakingand to someone else, or if a response is not required.",
        "parameters": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "reason to skip input",
                }
            },
            "required": [],
        },
    },
]

def process_user_input(user_input):
    global current_plan
    global planner_state
    global user_location
    global log

    if user_input == "reset":
        reset()
        planner_state = PlannerState.CONVERSING
        log("SYSTEM RESET", True)
        return (0, "My memory has been erased.")

    try:
        response = chatGPT(user_input, [], linear_functions if data.linear_tour else functions,  chat_log, send_response)
    except Exception as e:
        print(e)
        log("")
        log("Rate limit error. Try again later or reduce context.", True)
        return (0, "")
    
    if response[1] is None:
        # just conversing
        if planner_state == PlannerState.IDLE:
            planner_state = PlannerState.CONVERSING
        return (0, response[0])
    else:
        # function called
        if response[1]["name"] == "cancel_tour":
            cancel_execution()
            add_function_response("cancel_tour", "You successfully canceled the tour",  chat_log)
            return (3, chatGPT("", ["make a new plan or inform the user that you canceled the plan"], functions,  chat_log, send_response)[0]) #now inform user plan was canceled or create a new one
        elif response[1]["name"] == "start_tour":
            if current_plan != None:
                cancel_execution()

            print(response[1]["arguments"])
            plan = extract_plan(json.loads(response[1]["arguments"]).get("destination_sequence"), actions)
            attempts = 1
            while not plan[0] and attempts < 3:
                #invalid plan, will try to correct
                attempts += 1
                add_function_response("start_actions", f"'{plan[1]}' does not match any valid actions. Be sure to use only actions provided in the initial prompt.",  chat_log)
                response = chatGPT("", [], functions, chat_log, send_response)
                if response[1] == None: #abandoned the attempt, must be invalid request
                    return (0, response[0])
                plan = extract_plan(json.loads(response[1]["arguments"]).get("destination_sequence"), actions)
            
            if not plan[0]:
                return (0, chatGPT("", ["the robot is not capable of meeting this request"], functions,  chat_log, send_response, "none")[0])

            current_plan = plan[1]
            #correct_plan(current_plan)
            add_function_response("start_tour", "successfully started the tour",  chat_log)
            
            #check if dialogue was already provided with function call
            if response[0] != None and len(response[0]) > 0:
                send_response("\n")
                execute_plan(False)
                return (1, response[0])
            
            return (1, execute_plan())
        elif response[1]["name"] == "continue_tour":
            if current_plan == None or len(current_plan) == 0:
                if data.linear_tour:
                    add_function_response("continue_tour", "successfully started the tour",  chat_log)
                    return (1, start_linear_tour())
                else:
                    add_system_message("the robot is not currently executing a tour")
                    return process_user_input(user_input)
            if planner_state == PlannerState.EXECUTING:
                add_system_message("the robot hasn't reached the current destination yet")
                return (0, response[0])
            return (1, start_next_action())
        elif response[1]["name"] == "ignore_input":
            add_function_response("ignore_input", "ignoring user input",  chat_log)
            return (0, "")
        else:
            # function name does not match
            print (response[1]["name"] + " was invalid")
            chat_history.append({"role": "system", "content": "the provided function name is invalid"})
            return process_user_input("")