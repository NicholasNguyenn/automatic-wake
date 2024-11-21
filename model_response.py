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

class LLModel:
    #model_name = r"C:\Users\Nick\.cache\huggingface\hub\models--meta-llama--Llama-3.2-3B-Instruct\snapshots\392a143b624368100f77a3eafaa4a2468ba50a72"
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
        },
        {
            "name": "do_a_dance",
            "description": "Perform an obnoxious dance."
        }
    ]
    """

    system_prompt = """You are a conversational robot named Dobby. 
    Based on the conversation you overheard, you will call one of the provided functions.

    Choose only one function to invoke. Your response should be formatted like:
    {{
        "name": "get_robot_response",
        "parameters": {{
            "user_input": "Text from the conversation to prompt the agent."
        }}
    }}
    You SHOULD NOT include any other text in the response.
    Here is a list of functions in JSON format that you can invoke:

    {functions}
    """.format(functions=function_definitions)




    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        #self.model_name = r"C:\Users\Nick\.cache\huggingface\hub\models--meta-llama--Llama-3.2-3B-Instruct\snapshots\392a143b624368100f77a3eafaa4a2468ba50a72"
        self.model_name = r"C:\Users\jlars\.cache\huggingface\hub\models--meta-llama--Llama-3.2-3B\snapshots\13afe5124825b4f3751f836b40dafda64c1ed062"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(self.model_name).to(self.device)


    # get response from Llama given the transcription of the conversation
    # heard by Dobby
    def appropriate_action(self, conversation):

        print("Current device: ", torch.cuda.current_device())
        print("GPU name: ", torch.cuda.get_device_name(torch.cuda.current_device()))
        
        #create prompt
        prompt = (
            f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>"
            f"{self.system_prompt}<|eot_id|>"
            f"<|start_header_id|>user<|end_header_id|>"
            f"{conversation}<|eot_id|>"
            f"<|start_header_id|>assistant<|end_header_id|>"
        )

        torch.cuda.empty_cache()

        # Encode the input prompt
        inputs = self.tokenizer(prompt, return_tensors="pt")
        
        # Move input tensors to the GPU if available
        inputs = {key: value.to(self.device) for key, value in inputs.items()}

        # Generate output using the model
        with torch.no_grad():
            # Adjust max_length for longer/shorter responses
            output = self.model.generate(**inputs, max_length=500, num_return_sequences=1
                                         ,temperature=0.7, top_p=0.9, repetition_penalty=1.2
                                         ,eos_token_id=self.tokenizer.eos_token_id)
        
        # Decode the output tokens to string
        response = self.tokenizer.decode(output[0], skip_special_tokens=True).strip()

        print(response)

        result = response.split("assistant")[1]

        return result
