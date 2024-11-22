import socket
import threading
from enum import Enum
import time

# Interface file to render virtual face of Dobby

emotion_queue = []

class Emotion(Enum):
    IDLE = 0
    NEUTRAL = 1
    HAPPY = 2
    EXCITED = 3
    AMUSED = 4
    CONTEMPT = 5
    SAD = 6
    ANGRY = 7
    SCARED = 8
    CONFUSED = 9
    RECORDING = 10

curr_volume = 0
curr_threshold = 300

def server_thread():
    # Define the server address and port
    server_address = ('localhost', 12333)

    # Create a TCP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind the socket to the server address
    sock.bind(server_address)

    # Listen for incoming connections
    sock.listen(1)

    while True:
        # Wait for a connection
        print('waiting for a connection')
        connection, client_address = sock.accept()
        print('connection from', client_address)
        curr_emotion = Emotion.NEUTRAL

        try:
            while True:
                if len(emotion_queue) > 0:
                    curr_emotion = emotion_queue.pop(0)
                    data = ("Face " + str(curr_emotion.value)).encode()
                    connection.sendall(data)
                elif curr_emotion == Emotion.RECORDING:
                    data = f"{curr_volume} {curr_threshold}".encode()
                    connection.sendall(data)

                time.sleep(0.01)

        finally:
            # Clean up the connection
            connection.close()

def start_server():
    server = threading.Thread(target=server_thread)
    server.daemon = True
    server.start()

def set_emotion(emotion):
    #convert stings to Emotion enum
    if type(emotion) == str:
        if emotion.upper() in Emotion.__members__:
            emotion = Emotion[emotion.upper()]
        else:
            print("Invalid emotion " + str(emotion))
            emotion = Emotion.NEUTRAL
            return

    emotion_queue.append(emotion)

def set_audio_level(volume, threshold):
    global curr_volume
    global curr_threshold

    curr_volume = volume
    curr_threshold = threshold

# Start the server
start_server()
