import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# Load the tokenizer and model
#normal
#model_name = r"C:\Users\Jackson\.cache\huggingface\hub\models--meta-llama--Llama-3.2-1B\snapshots\221e3535e1ac4840bdf061a12b634139c84e144c"
#instruct
model_name = r"C:\Users\Jackson\.cache\huggingface\hub\models--meta-llama--Llama-3.2-1B-Instruct\snapshots\e9f8effbab1cbdc515c11ee6e098e3d5a9f51e14"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# Function to generate a response
def generate_response(prompt):
    # Encode the input prompt
    inputs = tokenizer(prompt, return_tensors="pt")
    # Generate output using the model
    with torch.no_grad():
        # Adjust max_length for longer/shorter responses
        output = model.generate(**inputs, max_length=100, num_return_sequences=1
                                ,eos_token_id=tokenizer.eos_token_id
                                ,do_sample=False, temperature=None, top_p=None)
    
    # Decode the output tokens to string
    response = tokenizer.decode(output[0], skip_special_tokens=True).strip()
    return response


#Method to follow flow chart
def should_respond(conversation):
    prompt = (
                f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>"
                f"You will be given a piece of text, analyze the text and answer 'True' if" 
                f"the text contains a question, answer 'False' if it does not."
                f"ONLY return either the word 'True' or the word 'False"
                f"<|eot_id|><|start_header_id|>user<|end_header_id|>"
                f"{conversation}\n"
                "<|eot_id|><|start_header_id|>assistant<|end_header_id|>"
             )
    print(f"prompt : \n{prompt}")
    response = generate_response(prompt)
    split = response.split("assistant")
    print("Response: \n")
    print(split[1])
    return split[1] == 'True'


# f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
# You are a helpful assistant who answers True or False questions
# You will be given a piece of text and you will analyze the text 
# and answer 'True' if it is a question and answer 'False' if it 
# is not a question. Your response should ONLY contain the word
# 'True' or the word 'False'.
# <|eot_id|><|start_header_id|>user<|end_header_id|>
# {conversation}
# <|eot_id|><|start_header_id|>assistant<|end_header_id|>"""



# Main
if __name__ == "__main__":
    prompt = "What is the future of AI"
    if (should_respond(prompt)):
        print("WOOOOOOOOOOOOOOOOOOO LlaMA GOAT")
    else:
        print("damn we ass")



