import record_audio as rec
import model_response as llama


class CognitiveModel:

    def __init__(self):
        self.recorder = rec.AudioProcessor()
        self.model = llama.LLModel()


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
        action = self.model.appropriate_action(speaker_transcriptions)
        print("action decided by model: ")
        print (action)
        
        return action
