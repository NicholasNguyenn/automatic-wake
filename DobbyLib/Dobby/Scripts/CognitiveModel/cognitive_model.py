import Dobby.Scripts.CognitiveModel.process_audio as aud_proc
import Dobby.Scripts.CognitiveModel.model_response as gpt
import json
import Dobby.Scripts.CognitiveModel.tokens as model_key
import wave
import re
from collections import deque

class CognitiveModel:

    do_nothing = { "name": "do_nothing" }
    

    def __init__(self):
        self.audio = aud_proc.AudioProcessor()
        self.model = gpt.LLModel(model_key.gpt_key)
        self.conversation = deque(maxlen=5)


    def decide_action(self, audio_recording="Dobby/Data/audio/input_audio.wav"):
        #AUDIO FILE MIGHT NEED ".wav" AT END NOT SURE CUZ I CAN'T RUN IT

        #If audio is empty there is no need to invoke models for processing
        with wave.open(audio_recording, 'rb') as wave_file:
            if wave_file.getnframes() == 0:
                return self.do_nothing

        # Run diarization on the recorded audio
        rttm_file = self.audio.run_diarization(audio_recording)
        
        # Parse RTTM for speaker segments
        diarization_segments = self.audio.parse_rttm(rttm_file)
        
        # Transcribe audio into turn based conversation given the diarization segments
        speaker_transcriptions = self.audio.transcribe_segments(audio_recording, 
                                                    diarization_segments)
        if not speaker_transcriptions:
            print("no new transcriptions, going to return early before getting in to an infinite loop")
            for i in range(len(speaker_transcriptions)):
                print(f"spearker[{i}]: {speaker_transcriptions[i]}") 
            return self.do_nothing


        # Add transcribed lines to conversation
        for i in range(len(speaker_transcriptions)):
            self.update_conversation(speaker_transcriptions[i])

        # Decide if we should respond given the conversation we've heard
        print("current conversation")
        updated_convo = "\n".join(self.conversation)
        print(updated_convo)
        response = self.model.appropriate_action(updated_convo)
        if not response or response.strip == "":
            print("empty response from cognitive model")
            return self.do_nothing
        print("RESPONSE FROM COGNITIVE MODEL: ")
        response = response.strip("`").strip("json")
        print(response)
        try: 
            action = json.loads(response)
        except:
            print("parsing resopnse from cogntnive model wen't wrong. Defaulting to do nothing")
            return self.do_nothing
        print("returning action")
        return action
    
    def update_conversation(self, conversation_line, dobby=False):
        if dobby:
            self.conversation.append(f"Dobby: {conversation_line}")
        else:
            self.conversation.append(conversation_line)


    def clear_conversation(self):
        self.conversation.clear()
