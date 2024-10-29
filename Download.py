from transformers import AutoModelForCausalLM, AutoTokenizer

model_name = "meta-llama/Llama-3.2-3B-Instruct"  # Replace with the correct model name
model = AutoModelForCausalLM.from_pretrained(model_name, force_download=True)
tokenizer = AutoTokenizer.from_pretrained(model_name, force_download=True)
