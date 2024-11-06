import record_audio as rec
import model_response as llama


def main():

    #record audio
    recorder = rec.Recorder()
    recorder.record_audio()

    # Run diarization on the recorded audio
    rttm_file = rec.run_diarization(recorder.WAVE_OUTPUT_FILENAME)
    
    # Parse RTTM for speaker segments
    diarization_segments = rec.parse_rttm(rttm_file)
    
    # Transcribe audio into turn based conversation given the diarization segments
    speaker_transcriptions = rec.transcribe_segments(recorder.WAVE_OUTPUT_FILENAME, 
                                                 diarization_segments)
    
    # Decide if we should respond given the conversation we've heard
    model = llama.Model()
    action = model.appropriate_action()
    print("action decided by model: ")
    print (action)

# Run the script
if __name__ == "__main__":
    main()