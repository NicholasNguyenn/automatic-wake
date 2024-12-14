from Dobby import Dobby
from Dobby import Action, Predicate
import Dobby.Scripts.CognitiveModel.model_response as cognitive

import yaml
from functools import partial
import time

ros_interface_on = False # Set to False if you are not using ROS (like at home computer)
if ros_interface_on:
    import ros_interface
    


prompt = open("lab_tour_prompt.txt", "r").read()
locations = {}
actions = []

def populate_locations():
    global locations
    global prompt
    print("adding locations")

    landmarks_str = ""
    with open("lab_landmarks.yaml", "r") as file:
        landmarks = yaml.safe_load(file)
        for landmark in landmarks.keys():
            print(landmark)
            if not landmarks[landmark]["visitable"]:
                continue
            
            floor = landmarks[landmark]["floor"]
            name = landmark
            locations[name] = ((
                landmarks[landmark]["pos_x"],
                landmarks[landmark]["pos_y"],
                landmarks[landmark]["rot_z"],
                landmarks[landmark]["rot_w"]),
                floor
            )
            landmarks_str += f"{name}\n"
                
    prompt = prompt.replace("<insert landmarks here>", landmarks_str)

    # create actions from locations
    for location_name, location in locations.items():
        goto_location = create_goto_action(location_name)
        actions.append(goto_location)

def delay_action():
    time.sleep(6)
    dobby.finished_action()

def create_goto_action(location_name):
    return Action(
        "Drive to " + location_name,
        action_function=delay_action
        if not ros_interface_on
        else partial(ros_interface.go_to_pos, locations[location_name])
    )

def goto_location(location_name):
    location = locations[location_name]
    print("\n\n just entered:" + location_name)
    dobby.cognitive_model.model.set_location(location_name)
    ros_interface.go_to_pos(location[0], reached_goal=destination_reached)

def destination_reached(result = None):
    dobby.finished_action()

def cancel_function():
    print("Cancelling action")
    if ros_interface_on:
        ros_interface.cancel_goal()

# Setup actions
populate_locations()

# Create a new Dobby object
dobby = Dobby(prompt, actions, [], cancel_function, verbose=True)
dobby.main_loop()

