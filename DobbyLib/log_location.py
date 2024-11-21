from ros_interface import get_position
from pynput.keyboard import Key, Listener, KeyCode
from os import system
import yaml

landmarks_file = "lab_landmarks.yaml"

def on_press(key):

    if key == Key.ctrl_r:
        system('clear')
        landmarks = {}
        with open(landmarks_file, 'r') as file:
            landmarks = yaml.safe_load(file)
            if landmarks is None:
                landmarks = {}
            else:
                landmarks = dict(landmarks)

        with open(landmarks_file, 'w') as file:
            print ("Enter landmark name: ")
            name = input()
            transform = get_position()
            translation = transform["translation"]
            rotation = transform["rotation"]
            landmarks[name] = {"pos_x" : translation["x"], "pos_y" : translation["y"], "rot_z" : rotation["z"], "rot_w" : rotation["w"]}
            yaml.dump(landmarks, file)
            print("Landmark saved")

# Collect events until released
with Listener(
        on_press=on_press) as listener:
    listener.join()