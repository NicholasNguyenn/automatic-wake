import torch
import json
from transformers import AutoModelForCausalLM, AutoTokenizer
import openai
import re



class LLModel:
    function_definitions = """
    [
        {
            "name": "get_robot_response",
            "description": "Generate a response from the agent.",
            "parameters": {
                "user_input": "Text from the conversation to prompt the agent."
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
    You are name Dobby.
    You use chatGPT to generate action plans and interact with humans using natural language.
    Additionally, this system will serve as a platform to build off of and a way to showcase the software being developed in the lab.

    The lab has things such as the following, keep them in mind in case someone mentions them and they might be curious:
    
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
    """.format(functions=function_definitions)


    def __init__(self, api_key):
        openai.api_key = api_key


    # get response from GPT given the transcription of the conversation
    # heard by Dobby
    def appropriate_action(self, conversation):
        #if conversation is empty don't invoke model
        if not re.search(r"[a-z]", conversation, flags=re.IGNORECASE):
            return """
            {
                "name": "do_nothing"
            }
            """.strip()


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