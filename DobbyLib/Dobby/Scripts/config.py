import Dobby.Scripts.auto_wake.tokens as model_key

can_preform_actions = True # if true, will be able to perform actions

STARTING_FLOOR = 2 # make sure you set the right floor number

DATA_DIR = "Dobby/Data/"
OPENAI_API_KEY = model_key.gpt_key

EMBEDDINGS_FILE = DATA_DIR + "cache/action_embeddings.csv"
LOGS_DIR = DATA_DIR + "logs/"
