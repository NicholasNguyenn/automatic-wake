import firebase_admin
from firebase_admin import credentials, firestore
import yaml
import data
import math
import data

map_size = (1721, 1106)
map_resolution = 0.05
map_origin = [-74.500000, -25.000000, 0.000000]

# Initialize Firebase Admin SDK
def initialize_firebase():
    cred = credentials.Certificate(data.DATA_DIR + "firebase_key.json")
    firebase_admin.initialize_app(cred)
    return firestore.client()

# Fetch landmarks from Firestore
def fetch_landmarks(db, collection_name="landmarks"):
    try:
        docs = db.collection(collection_name).stream()
        landmarks = []
        for doc in docs:
            landmarks.append(doc.to_dict())
        return landmarks
    except Exception as e:
        print(f"Error fetching landmarks: {e}")
        return []

def fetch_and_save_tours(db, collection_name="tours"):
    tour_dir = data.DATA_DIR + "tours/"
    try:
        docs = db.collection(collection_name).stream()
        tours = []
        for doc in docs:
            landmarks = []
            tour_data = doc.to_dict()
            for landmark in tour_data['landmarks']:
                landmarks.append(landmark['name'])
            tours.append(landmarks)

            with open(tour_dir + tour_data['name'] + ".txt", 'w') as f:
                for landmark in landmarks:
                    f.write(landmark + "\n")
            
        return tours
    except Exception as e:
        print(f"Error fetching tours: {e}")
        return []

# Save landmarks to a YAML file
def save_to_yaml(data, filename="landmarks.yaml"):
    try:
        with open(filename, 'w') as yaml_file:
            yaml.dump(data, yaml_file, default_flow_style=False, sort_keys=False)
        print(f"Data successfully saved to {filename}")
    except Exception as e:
        print(f"Error saving to YAML: {e}")

def transform_location(x, y):
    x = (map_size[0] * x) * map_resolution + map_origin[0]
    y = (map_size[1] - map_size[1] * y) * map_resolution + map_origin[1]
    return x, y

def parse_landmarks(landmarks):
    parsed_landmarks = {}
    for landmark in landmarks:
        x, y = transform_location(landmark['x'], landmark['y'])
        print(landmark['name'])
        print(landmark['x'], landmark['y'])
        endx, endy = transform_location(landmark['endx'], landmark['endy'])

        dx = endx - x
        dy = endy - y
        euler_yaw = math.atan2(dy, dx)

        parsed_landmark = {}
        parsed_landmark['x'] = x
        parsed_landmark['y'] = y
        parsed_landmark['yaw'] = euler_yaw
        parsed_landmark['info'] = landmark['info']
        parsed_landmark['floor'] = 2
        parsed_landmark['room'] = 202
        parsed_landmarks[landmark['name']] = parsed_landmark


    return parsed_landmarks

def update_landmarks():
    db = initialize_firebase()
    landmarks = fetch_landmarks(db)
    landmarks = parse_landmarks(landmarks)
    fetch_and_save_tours(db)

    landmarks_file = data.DATA_DIR + "knowledge/landmarks.yaml"

    if landmarks:
        save_to_yaml(landmarks, landmarks_file)
    else:
        print("No landmarks found.")


if __name__ == "__main__":
    update_landmarks()
