import Dobby.Scripts.auto_wake.record_audio as rec
import Dobby.Scripts.auto_wake.model_response as gpt
import json
import Dobby.Scripts.auto_wake.tokens as model_key

class CognitiveModel:

    def __init__(self):
        self.recorder = rec.AudioProcessor()
        self.model = gpt.LLModel(model_key.gpt_key)


    def listen_loop(self):

        #record audio
        self.recorder.record_audio()

        # Run diarization on the recorded audio
        rttm_file = self.recorder.run_diarization(self.recorder.WAVE_OUTPUT_FILENAME)
        
        # Parse RTTM for speaker segments
        diarization_segments = self.recorder.parse_rttm(rttm_file)
        
        # Transcribe audio into turn based conversation given the diarization segments
        speaker_transcriptions = self.recorder.transcribe_segments(self.recorder.WAVE_OUTPUT_FILENAME, 
                                                    diarization_segments)
        
        # Decide if we should respond given the conversation we've heard
        response = self.model.appropriate_action(speaker_transcriptions)
        action = json.loads(response)
        print(action["name"])
        return action
