import math
import yaml

# Function to calculate Euler yaw from quaternion (w, z)
def quaternion_to_yaw(w, z):
    return math.atan2(2 * (w * z), 1 - 2 * (z**2))

# Load and process the YAML data from a file
def load_and_process_yaml(file_path):
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)

    # Loop through each room entry in the data and process it
    for room_key, room_value in data.items():
        # Check if the room has quaternion values to process
        w = room_value.get('rot_w')
        z = room_value.get('rot_z')
        
        if w is not None and z is not None:
            # Calculate yaw from quaternion values
            yaw = quaternion_to_yaw(w, z)
            room_value['yaw'] = yaw  # Add the yaw value

            # Optionally remove the quaternion components (rot_w and rot_z)
            room_value.pop('rot_w', None)
            room_value.pop('rot_z', None)

    # Save the modified data back to a file
    with open('modified_rooms.yaml', 'w') as outfile:
        yaml.dump(data, outfile, default_flow_style=False)

    return data

# Example usage
file_path = 'Dobby/Data/knowledge/ahg_tour_landmarks.yaml'  # Path to your input YAML file
modified_data = load_and_process_yaml(file_path)

# Optionally print the modified data
print(yaml.dump(modified_data, default_flow_style=False))
