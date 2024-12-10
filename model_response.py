import torch
import json
from transformers import AutoModelForCausalLM, AutoTokenizer
from openai import OpenAI


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

    system_prompt = """You are a conversational robot named Dobby. 
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
        self.client = OpenAI(api_key=api_key)


    # get response from GPT given the transcription of the conversation
    # heard by Dobby
    def appropriate_action(self, conversation):
        # Combine the system prompt and user conversation
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": conversation}
        ]

        # Generate response using GPT
        try:
            chat_completion = self.client.chat.completions.create(
            messages=messages,
            model="gpt-4o",
            )

            # Extract and return the assistant's reply
            result = chat_completion.choices[0].message.content.strip()
            print("result" + result)  # Debugging output
            return result
        except Exception as e:
            print(f"Error generating response: {e}")
            return None
