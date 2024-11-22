import time
import cv2
import numpy as np
import pykinect_azure as pykinect
import threading

# Initialize the library, if the library is not found, add the library path as argument
pykinect.initialize_libraries(track_body=False)

# Modify camera configuration
device_config = pykinect.default_configuration
device_config.color_resolution = pykinect.K4A_COLOR_RESOLUTION_720P
device_config.color_format = pykinect.K4A_IMAGE_FORMAT_COLOR_BGRA32
device_config.camera_fps = pykinect.K4A_FRAMES_PER_SECOND_15
device_config.depth_mode = pykinect.K4A_DEPTH_MODE_NFOV_2X2BINNED
device_config.synchronized_images_only = False
#print(device_config)

# Start device
device = pykinect.start_device(config=device_config)

# Start body tracker
#bodyTracker = pykinect.start_body_tracker(model_type=pykinect.K4ABT_DEFAULT_MODEL)

#available for other modules
color_image = None
depth_image = None
get_depth = False
person_pos = None
get_person = False

def get_depth_color_pair():
    global get_depth
    get_depth = True
    while get_depth:
        #wait for update thread to flip flag
        continue
    return depth_image, color_image

def get_person_pos():
    global get_person
    get_person = True
    while get_person:
        #wait for update thread to flip flag
        continue
    return person_pos

def get_center_depth():
    height, width = depth_image.shape
    total_depth = 0
    for r in range (int(width * 0.4), int(width * 0.6)):
        for c in range (int(height * 0.4), int(height * 0.6)):
            if depth_image[c,r] > 0:
                total_depth += depth_image[c,r] * 0.001
            else:
                total_depth += 8
    avg_depth = total_depth / (width * height * 0.04)
    print(avg_depth)
    return avg_depth

def update_frames():
    global color_image
    global depth_image
    global get_depth
    global person_pos
    global get_person

    while True:
        capture = device.update()

        ret_color, color_image = capture.get_color_image()
        ret_depth, depth_image = capture.get_transformed_depth_image()

        if get_person:
            body_frame = bodyTracker.update()
            if body_frame.get_num_bodies() > 0:
                skeleton_3d = body_frame.get_body(0).numpy()
                person_pos = skeleton_3d[pykinect.K4ABT_JOINT_NECK,:3]
                print(person_pos)
            else:
                person_pos = None
            get_person = False

threading.Thread(target=update_frames, daemon=True).start()