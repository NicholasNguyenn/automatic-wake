from Dobby.Scripts.gui import GUI
import Dobby.Scripts.audio as audio
from Dobby.Scripts.agent import Agent
import Dobby.Scripts.config as config
from functools import partial
from playsound import playsound
import random
import pygame
from Dobby.Scripts.environment_state import Action, Predicate
from Dobby.Scripts.CognitiveModel.cognitive_model import CognitiveModel


from typing import List
from typing import Callable

import re
from queue import Queue
import time

class Dobby:
    def __init__(self, prompt: str, actions: List[Action], predicates: List[Predicate], cancel_function: Callable[[],None], idle_hook:Callable[[],None] = None, recording_hook:Callable[[],None] = None, gui_enabled=True, verbose=False):
        self.__audio_recorder = audio.Recorder()

        pygame.init()
        pygame.mixer.init()
        self.__recording_tone = pygame.mixer.Sound("Dobby/Data/audio/recording_tone.mp3")
        self.__recording_tone.set_volume(0.2)

        self.__idle_hook = idle_hook
        self.__recording_hook = recording_hook
        self.__ui_enabled = gui_enabled
        self.__verbose = verbose

        self.__callback_queue = Queue()
        self.__is_recording = False
        self.__current_response_phrase = ""
        self.__last_message = False
        self.__event_flag = False

        self.__agent = Agent(prompt, actions, predicates, cancel_function, self.__audio_recorder, self.__set_event_flag, self.__incoming_response)

        self.cognitive_model = CognitiveModel()

        if gui_enabled:
            self.__ui = GUI(self.__toggle_recording, self.get_robot_response, self.__agent.get_state)
            self.__agent.set_logger(self.__ui.log_console)
        
        if self.__hey_dobby_mode():
            self.__enqueue_callback(self.__begin_idling)


    # --- PUBLIC METHODS ---

    def finished_action(self):
        """signal that the current action has been completed"""
        self.__enqueue_callback(self.__agent.finished_action)

    def add_system_message(self, message: str):
        """add system information to the agent's context buffer"""
        self.__agent.add_system_message(message)

    def start_conversation(self):
        """interrupt idling and begin recording a user's input"""
        if not self.__is_recording:
            self.__audio_recorder.stop_recording()
            self.__recording_tone.play()
            self.__toggle_recording()

    def get_robot_response(self, user_input: str):
        """get a response from the agent based on the user's input"""

        if user_input != "":
            self.log_console("USER: " + user_input)
        self.__set_receiving_response(True)
        func, response = self.__agent.process_user_input(user_input)
        time.sleep(0.5)
        if len(self.__current_response_phrase) > 0:
            self.cognitive_model.update_conversation(response, True)
            self.__audio_recorder.enqueue_speech_line(self.__current_response_phrase)
        self.__set_receiving_response(False)
        if response == None or len(response.strip()) == 0:
            self.__audio_recorder.stop_speaking()
        if func == 2:
            self.__last_message = True
        if response != None and len(response) > 0 and response[-1] != "\n":
            self.log_console("")

    def log_console(self, text: str, system=False, end="\n"):
        """log a message to the GUI console"""

        if self.__ui_enabled:
            self.__ui.log_console(text, system, end)
        else:
            print(text)

    # --- PRIVATE METHODS ---

    # We want to replace these methods so instead of waiting for the keyword in the idle loop we 
    # use the loop we make to record audio and wait of the cognitive model to decide its time to interject
    # we will need to start a new theread and make a callback function
    def __begin_idling(self):
        self.__toggle_recording()
        self.log_console("Listening for Dobby...", True)
        if self.__idle_hook != None:
            self.__idle_hook()


    def __recording_finished(self):
        self.__enqueue_callback(self.__toggle_recording)

    def __toggle_recording(self, respond=True):
        if not self.__is_recording:
            self.__is_recording = True
            if self.__recording_hook != None:
                self.__recording_hook(True)
            # If we've detected silence for a while clear the current conversation
            # before continuing to record
            if self.__audio_recorder.silent_cycles == 4:
                self.cognitive_model.clear_conversation()
            self.__audio_recorder.start_recording(self.__recording_finished, self.__hey_dobby_mode())
            if self.__ui_enabled:
                self.__ui.display_recording(True)
                self.__ui.enable_input(False)
        else:
            self.__is_recording = False
            if self.__recording_hook != None:
                self.__recording_hook(False)
            self.__audio_recorder.stop_recording()
            if self.__ui_enabled:
                self.__ui.display_recording(False)
                self.__ui.enable_input(True)
            self.__recording_tone.play()
            if not respond:
                return
            action = self.cognitive_model.decide_action()
            if action["name"] == 'get_robot_response':
                self.get_robot_response(action["parameters"]["user_input"])
            else:
                if self.__event_flag:
                    self.__event_flag = False
                    self.get_robot_response("") 
                elif self.__agent.get_state() == "CONVERSING" and self.__hey_dobby_mode():
                    self.__begin_idling()
                elif self.__agent.get_state() == "EXECUTING" and self.__hey_dobby_mode():
                    self.log_console("Listening for Dobby...", True)
                    self.__begin_idling()

    def __hey_dobby_mode(self):
        if self.__ui_enabled:
            return self.__ui.hey_dobby_mode.get()
        return True

    def __set_receiving_response(self, val):
        if self.__is_recording and not val:
            self.__toggle_recording(False)
        if val and self.__ui_enabled:
            self.__ui.enable_input(False)
            self.__ui.enable_recording(False)
        self.__audio_recorder.set_recieving_response(val)
        self.__event_flag = False
        if not val:
            self.log_console("")
        if val:
            self.__audio_recorder.start_speaking(finished_callback=self.__finished_speaking_callback)

    def __set_event_flag(self):
        self.__event_flag = True

    def __incoming_response(self, chunk):
        self.__current_response_phrase += chunk
        self.log_console(chunk, end="")
        if re.search(r"[a-zA-Z][.?!,;:\(\)\n]", self.__current_response_phrase):
            if (
                "robot:" not in self.__current_response_phrase.lower()
                and "dobby:" not in self.__current_response_phrase.lower()
            ):
                self.__audio_recorder.enqueue_speech_line(self.__current_response_phrase)
            self.__current_response_phrase = ""

    def __finished_speaking_callback(self):
        self.__enqueue_callback(self.__finished_speaking)

    def __finished_speaking(self, followup=True):
        self.__audio_recorder.stop_speaking()
        if self.__ui_enabled:
            self.__ui.enable_recording(True)
            self.__ui.enable_input(True)
        if self.__last_message:
            self.__begin_idling()
            self.__last_message = False
        elif followup and self.__hey_dobby_mode() and not self.__is_recording:
            self.__toggle_recording()

    def __enqueue_callback(self, callback):
        if self.__verbose:
            print(f"{callback} queued")
        self.__callback_queue.put(callback)

    def __consume_callback(self):
        if self.__callback_queue.empty():
            return
        callback = self.__callback_queue.get(False)
        if self.__verbose:
            print(f"running {callback}")
        callback()

    def main_loop(self):
        if self.__ui_enabled:
            while not self.__ui.is_exit_clicked():
                self.__ui.update()
                self.__consume_callback()
        else:
            while True:
                self.__consume_callback()

        self.__audio_recorder.stop_recording()
        self.__audio_recorder.stop_speaking()

if __name__ == "__main__":
    dobby = Dobby()
    dobby.main_loop()