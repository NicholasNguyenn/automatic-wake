
import torch
import time
from transformers import AutoModelForCausalLM, AutoTokenizer

# Check if GPU is available
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Load the tokenizer and model
#normal
#model_name = r"C:\Users\Nick\.cache\huggingface\hub\models--meta-llama--Llama-3.2-1B\snapshots\221e3535e1ac4840bdf061a12b634139c84e144c"
#instruct
model_name = r"C:\Users\Nick\.cache\huggingface\hub\models--meta-llama--Llama-3.2-3B-Instruct\snapshots\392a143b624368100f77a3eafaa4a2468ba50a72"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name).to(device)

# Function to generate a response
def generate_response(prompt):
    # Encode the input prompt
    inputs = tokenizer(prompt, return_tensors="pt")
    
    # Move input tensors to the GPU if available
    inputs = {key: value.to(device) for key, value in inputs.items()}

    # Generate output using the model
    with torch.no_grad():
        # Adjust max_length for longer/shorter responses
        output = model.generate(**inputs, max_length=100, num_return_sequences=1
                                ,eos_token_id=tokenizer.eos_token_id
                                ,do_sample=False, temperature=None, top_p=None)
    
    # Decode the output tokens to string
    response = tokenizer.decode(output[0], skip_special_tokens=True).strip()
    print(inputs['input_ids'].device)

    return response
    
#Method to see if someone answered the question
def no_response(conversation):
    prompt = (
                f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>"
                f"You will be given a piece of text that contains a question," 
                f"analyze the text and answer 'True' if" 
                f"the you are given an answer to the question, answer 'False' if you are not given an answer."
                f"ONLY return either the word 'True' or the word 'False"
                f"<|eot_id|><|start_header_id|>user<|end_header_id|>"
                f"{conversation}\n"
                "<|eot_id|><|start_header_id|>assistant<|end_header_id|>"
             )
    response = generate_response(prompt)
    split = response.split("assistant")
    print("There is an answer: \n")
    print(split[1])
    return 'False' in split[1]


#Method to see if someone is asking a question
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
    response = generate_response(prompt)
    split = response.split("assistant")
    print("There is a question: \n")
    print(split[1])
    return 'True' in split[1]


#Extract the answer
def what_is_answer(conversation):
    prompt = (
                f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>"
                f"You will be given a piece of text that has both a question and the answer to that question." 
                f"Analyze the text and return both the question and answer"
                f"Format your response with the following:"
                f"<Insert Question> | <Insert Answer>"
                f"<|eot_id|><|start_header_id|>user<|end_header_id|>"
                f"{conversation}\n"
                "<|eot_id|><|start_header_id|>assistant<|end_header_id|>"
             )
    response = generate_response(prompt)
    split = response.split("assistant")
    Question_Answer = split[1].split("|")
    print("Question: "+ Question_Answer[0] + "\n Answer: " + Question_Answer[1] + "\n")
    return Question_Answer


# compare the answer w/ Dobby's
def compare_answers(answer1, answer2, question):
    prompt = (
                f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>"
                f"You will be given a question and two answers to that question" 
                f"Analyze the answers, and determine if they are MEANINGFULLY identical to the question"
                f"If they are MEANINGFULLY identical, ONLY return true"
                f"otherwise, ONLY return false"
                f"<|eot_id|><|start_header_id|>user<|end_header_id|>"
                f"Question: {question} Answer 1: {answer1}, Answer 2: {answer2}\n"
                "<|eot_id|><|start_header_id|>assistant<|end_header_id|>"
             )
    response = generate_response(prompt)
    split = response.split("assistant")
    print(split[1])
    return 'True' in split[1]

# primitive dob 
def dobby_answer(question):
    # figure out how to get dobby answer
    # two options: start convo and stop one (slow)?
    # idk look in memory idk how dobby works yet
    
    dobbyAnswer = ['True',"upstairs or smthn"]
    return dobbyAnswer 


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
    prompt = "Do you know where I can find the restroom?"
    if (should_respond(prompt)): # do we hear a question
        print("WOOOOOOOOOOOOOOOOOOO LlaMA GOAT")
        QA = what_is_answer(prompt)
        dobby_knows = dobby_answer(QA[0])
        if (dobby_knows): # does dobby know the answer to the question
            if (no_response(prompt)): # did we hear an answer to the question
                print("we're still goated lets go")
                # start convo
            else: # we heard an answer, let's compare
                if compare_answers(QA[0],QA[1],dobby_knows[1]): # we don't need to barge in, they alr know answer
                    print("answers the same")
                    # give up, no need to do anything else
                else: # we have a different answer
                    print("diff answers")
                    # start convo
    else:
        print("damn we ass")

    print("Device: " + "\n" + str(next(model.parameters()).device))


