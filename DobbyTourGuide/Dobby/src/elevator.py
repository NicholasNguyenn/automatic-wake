import data as data
import yaml
import time
if data.ros_interface_on:
    import ros_interface as ros_interface
    import python_kinect

current_floor = data.STARTING_FLOOR
desired_floor = data.STARTING_FLOOR
waiting_outside_elevator = False
verifying = False

arrival_callback = None

waypoint_locations = {}
with open(data.WAYPOINTS_FILE, "r") as file:
    locations = yaml.safe_load(file)
    if locations is not None:
        waypoint_locations = dict(locations)

def location_of(waypoint):
    return (waypoint_locations[waypoint]["x"], waypoint_locations[waypoint]["y"], waypoint_locations[waypoint]["yaw"])

def inside_elevator(result):
    global current_floor
    print("inside elevator")
    time.sleep(12)
    wait_open_door()
    print("elevator arrived")
    current_floor = desired_floor
    if arrival_callback is not None:
        arrival_callback()
    else:
        ros_interface.go_to_pos(location_of("ElevatorEntrance"), None)


def at_elevator(result):
    global waiting_outside_elevator
    if not ros_interface.within_threshold(1): 
        print("canceling elevator")
        return
    print("calling elevator")
    ros_interface.send_elevator_command(current_floor, False)
    waiting_outside_elevator = True

def elevator_status_updated(status):
    global waiting_outside_elevator
    global current_floor
    
    if waiting_outside_elevator:
        print(status)
        if status["door"] != 0 and status["floor"] == current_floor:
            waiting_outside_elevator = False
            print("elevator arrived")
            ros_interface.change_map_level(desired_floor, 0)
            ros_interface.send_elevator_command(desired_floor, False)
            ros_interface.go_to_pos(location_of("InsideElevator"), inside_elevator)
        

def wait_open_door():
    global current_floor

    time.sleep(2)
    frames_open = 0
    while frames_open < 5:
        if python_kinect.get_center_depth() > 3:
            frames_open += 1
        else:
            frames_open = 0
        time.sleep(0.1)
        

def cancel_elevator():
    global waiting_outside_elevator
    waiting_outside_elevator = False
    ros_interface.cancel_goal()

def take_elevator(floor, callback=None):
    if not data.ros_interface_on:
        return

    global arrival_callback
    global desired_floor
    desired_floor = floor
    arrival_callback = callback
    ros_interface.go_to_pos(location_of("ElevatorEntrance"), at_elevator)

if data.ros_interface_on:
    ros_interface.add_elevator_status_listener(elevator_status_updated)