import torch
import json
from transformers import AutoModelForCausalLM, AutoTokenizer
import openai
import re


class LLModel:
    current_location = "Somwhere arbitrary in the lab"

    do_nothing = """
        {
            "name": "do_nothing"
        }
        """.strip()
        
    function_definitions = """
    [
        {
            "name": "get_robot_response",
            "description": "Generate a response from the agent.",
            "parameters": {
                "user_input": "most recent lines of text from the conversation to prompt the agent. Should not be responses from the agent labeled 'Dobby'"
            }
        },
        {
            "name": "do_nothing",
            "description": "Do nothing, as Dobby is not needed."
        }
    ]
    """

    system_prompt = """You are currently in the Living with Robots lab in the AHG building at the University of Texas at Austin.
    You are a domestic service robot who was programmed by students doing research for the living with robots lab.
    You are named Dobby.
    You use chatGPT to generate action plans and interact with humans using natural language.

    Sometimes people might think your name is Tobi or Dabi or something similar. You are currently in {currrent}.
    
    More often than not, you should respond and talk to people. The lab has things such as the following, if someone mentions them they might be curious:
        
    Astro Robot
    BWI Bots
    BWIV5 Robot
    Boston Dynamics Spot Robot
    Drone Cage
    Husky and Jackel Autonomous Vehicles
    Mock Apartment
    RoboCup@Home Robot
    Robot Manipulator
    Social Navigation Hallway
    
    Consider what was said the latest (at the bottom of the transcript) most importantly over anything else. Consider it in context of the line before it too.
    
    Based on the conversation you overheard, you will call one of the provided functions. 

    Choose only one function to invoke. Your response should only be a JSON object. Do not include any other text, formatting, or Markdown syntax (like triple backticks or language specifiers). The JSON object should look like this:
    {{
        "name": "get_robot_response",
        "parameters": {{
            "user_input": "Text from the conversation to prompt the agent."
        }}
    }}
    Here is a list of functions in JSON format that you can invoke:

    {functions}
    """.format(functions=function_definitions, current = current_location)


    def __init__(self, api_key):
        openai.api_key = api_key
    
    def set_location(self, name):
        print("\n\n just entered:" + name)
        self.current_location = name
        # Update the system prompt dynamically
        self.system_prompt = self.system_prompt_template.format(
            functions=self.function_definitions, current=self.current_location
        )

    # get response from GPT given the transcription of the conversation
    # heard by Dobby
    def appropriate_action(self, conversation):
        #if conversation is empty don't invoke model
        if not re.search(r"[a-z]", conversation, flags=re.IGNORECASE):
            return self.do_nothing


        # Combine the system prompt and user conversation
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": conversation}
        ]

        # Generate response using GPT
        try:
            chat_completion = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=messages
            )

            # Extract and return the assistant's reply
            result = chat_completion.choices[0].message.content.strip()
            print("result" + result)  # Debugging output
            return result
        except Exception as e:
            print(f"Error generating response: {e}")
            return None