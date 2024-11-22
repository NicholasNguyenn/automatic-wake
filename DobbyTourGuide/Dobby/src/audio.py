import time
from playsound import playsound
from gtts import gTTS
import os
import threading
import wave
from google.cloud import texttospeech
from google.cloud import speech
from pocketsphinx import *
import audioop
import pyaudio
import io
import numpy as np
from functools import partial
import math
import face_interface
import re
from collections import deque
import data
from CognitiveModel.cognitive_model import CognitiveModel

#from elevenlabs import voices, generate, play, stream, save, Voice


# Class for handling audio recording and playback on Dobby.
# Controls the microphone and speaker, and handles the generation of audio from text.

# generate a dictionary file with http://www.speech.cs.cmu.edu/tools/lextool.html

input_file_count = 0

from openai import OpenAI
openai_client = OpenAI(api_key=data.OPENAI_API_KEY)

# Set up audio input stream
class Recorder:
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    CHUNK = 512
    WAVE_OUTPUT_FILENAME = "Dobby/Data/audio/input_audio"

    speech_line_queue = list()
    speech_file_queue = list()
    file_count = 0
    generating_audio = False

    def __init__(self, enqueue_callback):
        modeldir = get_model_path()
        self.decoder = Decoder(
            keyphrase="dobby",
            hmm=os.path.join(modeldir, "en-us/en-us"),
            dict="Dobby/Data/audio/keyword.dict",
            kws_threshold=1e-9,
        )
        self.frames = []
        self.audio = pyaudio.PyAudio()
        self.talking_threshold = 40
        self.stop_recording_event = threading.Event()
        self.stop_listening_event = threading.Event()
        self.stop_speaking_event = threading.Event()
        self.speaking = False
        self.user_speaking = False
        self.recieving_response = False
        self.enqueue_callback = enqueue_callback
        self.recording = False
        self.cognitive_model = CognitiveModel()

    def calibrate_microphone(self, threshold=2):
        print("Calibrating microphone for 5 chunks... Stay silent")

        stream = self.audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK,
        )

        chunks = 0
        rms_array = []
        while chunks < 10:
            data = stream.read(self.CHUNK, exception_on_overflow=False)
            cur_rms = audioop.rms(data, 2)
            print(cur_rms)
            rms_array.append(cur_rms)
            chunks += 1
        a = np.array(rms_array)
        background_rms = np.median(a)
        print("Median background noise: " + str(background_rms))
        self.talking_threshold = background_rms * threshold

        stream.stop_stream()
        stream.close()

    def start_recording(self, finished_callback, auto_stop=False):
        # start recording thread
        self.recording = True
        self.stop_recording_event = threading.Event()
        self.record_thread = threading.Thread(
            target=self.record_audio, args=(finished_callback, auto_stop), daemon=True)
        self.record_thread.start()

    def stop_recording(self):
        # stop recording thread
        self.stop_recording_event.set()
        while self.recording:
            time.sleep(0.1)

    def record_audio(self, finished_callback=None, auto_stop=False):
        global input_file_count
        stream = self.audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK,
        )

        max_silent_chunks = 12
        max_silent_chunks_convo = 6
        silent_chunks = 0
        last_rms = 0
        total_rms = 0
        chunks = 0
        self.user_speaking = False
        speaking_threshold = 0
     
        print("Recording...")
        while not self.stop_recording_event.is_set() and (
            not auto_stop or silent_chunks < max_silent_chunks
        ):
            data = stream.read(self.CHUNK, exception_on_overflow=False)
            self.frames.append(data)
            chunks += 1
            rms = audioop.rms(data, 2)
            face_interface.set_audio_level(rms, speaking_threshold)
            total_rms += rms

            if chunks > 10:
                rms = total_rms / chunks
                chunks = 0
                total_rms = 0
                print("Audio Level: " + str(rms))
                # spike in volume means we started speaking
                if last_rms != 0 and rms - last_rms > last_rms * 0.8:
                    if not self.user_speaking:
                        self.user_speaking = True
                        #set threshold halfway between silent and speaking 
                        speaking_threshold = last_rms + (rms - last_rms) * 0.5
                        print ("Started speaking " + str(speaking_threshold))
                        max_silent_chunks = max_silent_chunks_convo
                    silent_chunks = 0
                if rms < speaking_threshold or speaking_threshold == 0:
                    self.user_speaking = False
                    silent_chunks += 1
                last_rms = rms


        print("Stopping recording...")

        stream.stop_stream()
        stream.close()

        # Save recorded audio to file
        input_file_count += 1
        file_name = self.WAVE_OUTPUT_FILENAME + ".wav"
        waveFile = wave.open(file_name, "wb")
        waveFile.setnchannels(self.CHANNELS)
        waveFile.setsampwidth(self.audio.get_sample_size(self.FORMAT))
        waveFile.setframerate(self.RATE)
        waveFile.writeframes(
            b"".join(self.frames[: len(self.frames) - (min(0, silent_chunks - 1))])
        )
        waveFile.close()
        print("Saved recording to", file_name)
        self.frames = []

        #recorder.add_audio_clip(file_name, time.time())

        if not self.stop_recording_event.is_set() and auto_stop:
            self.enqueue_callback(finished_callback)

        self.recording = False

    def start_listening(self, callback):
        self.stop_listening_event = threading.Event()
        self.listen_thread = threading.Thread(
            target=self.wait_turn, args=(callback,), daemon=True
        )
        self.listen_thread.start()

    def stop_listening(self):
        # stop listening thread
        self.stop_listening_event.set()

    # Listen to ongoing conversation, cognitive model will return when it is
    # appropriate for Dobby to interject
    def wait_turn(self, callback):
        while not self.stop_listening_event.is_set():
            action = self.cognitive_model.listen_loop()
            if action["name"] == 'get_robot_response' and not self.stop_listening_event.is_set():
                callback(action["parameters"]["user_input"])

    # Listens for keyword to begin listening for speech. Default is "Dobby"
    def listen_keyword(self, callback):
        stream_single = self.audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK,
        )

        self.decoder.start_utt()
        # Loop until keyword is detected
        while not self.stop_listening_event.is_set():
            data = stream_single.read(self.CHUNK, exception_on_overflow=False)
            self.frames = [data]
            self.decoder.process_raw(data, False, False)
            if self.decoder.hyp() != None:
                print(
                    [
                        (seg.word, seg.prob, seg.start_frame, seg.end_frame)
                        for seg in self.decoder.seg()
                    ]
                )
                if not self.stop_listening_event.is_set():
                    self.enqueue_callback(partial(callback, "front", 0))
        self.decoder.end_utt()
        stream_single.stop_stream()
        stream_single.close()

    def enqueue_speech_line(self, line):
        self.speech_line_queue.append(line)
    
    def set_recieving_response(self, recieving):
        self.recieving_response = recieving

    def start_speaking(self, finished_callback):
        self.stop_speaking_event = threading.Event()
        if not self.speaking:
            self.recieving_response = True
            self.file_count = 0
            self.speaking = True
            self.speak_thread = threading.Thread(
                target=self.speak_lines, args=(finished_callback,), daemon=True
            )
            self.speak_thread.start()
            self.tts_thread = threading.Thread(target=self.text_to_speech, daemon=True)
            self.tts_thread.start()

    # Generate audio from text
    def text_to_speech(self):
        pattern = re.compile(r"\((.*?)\)")
        #voice = Voice(voice_id="e1m53KLIEGzPB8wotn3d")

        while not self.stop_speaking_event.isSet():
            if len(self.speech_line_queue) > 0:
                self.generating_audio = True
                text = self.speech_line_queue.pop(0)
                print(text)
                match = pattern.search(text)
                if match:
                    # an emotion was specified
                    filename = match.group(1)
                    self.speech_file_queue.append(filename)
                if len(text) > 0:
                    self.file_count += 1
                    filename = f"Dobby/Data/audio/output_audio{self.file_count}.mp3"
                    response = openai_client.audio.speech.create(
                        model="tts-1",
                        voice="nova",
                        input=text,
                    )

                    response.stream_to_file(filename)

                    """synthesis_input = texttospeech.SynthesisInput(text=text)
                    response = client.synthesize_speech(
                        input=synthesis_input, voice=voice, audio_config=audio_config
                    )
                    with open(filename, "wb") as out_file:
                        out_file.write(response.audio_content)"""
                    """audio = generate(
                        text=text,
                        voice="Daniel",
                        model="eleven_multilingual_v1",
                        api_key="1832fbcffb93b263ffee1b2762f16119"
                    )
                    save (audio, filename)"""
                    self.speech_file_queue.append(filename)
                    self.generating_audio = False

    # Use TTS to speak lines
    def speak_lines(self, finished_callback):
        started = False
        while not self.stop_speaking_event.isSet():
            if len(self.speech_file_queue) > 0:
                filename = self.speech_file_queue.pop(0)
                if not filename.endswith(".mp3"):
                    face_interface.set_emotion(filename)
                else:
                    #recorder.add_audio_clip(filename, time.time())
                    playsound(filename, True)
                    os.remove(filename)
                started = True
            elif (
                started and
                not self.recieving_response
                and not self.generating_audio
                and len(self.speech_line_queue) == 0
                and finished_callback is not None
            ):  # no more audio in both queues
                self.enqueue_callback(finished_callback)
                started = False

    # Handle the end of speaking
    def stop_speaking(self):
        self.file_count = 0
        self.stop_speaking_event.set()
        self.speaking = False


## Intialize Google API for speech recognition
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "Dobby/Data/audio/google_api_config.json"
client = texttospeech.TextToSpeechClient()
speechClient = speech.SpeechClient()
voice = texttospeech.VoiceSelectionParams(
    language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.MALE
)
audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

speech_config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    enable_automatic_punctuation=True,
    audio_channel_count=1,
    language_code="en-US",
)

def transcribe_into_text(filename="Dobby/Data/audio/input_audio"):
    with io.open(filename + ".wav", "rb") as audio_file:
        content = audio_file.read()
        audio = speech.RecognitionAudio(content=content)

    response = speechClient.recognize(request={"config": speech_config, "audio": audio})
    transcript = ""
    for result in response.results:
        transcript += result.alternatives[0].transcript

    return transcript