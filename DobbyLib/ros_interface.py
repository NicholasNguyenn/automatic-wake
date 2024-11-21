import base64
import random
import roslibpy.tf
import roslibpy.actionlib
import time
import transformations as tf
import numpy as np
import colorsys
import threading

# must run $rosrun tf2_web_republisher tf2_web_republisher

move_goal = None
goal_position = None
position = None
elevator_status = None

def update_position(current_pos):
    global position
    position = current_pos

def get_position():
    return position


def within_threshold(threshold=0.2):
    if position is None or goal_position is None:
        return True
    return (
        abs(position["translation"]["x"] - goal_position[0]) < threshold
        and abs(position["translation"]["y"] - goal_position[1]) < threshold
    )

def within_coord_threshold(position, threshold=0.2):
    if position is None or goal_position is None:
        return False
    print(str(abs(position[0] - goal_position[0])))
    print(str(abs(position[1] - goal_position[1])))
    return (
        abs(position[0] - goal_position[0]) < threshold
        and abs(position[1] - goal_position[1]) < threshold
    )


# target is (x, y, quat z, quat w)
def go_to_pos(target, reached_goal):
    global move_goal
    global goal_position
    global target_vel

    print("goal recieved")
    
    if goal_position is not None and abs(target[0] - goal_position[0]) < 0.1 \
        and abs(target[1] - goal_position[1]) < 0.1:
        if reached_goal is not None:
            reached_goal(None)
        return

    print("going to position " + str(target))
    message = {
        "target_pose": {
            "header": {"frame_id": "map"},
            "pose": {
                "position": {"x": target[0], "y": target[1], "z": 0.0},
                "orientation": {"x": 0.0, "y": 0.0, "z": target[2], "w": target[3]},
            },
        }
    }

    target_vel = None
    goal_position = target
    move_goal = roslibpy.actionlib.Goal(action_client, message)
    move_goal.send(result_callback=reached_goal)

# target is (x, y)
def go_to_relative_pos(target):
    transformed_target = transform_to_map_frame(target)
    go_to_pos(transformed_target, None)
    return transformed_target

def transform_to_map_frame(target):
    translation_vector = np.array(
        [position["translation"]["x"], position["translation"]["y"], 0]
    )
    rotation_quaternion = np.array(
        [position["rotation"]["w"], 0, 0, position["rotation"]["z"]]
    )
    transformation_matrix = tf.quaternion_matrix(rotation_quaternion)
    transformation_matrix[:3, 3] = translation_vector

    # Apply the transformation
    transformed_target = tf.translation_from_matrix(
        np.dot(
            transformation_matrix,
            tf.translation_matrix((np.array([target[0], target[1], 0]))),
        )
    )
    return (transformed_target[0], transformed_target[1], position["rotation"]["z"], position["rotation"]["w"])


def cancel_goal():
    global move_goal
    global goal_position
    if move_goal is not None:
        print("move goal cancelled")
        move_goal.cancel()
        move_goal = None
        goal_position = None


target_vel = None
def send_vel(vel_command):
    global target_vel
    #print("sending vel " + str(vel_command))
    global goal_position
    goal_position = None
    #if target_vel is not None and target_vel == vel_command:
     #   return
    
    target_vel = vel_command
    message = {
        "linear": {"x": vel_command[0], "y": 0, "z": 0},
        "angular": {"x": 0, "y": 0, "z": vel_command[1]},
    }
    vel_pub.publish(message)
    
def add_elevator_status_listener(listener):
    elevator_sub.subscribe(listener)

def send_elevator_command(floor, door):
    cmd_msg = {"floor_cmd" : floor, "hold_door" : door}
    elevator_pub.publish(cmd_msg)

maps = ["1stFloorWhole", "2ndFloorWhole"]
def change_map_level(level):
    print("changing map to " + maps[level])
    request = roslibpy.ServiceRequest({"new_level_id": maps[level]})
    change_level.call(request, lambda response: print(response))

current_map = 0
def update_map_level(message):
    global current_map
    current_map = maps.index(message["level_id"])

def get_map_level():
    return current_map

client = roslibpy.Ros(host="0.0.0.0", port=9090)
client.run()
print("Is ROS connected?", client.is_connected)
action_client = roslibpy.actionlib.ActionClient(
    client, "/move_base", "move_base_msgs/MoveBaseAction"
)
tf_client = roslibpy.tf.TFClient(client, "/2ndFloorWhole_map")
tf_client.subscribe("base_link", update_position)
map_topic = roslibpy.Topic(client, "/level_mux/current_level", "multi_level_map_msgs/LevelMetaData")
map_topic.subscribe(update_map_level)
vel_pub = roslibpy.Topic(client, "cmd_vel", "geometry_msgs/Twist", queue_size=0)
elevator_sub = roslibpy.Topic(client, "elevator/status", "amrl_msgs/ElevatorStatus")
elevator_pub = roslibpy.Topic(client, "elevator/command", "amrl_msgs/ElevatorCommand")
change_level = roslibpy.Service(client, "/level_mux/change_current_level", "multi_level_map_msgs/ChangeCurrentLevel")