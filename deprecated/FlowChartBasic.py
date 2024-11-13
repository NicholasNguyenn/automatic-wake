
import torch
import json
from transformers import AutoModelForCausalLM, AutoTokenizer

# Check if GPU is available
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Load the tokenizer and model
#normal
#model_name = r"C:\Users\Nick\.cache\huggingface\hub\models--meta-llama--Llama-3.2-1B\snapshots\221e3535e1ac4840bdf061a12b634139c84e144c"
#instruct
#model_name = r"C:\Users\Nick\.cache\huggingface\hub\models--meta-llama--Llama-3.2-3B-Instruct\snapshots\392a143b624368100f77a3eafaa4a2468ba50a72"
model_name = "/home/bwilab/.cache/huggingface/hub/models--meta-llama--Llama-3.2-3B-Instruct/snapshots/392a143b624368100f77a3eafaa4a2468ba50a72"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name).to(device)

test_cases = [
    {"conversation": "Hey, do you know where the restroom is? Oh yeah, it's downstairs next to the conference room.", "expected_answer": "it's downstairs next to the conference room.", "should_respond": True, "did_respond": False},
    {"conversation": "What time does the lab close today? I'm not sure, but I think it's 8 PM.", "expected_answer": "it's actually 9 PM.", "should_respond": True, "did_respond": False},
    {"conversation": "Is there a way to reset the robot? You could just turn it off and on.", "expected_answer": "turning it off and on is a good start.", "should_respond": False, "did_respond": False},
    {"conversation": "Can you remind me where we keep the extra batteries? They should be in the supply closet.", "expected_answer": "they're in the storage room, actually.", "should_respond": True, "did_respond": False},
    {"conversation": "Do you have any idea how to fix the motor issue? I think we might need a new part.", "expected_answer": "we might just need to recalibrate it.", "should_respond": True, "did_respond": False},
    {"conversation": "Is this the right cable for the connection? Yes, that's the one we need.", "expected_answer": "no question found.", "should_respond": False, "did_respond": False},
    {"conversation": "I can't remember where I parked my robot. Maybe it's in the lab parking area?", "expected_answer": "it's in the lab parking area.", "should_respond": False, "did_respond": False},
    {"conversation": "Hey, did you finish the project proposal? Not yet, I still have some sections to complete.", "expected_answer": "no question found.", "should_respond": False, "did_respond": False},
    {"conversation": "How do I access the new software update? You need to download it from the website.", "expected_answer": "you can find it in the documentation.", "should_respond": True, "did_respond": False},
    {"conversation": "Can someone help me with the coding? I'm here if you need assistance!", "expected_answer": "no question found.", "should_respond": False, "did_respond": False},
    {"conversation": "Where's the meeting scheduled for? It's in the main conference room.", "expected_answer": "it's in the main conference room.", "should_respond": False, "did_respond": False},
    {"conversation": "Hey, do you know how to calibrate the sensors? Yeah, just follow the manual's instructions.", "expected_answer": "just follow the manual's instructions.", "should_respond": False, "did_respond": False},
    {"conversation": "When is the deadline for the project submission? It's due next Friday, I think.", "expected_answer": "it's actually due on Thursday.", "should_respond": True, "did_respond": False},
    {"conversation": "Do you think we need more supplies for the next experiment? Yes, we're running low on several items.", "expected_answer": "no question found.", "should_respond": False, "did_respond": False},
    {"conversation": "What should I do if the robot stops responding? You should try rebooting it.", "expected_answer": "rebooting it is a good idea.", "should_respond": False, "did_respond": False},
    {"conversation": "Have you seen the new lab equipment? Yes, it's been set up in the back room.", "expected_answer": "no question found.", "should_respond": False, "did_respond": False},
    {"conversation": "Where can I find the toolbox? It should be on the workbench.", "expected_answer": "it's actually in the storage cabinet.", "should_respond": True, "did_respond": False},
    {"conversation": "Can I borrow your laptop for a bit? Sure, just be careful with it.", "expected_answer": "no question found.", "should_respond": False, "did_respond": False},
    {"conversation": "Is there a time when we can test the robot? We can do it tomorrow afternoon.", "expected_answer": "no question found.", "should_respond": False, "did_respond": False},
    {"conversation": "I heard the lab is open 24/7. Yeah, but you need a keycard.", "expected_answer": "you need a keycard to access it.", "should_respond": True, "did_respond": False},
    {"conversation": "What if the robot runs out of battery? We have spares in the drawer.", "expected_answer": "we have spares in the drawer.", "should_respond": False, "did_respond": False},
    {"conversation": "Is this robot ready for the test run? Yes, it's all set to go.", "expected_answer": "no question found.", "should_respond": False, "did_respond": False},
    {"conversation": "Do you know if we have any meetings scheduled this week? Yes, there's one on Thursday.", "expected_answer": "there's one on Thursday.", "should_respond": False, "did_respond": False},
]




