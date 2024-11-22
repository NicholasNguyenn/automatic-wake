import torch
import json
from transformers import AutoModelForCausalLM, AutoTokenizer
from openai import OpenAI

# Check if GPU is available
    # device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


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
        },
        {
            "name": "do_a_dance",
            "description": "Perform an obnoxious dance."
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




    # def __init__(self):
    #     self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    #     #self.model_name = r"C:\Users\Nick\.cache\huggingface\hub\models--meta-llama--Llama-3.2-3B-Instruct\snapshots\392a143b624368100f77a3eafaa4a2468ba50a72"
    #     self.model_name = r"C:\Users\jlars\.cache\huggingface\hub\models--meta-llama--Llama-3.2-3B\snapshots\13afe5124825b4f3751f836b40dafda64c1ed062"
    #     self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
    #     self.model = AutoModelForCausalLM.from_pretrained(self.model_name).to(self.device)

    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)


    # get response from Llama given the transcription of the conversation
    # heard by Dobby
    def appropriate_action(self, conversation):
        
        #create prompt
        # prompt = (
        #     f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>"
        #     f"{self.system_prompt}<|eot_id|>"
        #     f"<|start_header_id|>user<|end_header_id|>"
        #     f"{conversation}<|eot_id|>"
        #     f"<|start_header_id|>assistant<|end_header_id|>"
        # )

        # torch.cuda.empty_cache()

        # # Encode the input prompt
        # inputs = self.tokenizer(prompt, return_tensors="pt")
        
        # # Move input tensors to the GPU if available
        # inputs = {key: value.to(self.device) for key, value in inputs.items()}

        # # Generate output using the model
        # with torch.no_grad():
        #     # Adjust max_length for longer/shorter responses
        #     output = self.model.generate(**inputs, max_length=500, num_return_sequences=1
        #                                  ,temperature=0.7, top_p=0.9, repetition_penalty=1.2
        #                                  ,eos_token_id=self.tokenizer.eos_token_id)
        
        # # Decode the output tokens to string
        # response = self.tokenizer.decode(output[0], skip_special_tokens=True).strip()

        # print(response)

        # result = response.split("assistant")[1]

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
