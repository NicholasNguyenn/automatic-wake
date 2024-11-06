import torch
import json
from transformers import AutoModelForCausalLM, AutoTokenizer

# Check if GPU is available
    # device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Load the tokenizer and model
# normal
#   model_name = r"C:\Users\Nick\.cache\huggingface\hub\models--meta-llama--Llama-3.2-1B\snapshots\221e3535e1ac4840bdf061a12b634139c84e144c"
# instruct
#   model_name = r"C:\Users\Nick\.cache\huggingface\hub\models--meta-llama--Llama-3.2-3B-Instruct\snapshots\392a143b624368100f77a3eafaa4a2468ba50a72"
# lab machine
    # model_name = "/home/bwilab/.cache/huggingface/hub/models--meta-llama--Llama-3.2-3B/snapshots/392a143b624368100f77a3eafaa4a2468ba50a72"
    # tokenizer = AutoTokenizer.from_pretrained(model_name)
    # model = AutoModelForCausalLM.from_pretrained(model_name).to(device)

class Model:
    model_name = "/home/bwilab/.cache/huggingface/hub/models--meta-llama--Llama-3.2-3B/snapshots/392a143b624368100f77a3eafaa4a2468ba50a72"
    function_definitions = """[
        {
            "name": "get_robot_response",
            "description": "Get a response from the agent based on the user's input. 
                            Calling this function would generate a response and 
                            cause Dobby to speak out loud",
            "parameters": {
                "user_input": {
                "type": "string",
                "description": "The text from the current conversation that the agent 
                                should respond to. This text is used to prompt the agent.
                                Should come directly from the user, such as the last few
                                lines from the current ongoing conversation"
                },
            }
            "name": "do_nothing",
            "description": "Nothing should be done because there is no indication 
                            that Dobby is needed",
            
            "name": "do_a_dance",
            "description": "Dance around like you just don't care. Very obnoxious 
                            but could be fun",
        }
    ]
    """
    system_prompt = """You are a converstional robot named Dobby in the robotics 
    building. You have overheard a conversation going on around you and have a set 
    of possible functions. Based on the conversation you have heard, you will need
    to make ONE function call to respond appropriately to the situation.

    When you decide to invoke a function, you MUST put it in the format of 
    [func_name1(params_name1=params_value1, params_name2=params_value2...)\n
    You SHOULD NOT include any other text in the response.

    Here is a list of functions in JSON format that you can 
    invoke.\n\n{functions}\n""".format(functions=function_definitions)

    def __init__(self):
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        model_name = "/home/bwilab/.cache/huggingface/hub/models--meta-llama--Llama-3.2-3B/snapshots/392a143b624368100f77a3eafaa4a2468ba50a72"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name).to(device)


    # get response from Llama given the transcription of the conversation
    # heard by Dobby
    def appropriate_action(self, conversation):
        #create prompt
        prompt = (
            f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>"
            f"{self.system_prompt}<|eot_id|>"
            f"<|start_header_id|>user<|end_header_id|>"
            f"{conversation}<|eot_id|>"
            f"<|start_header_id|>assistant<|end_header_id|>"
        )

        # Encode the input prompt
        inputs = self.tokenizer(prompt, return_tensors="pt")
        
        # Move input tensors to the GPU if available
        inputs = {key: value.to(self.device) for key, value in inputs.items()}

        # Generate output using the model
        with torch.no_grad():
            # Adjust max_length for longer/shorter responses
            output = self.model.generate(**inputs, max_length=200, num_return_sequences=1
                                    ,eos_token_id=self.tokenizer.eos_token_id)
        
        # Decode the output tokens to string
        response = self.tokenizer.decode(output[0], skip_special_tokens=True).strip()

        print(response)

        result = response.split("assistant")[1]

        return result
