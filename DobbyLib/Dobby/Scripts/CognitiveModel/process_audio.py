# import pyaudio NOT SURE IF OTHER IMPORTS RELY ON THIS BUT SHOULD BE GOOD
import wave
import re
from pyannote.audio import Pipeline
from pydub import AudioSegment
import whisper

class AudioProcessor:
    # Set audio recording parameters
    # FORMAT = pyaudio.paInt16  # 16-bit resolution
    # CHANNELS = 1              # 1 channel (mono)
    # RATE = 16000              # 16kHz sampling rate
    # CHUNK = 512              # 512 samples per frame
    # RECORD_SECONDS = 10        # Record for 5 seconds
    # WAVE_OUTPUT_FILENAME = "recorded_audio.wav"

    def __init__(self):
        print("making audio processor")
        # self.audio = pyaudio.PyAudio()
        # self.frames = []
    
    # def record_audio(self):
    #     # Reinitialize PyAudio to ensure a fresh instance
    #     self.audio = pyaudio.PyAudio()
    #     self.frames = []

    #     # Open the stream
    #     stream = self.audio.open(
    #         format=self.FORMAT, 
    #         channels=self.CHANNELS,
    #         rate=self.RATE, 
    #         input=True, 
    #         input_device_index=1,  # Keep this if you know the specific input device
    #         frames_per_buffer=self.CHUNK
    #     )
        
    #     print("start recording")
        
    #     try:
    #         # Record for specified duration
    #         for _ in range(int(self.RATE / self.CHUNK * self.RECORD_SECONDS)):
    #             # Read the stream only once per iteration
    #             data = stream.read(self.CHUNK)
    #             self.frames.append(data)

    #         print("Finished recording.")

    #     except Exception as e:
    #         print(f"Error during recording: {e}")
        
    #     finally:
    #         # Stop and close the stream
    #         stream.stop_stream()
    #         stream.close()
    #         self.audio.terminate()

    #         # Save the recorded data as a WAV file
    #         wf = wave.open(self.WAVE_OUTPUT_FILENAME, 'wb')
    #         wf.setnchannels(self.CHANNELS)
    #         wf.setsampwidth(self.audio.get_sample_size(self.FORMAT))
    #         wf.setframerate(self.RATE)
    #         wf.writeframes(b''.join(self.frames))
    #         wf.close()

    #Load and run speaker diarization with Pyannote on audio_file
    def run_diarization(self, audio_file):
        # Load the pre-trained diarization model
        # pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization")
        
        pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        use_auth_token="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")
    
        # Run diarization on your audio file
        diarization = pipeline(audio_file)
        
        # Save diarization result to RTTM file
        with open("diarization.rttm", "w") as rttm:
            diarization.write_rttm(rttm)
        
        print("Diarization complete, saved to diarization.rttm.")
        return "diarization.rttm"

    # Parse RTTM file to extract speaker segments
    # returns list of (speaker, start_time, duration) entries that describe 
    # each segment of audio
    def parse_rttm(self, rttm_file):
        diarization_segments = []
        with open(rttm_file, "r") as rttm:
            for line in rttm:
                parts = line.strip().split()
                speaker = parts[7]
                start_time = float(parts[3]) * 1000  # Convert to milliseconds
                duration = float(parts[4]) * 1000    # Convert to milliseconds
                diarization_segments.append((speaker, start_time, duration))
        return diarization_segments

    # Transcribe audio_file to a turn based conversation using the 
    # information describing each segment in diarization_segments
    def transcribe_segments(self, audio_file, diarization_segments):
        # Load the audio file with pydub
        audio = AudioSegment.from_wav(audio_file)
        
        # Load the Whisper model
        model = whisper.load_model("small")
        
        # List to hold transcription for each turn of speaking
        turn_transcriptions = []

        for speaker, start, duration in diarization_segments:
            # Extract segment audio
            segment_audio = audio[start:start + duration]
            segment_file = "temp_segment.wav"
            segment_audio.export(segment_file, format="wav")
            
            # Transcribe the audio segment with Whisper
            result = model.transcribe(segment_file)
            text = result["text"]
            
            turn_transcriptions.append(f"{speaker}: {text}")
            
            print(f"Transcribed segment for {speaker}: {text}")

        final_transcription = '\n'.join(turn_transcriptions)
        
        return final_transcription


