from ros_interface import get_position
from pynput.keyboard import Key, Listener, KeyCode
from os import system
import yaml
import data as data

current_floor = 2

def on_press(key):

    if key == Key.ctrl_r:
        system('clear')
        rooms = {}
        with open(data.DOORWAYS_FILE, 'r') as file:
            rooms = yaml.safe_load(file)
            if rooms is None:
                rooms = {}
            else:
                rooms = dict(rooms)
        print (rooms)

        with open(data.DOORWAYS_FILE, 'w') as file:
            print ("Enter landmark name: ")
            name = input()
            transform = get_position()
            translation = transform["translation"]
            rotation = transform["rotation"]
            rooms[name] = {"floor": current_floor, "pos_x" : translation["x"], "pos_y" : translation["y"], "rot_z" : rotation["z"], "rot_w" : rotation["w"], "visitable" : True}
            yaml.dump(rooms, file)



# Collect events until released
with Listener(
        on_press=on_press) as listener:
    listener.join()