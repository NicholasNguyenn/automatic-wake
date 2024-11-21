# Dobby Lib
## Setup
Instructions for setup on Ubuntu 22.04
1. Clone the repository
```
git clone https://github.com/Living-With-Robots-Lab/DobbyLib.git
cd DobbyLib
```
2. Make a python virtual environment
```
python3 -m venv venv
source ./venv/bin/activate
python -m pip install --upgrade pip
```
3. Install pyaudio dependencies
```
sudo apt-get install python3-pyaudio
sudo apt install portaudio19-dev
```
4. Install pip requirements
```
pip install --upgrade pip
pip install -r requirements.txt
```
There may be issues installing the requirements due to your python version, missing dependencies, etc. You may have to run the program, look at the errors, and manually pip install any missing imports. Google any remaining import errors, they usually have quick fixes. The openAI library must be version 0.28.0.

## Usage

This repo provides a couple of convenience scripts like ros_interface and log_location, as well as an example usage of the Dobby lib in example.py.

1. Import the Dobby library
```
from Dobby import Dobby
from Dobby import Action, Predicate
```
2. Write a prompt as a separate text file. An example prompt is provided in the repo. Make sure that you list the possible actions that the robot can do somewhere in the prompt. Load this file as a string that you will use to initialize Dobby.
3. Define your actions. When you create an action, you provide an action function and the action title. Do not worry about defining predicates because most actions won’t need them and plan validation is not implemented currently.
```
Action (string name, Predicate[] pos_dependencies = [], Predicate[] pos_outcomes = [], Predicate[] neg_dependencies = [], Predicate[] neg_outcomes = [], Callable action_function = None, bool require_response = True)
```
Parameter | Description
---|---
name | the title of the action
pos/neg dependencies | the predicates that must be true / false for the action to be valid
pos/neg outcomes | the predicates that will be set to true / false when the action executes
action_function | the method that will be called when the action is executed by the agent
require_response | if false, the next action will immediately start executing when this action is completed, if true, the agent will have to call continue_plan() to start the action (useful for tours where you want the user to confirm they are ready to move on)
4. Create a Dobby object
```
Dobby(string prompt, Action[] actions, Predicate[] predicates, Callable cancel_function, Callable idle_hook = None, Callable(bool recording) recording_hook = None, bool gui_enabled = True, verbose = False)
```
Parameter | Description
---|---
prompt | a string that is provided as the initial system message in the chat history. Use this to define the behavior of the agent, outline its personality, and provide instructions
actions | a list of action objects that the agent can include in its plan
predicates | the predicates that define the environment, leave this as an empty list in most cases
cancel_function | function that will be called if the agent cancels the current plan, should cancel the move goal in most cases
idle_hook | called when the robot goes into idle mode, used to start custom idle behaviors like wandering
recording_hook | called when the robot starts and stops recording (ready to accept input), can be used to create custom input methods
gui-enabled | whether or not to show the graphical interface for Dobby
verbose | adds print statements for debugging
5. Start the main loop. The Dobby architecture runs an update loop on the main thread. You can start Dobby by calling .main_loop() on your Dobby object. You should see the UI pop up. This function will block until the program quits, so it should be the last line of your script. Any additional functionality that you add should be triggered by one of the event hooks or actions that you defined.

## Dobby API

Methods | Description
---|---
finished_action() | signals that the current action has been completed, this is needed because most actions will run asynchronously (setting a navigation goal, for example). This must be called for the agent to move on to the next action.
add_system_message(string message) | adds a system message to the chat history, you can use this to inform the agent of an event, such as recognizing the identity of a person, or to add context like the information associated with a landmark
start_conversation() | this will interrupt the idle state and start recording for the user’s input, currently only called when the keyword “Dobby” is heard, can be used in conjunction with person detection for example
get_robot_response(string user_input) | get a response from the agent based on the user's input, can be used to create non-audio input methods, should be used in conjunction with the recording_hook. This will override the current recording. Ex: when recording hook is called, sign language detection starts, input sent to agent with get_robot_response().
log_console(string text, system=False, end=”\n) | logs a message to the GUI console, if system is true, the text will be orange
main_loop() | Starts the Dobby update loop, blocking indefinitely


