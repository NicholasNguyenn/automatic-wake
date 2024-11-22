ros_interface_on = True # disable for testing without ROS or for stationary demo
can_preform_actions = True # if true, will be able to perform actions
switching_floors = False  #include destinations from both floors
linear_tour = False

STARTING_FLOOR = 2 # make sure you set the right floor number
STARTING_ROOM = 202 # make sure you set the right room number

DATA_DIR = "Dobby/Data/"
OPENAI_API_KEY = "sk-nAiERyhvKorLjicsAHHaSXU02vlV9jQp_7JY8XsYVjT3BlbkFJKdYCsXL0YadHxy12TUJC0-W0ojXWQ5iH6e46AjPl4A"

EMBEDDINGS_FILE = DATA_DIR + "action_embeddings.csv"
LOGS_DIR = DATA_DIR + "logs/"

LANDMARKS_FILE = DATA_DIR + "knowledge/landmarks.yaml"
DOORWAYS_FILE = DATA_DIR + "knowledge/modified_doors.yaml"
WAYPOINTS_FILE = DATA_DIR + "knowledge/internal_waypoints.yaml"
INFORMATION_FILE = DATA_DIR + "knowledge/information.yaml"
TOUR_FILE = DATA_DIR + "tours/LWR.txt"

PROMPT_TEMPLATE = DATA_DIR + "prompts/lab_tour_prompt.txt" #template that will be filled in
BACKGROUND_FILE = DATA_DIR + "prompts/background.txt" #background information about the robot and where it is
if linear_tour:
    INSTRUCTIONS_FILE = DATA_DIR + "prompts/linear_instructions.txt" #instructions for the robot assistant to follow
else:
    INSTRUCTIONS_FILE = DATA_DIR + "prompts/instructions.txt"