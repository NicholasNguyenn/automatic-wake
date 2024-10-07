import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# Load the tokenizer and model
model_name = r"C:\Users\Jackson\.cache\huggingface\hub\models--meta-llama--Llama-3.2-1B\snapshots\221e3535e1ac4840bdf061a12b634139c84e144c"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# Function to generate a response
def generate_response(prompt):
    # Encode the input prompt
    inputs = tokenizer(prompt, return_tensors="pt")
    # Generate output using the model
    with torch.no_grad():
        # Adjust max_length for longer/shorter responses
        output = model.generate(**inputs, max_length=200) 
    
    # Decode the output tokens to string
    response = tokenizer.decode(output[0], skip_special_tokens=True)
    return response

# Example usage
if __name__ == "__main__":
    prompt = "What is the future of AI?"
    response = generate_response(prompt)
    print(response)
