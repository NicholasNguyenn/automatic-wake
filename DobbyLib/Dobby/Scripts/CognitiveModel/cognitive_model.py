import Dobby.Scripts.CognitiveModel.process_audio as aud_proc
import Dobby.Scripts.CognitiveModel.model_response as gpt
import json
import Dobby.Scripts.CognitiveModel.tokens as model_key
import wave

class CognitiveModel:

    def __init__(self):
        self.audio = aud_proc.AudioProcessor()
        self.model = gpt.LLModel(model_key.gpt_key)


    def decide_action(self, audio_recording="Dobby/Data/audio/input_audio"):
        #AUDIO FILE MIGHT NEED ".wav" AT END NOT SURE CUZ I CAN'T RUN IT

        #If audio is empty there is no need to invoke models for processing
        with wave.open(audio_recording, 'rb') as wave_file:
            if wave_file.getnframes() == 0:
                return """
                {
                    "name": "do_nothing"
                }
                """.strip()

        # Run diarization on the recorded audio
        rttm_file = self.audio.run_diarization(audio_recording)
        
        # Parse RTTM for speaker segments
        diarization_segments = self.audio.parse_rttm(rttm_file)
        
        # Transcribe audio into turn based conversation given the diarization segments
        speaker_transcriptions = self.audio.transcribe_segments(audio_recording, 
                                                    diarization_segments)
        
        # Decide if we should respond given the conversation we've heard
        response = self.model.appropriate_action(speaker_transcriptions)
        action = json.loads(response)
        #print(action["name"])
        return action
