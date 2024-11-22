from gui import GUI
import audio as audio
import agent as agent

import data as data
from functools import partial
from playsound import playsound
import random
import pygame

if data.ros_interface_on:
    import ros_interface as ros_interface

import re
from queue import Queue
import time

import face_interface
import load_tour_data

# Main driver class of Dobby. This is the python file that should be run to start Dobby.

# initial setup and dependency injection (to prevent circular import)
def setup():
    load_tour_data.update_landmarks()

    agent.set_logger(ui.log_console)
    agent.set_response_callback(incoming_response)
    agent.audio_processor = audio_recorder
    agent.enqueue_callback = enqueue_callback
    agent.set_receiving_response = set_recieving_response
    agent.set_event_flag = set_event_flag
    agent.setup()
    if ui.hey_dobby_mode.get():
        begin_idling()


# called when a conversation is over, begins wandering and looking for new person
def begin_idling():
    audio_recorder.start_listening(enter_conversation)
    face_interface.set_emotion(face_interface.Emotion.IDLE)
    ui.log_console("Listening for Dobby...", True)

# event called when cognitive model decides we should enter the conversation
def enter_conversation(transcription):
    face_interface.set_emotion(face_interface.Emotion.NEUTRAL)
    if not is_recording:
        get_robot_response(transcription)
        audio_recorder.stop_listening()
        sound.play()
        toggle_recording()


# # event called when keyword detected, starts recording
# def heard_keyword(direction, direction_index):
#     # self.log_console("Detected direction at " + direction, system=True)
#     face_interface.set_emotion(face_interface.Emotion.NEUTRAL)
#     if not is_recording:
#         audio_recorder.stop_listening()
#         sound.play()
#         toggle_recording()


def toggle_recording(respond=True):
    global is_recording
    global event_flag

    if not is_recording:
        # start recording
        is_recording = True
        audio_recorder.stop_listening()
        face_interface.set_emotion(face_interface.Emotion.RECORDING)
        # toggle recording called again when silence is detected
        audio_recorder.start_recording(toggle_recording, ui.hey_dobby_mode.get())
        ui.display_recording(True)
        ui.enable_input(False)
        sound.play()
    else:
        # stop recording, transcribe input, get robots response
        is_recording = False
        audio_recorder.stop_recording()
        ui.display_recording(False)
        ui.enable_input(True)

        sound.play()
        face_interface.set_emotion(face_interface.Emotion.NEUTRAL)

        if not respond:
            return
        user_input = audio.transcribe_into_text()
        if re.search(r"[a-z]", user_input, flags=re.IGNORECASE):
            get_robot_response(user_input)
        else:
            # no response
            if event_flag:
                event_flag = False
                get_robot_response("") # chatGPT will give a response saying it reached the destination
            elif agent.get_state() == "CONVERSING" and ui.hey_dobby_mode.get():
                begin_idling()
            elif agent.get_state() == "EXECUTING" and ui.hey_dobby_mode.get():
                ui.log_console("Listening for Dobby...", True)
                audio_recorder.start_listening(heard_keyword)


# send input to SayCan
def get_robot_response(user_input):
    global last_message
    global event_flag

    if user_input != "":
        ui.log_console("USER: " + user_input)
    if is_recording:
        ui.toggle_recording(False)
    ui.enable_input(False)
    ui.enable_recording(False)

    event_flag = False
    audio_recorder.start_speaking(finished_callback=finished_speaking)
    func, response = agent.process_user_input(user_input)
    time.sleep(0.5)

    if len(current_response_phrase) > 0:
        audio_recorder.enqueue_speech_line(current_response_phrase)

    audio_recorder.set_recieving_response(False)
    if response == None or len(response.strip()) == 0: #handle empty response
        audio_recorder.stop_speaking()
        finished_speaking(True)
    if func == 2: #conversation ended
        last_message = True
    if response != None and len(response) > 0 and response[-1] != "\n":
        ui.log_console("")

#used for external dialogue lines
def set_recieving_response(val):
    if is_recording:
        toggle_recording(False)

    ui.enable_input(val)
    ui.enable_recording(val)
    if not val:
        audio_recorder.stop_listening()

    if not val:
        ui.log_console("")
    
    audio_recorder.set_recieving_response(val)
    ui.enable_input(not val)
    if val:
        audio_recorder.start_speaking(finished_callback=finished_speaking)

def set_event_flag():
    global event_flag
    event_flag = True

# called while response is streamed from openai
# enables faster response time
def incoming_response(chunk):
    global current_response_phrase

    current_response_phrase += chunk
    ui.log_console(chunk, end="")

    # wait until we receive punctuation to add speech line
    # (compromise between waiting for whole response and speaking each word separately)
    if re.search(r"[a-zA-Z][.?!\n]", current_response_phrase):
        # sometimes chat bot starts with dialogue tag and we should not speak that
        current_response_phrase = current_response_phrase.replace("DOBBY:", "")
        current_response_phrase = current_response_phrase.replace("ROBOT:", "")
        audio_recorder.enqueue_speech_line(current_response_phrase)
        current_response_phrase = ""


# called when audio thread finishes all lines
def finished_speaking(followup=True):
    global last_message
    global event_flag

    audio_recorder.stop_speaking()

    ui.enable_recording(True)
    ui.enable_input(True)
    if last_message:
        begin_idling()
        if data.initiating_convos_on:
            agent.user_left()
        last_message = False
    elif event_flag:
        event_flag = False
        get_robot_response("")
    elif followup and ui.hey_dobby_mode.get() and not is_recording:
        toggle_recording()  # start recording again for followup


# used by threads to trigger events on main thread
def enqueue_callback(callback):
    print(f"{callback} queued")
    callback_queue.put(callback)


callback_queue = Queue()

audio_recorder = audio.Recorder(enqueue_callback)
ui = GUI(toggle_recording, get_robot_response)
face_interface.start_server()

pygame.init()
pygame.mixer.init()
sound = pygame.mixer.Sound("Dobby/Data/audio/recording_tone.mp3")
sound.set_volume(0.2)

is_recording = False
current_response_phrase = ""
first_phrase = False
last_message = False
event_flag = False

setup()

def consume_callback():
    if callback_queue.empty():
        return

    callback = callback_queue.get(False)

    print(f"running {callback}")
    callback()

# main loop
while not ui.is_exit_clicked():
    ui.update()  # refresh UI elements
    consume_callback()

#exit remaining threads
audio_recorder.stop_listening()
audio_recorder.stop_speaking()