# Function to generate a response
def generate_response(prompt):
    # Encode the input prompt
    inputs = tokenizer(prompt, return_tensors="pt")
    
    # Move input tensors to the GPU if available
    inputs = {key: value.to(device) for key, value in inputs.items()}

    # Generate output using the model
    with torch.no_grad():
        # Adjust max_length for longer/shorter responses
        output = model.generate(**inputs, max_length=200, num_return_sequences=1
                                ,eos_token_id=tokenizer.eos_token_id
                                ,do_sample=False, temperature=None, top_p=None)
    
    # Decode the output tokens to string
    response = tokenizer.decode(output[0], skip_special_tokens=True).strip()

    return response
    

# Method to see if someone is asking a question, and if so what is it
def is_there_question(conversation):
    prompt = (
        f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>"
        f"Does the text provided by the user contain a question? "
        f"If yes, format the answer in the following JSON format: "
        f"{{\"question_found\": true, \"question\": \"[extracted question]\"}}. "
        f"If no question is found, respond in the format: "
        f"{{\"question_found\": false, \"answer\": \"no question found\"}}. "
        f"<|eot_id|><|start_header_id|>user<|end_header_id|>"
        f"{conversation}\n"
        f"<|eot_id|><|start_header_id|>assistant<|end_header_id|>"
    )
    response = generate_response(prompt)
    split = response.split("assistant")
    model_response = split[1].replace("`", "").strip()
    question_dict = json.loads(model_response)
    return question_dict


# Method to see if someone answered the question, and if so what is it
def is_there_answer(conversation, question):
    prompt = (
        f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>"
        f"Given the following question: {question} " 
        f"does the text given by the user provide a direct answer?" 
        f"If yes, format the answer in the following JSON format:"
        f"{{\"answer_found\": true, \"answer\": \"[extracted answer]\" }}"
        f"If no answer is found, respond in the format:"
        f"{{\"answer_found\": false, \"answer\": \"no answer found\" }}"
        f"<|eot_id|><|start_header_id|>user<|end_header_id|>"
        f"{conversation}\n"
        f"<|eot_id|><|start_header_id|>assistant<|end_header_id|>"
    )
    response = generate_response(prompt)
    split = response.split("assistant")
    model_response = split[1].replace("`", "").strip()
    answer_dict = json.loads(model_response)
    return answer_dict


# compare the answer w/ Dobby's
def compare_answers(question, answer1, answer2):
    prompt = (
        f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>"
        f"You will be given two responses to the following question {question}" 
        f"Analyze the responses and determine if they answer the question"
        f"with essentially the same meaning."
        f"If the responses convey the same essential answer to the question"
        f", format the answer in the following JSON format:"
        f"{{\"answers_same\": true}}"
        f"If the responses convey meaningfully different answers, format the answer in the following JSON format:"
        f"{{\"answers_same\": false}}"
        f"<|eot_id|><|start_header_id|>user<|end_header_id|>"
        f"Response 1: {answer1}, Response 2: {answer2}\n"
        f"<|eot_id|><|start_header_id|>assistant<|end_header_id|>"
    )
    response = generate_response(prompt)
    split = response.split("assistant")
    model_response = split[1].replace("`", "").strip()
    answer_dict = json.loads(model_response)
    return answer_dict['answers_same']


# primitive dob 
def dobby_answer(question):
    # figure out how to get dobby answer
    # two options: start convo and stop one (slow)?
    # idk look in memory idk how dobby works yet
    
    dobbyAnswer = {
        "answer_found": True,
        "answer": "my favorite lab is in san francisco"
    }
    return dobbyAnswer 



def should_respond(conversation, expected_answer, response):
    question = is_there_question(conversation)
    if (question['question_found']): # do we hear a question
        print("there is a question")

        # Temporarily replace the Dobby answer with the expected answer
        dobby_knows = {
            "answer_found": True,
            "answer": expected_answer
        }
        if (dobby_knows['answer'] == "no question found"):
            dobby_knows['answer_found'] = False
        #dobby_knows = dobby_answer(question['question'])
        if (dobby_knows['answer_found']): # does dobby know the answer to the question
            print("Dobby knows the answer")
            answer = is_there_answer(conversation, question['question'])
            if (not answer['answer_found']): # did we hear an answer to the question
                print("No one answered, Dobby should help")
                response = True
                # start convo
            else: # we heard an answer, let's compare
                if compare_answers(question['question'],answer['answer'],dobby_knows['answer']): # we don't need to barge in, they alr know answer
                    print("answers the same")
                    response = False
                    # give up, no need to do anything else
                else: # we have a different answer
                    print("diff answers")
                    response = True
                    # start convo
        else:
            print("Dobby did not know the answer")
            response = False
    else:
        print("no question found")
        response = False



def run_tests():
    tests_passed = 0
    for index, test_case in enumerate(test_cases):
        conversation = test_case["conversation"]
        expected_answer = test_case["expected_answer"]
        response = test_case['did_respond']
        print(f"\nRunning Test Case {index + 1}:")
        print(f"Conversation: {conversation}")
        should_respond(conversation, expected_answer, response)
        if(test_case["should_respond"] == test_case['did_respond']):
            tests_passed+=1
    print("Number of tests passed: "+ tests_passed)

# Main
if __name__ == "__main__":
    run_tests()



