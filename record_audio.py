import pyaudio
import wave
import re
from pyannote.audio import Pipeline
from pydub import AudioSegment
import whisper

class Recorder:
    # Set audio recording parameters
    FORMAT = pyaudio.paInt16  # 16-bit resolution
    CHANNELS = 1              # 1 channel (mono)
    RATE = 16000              # 16kHz sampling rate
    CHUNK = 512              # 1024 samples per frame
    RECORD_SECONDS = 10        # Record for 5 seconds
    WAVE_OUTPUT_FILENAME = "recorded_audio.wav"

    def __init__(self):
        print("making recorder")
        self.audio = pyaudio.PyAudio()
        self.frames = []
    
    def record_audio(self):
        stream = self.audio.open(format= self.FORMAT, channels= self.CHANNELS,
                    rate= self.RATE, input=True,
                    frames_per_buffer= self.CHUNK)
        print("start recording")
        
        for _ in range(int(self.RATE / self.CHUNK * self.RECORD_SECONDS)):
            data = stream.read(self.CHUNK)
            self.frames.append(data)

        print("Finished recording.")

        # Stop and close the stream
        stream.stop_stream()
        stream.close()
        self.audio.terminate()

        # Save the recorded data as a WAV file
        wf = wave.open(self.WAVE_OUTPUT_FILENAME, 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(self.audio.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(b''.join(self.frames))
        wf.close()

        
        
        



# Step 1: Load and Run Speaker Diarization with Pyannote
def run_diarization(audio_file):
    # Load the pre-trained diarization model
    pipeline = Pipeline.from_pretrained(
        "Revai/reverb-diarization-v2",
        use_auth_token="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")
    
    # Run diarization on your audio file
    diarization = pipeline(audio_file)
    
    # Save diarization result to RTTM format
    with open("diarization.rttm", "w") as rttm:
        diarization.write_rttm(rttm)
    
    print("Diarization complete, saved to diarization.rttm.")
    return "diarization.rttm"

# Step 2: Parse RTTM File to Extract Speaker Segments
def parse_rttm(rttm_file):
    diarization_segments = []
    with open(rttm_file, "r") as rttm:
        for line in rttm:
            parts = line.strip().split()
            speaker = parts[7]
            start_time = float(parts[3]) * 1000  # Convert to milliseconds
            duration = float(parts[4]) * 1000    # Convert to milliseconds
            diarization_segments.append((speaker, start_time, duration))
    return diarization_segments

# Step 3: Transcribe Each Segment with Whisper
def transcribe_segments(audio_file, diarization_segments):
    # Load the audio file with pydub
    audio = AudioSegment.from_wav(audio_file)
    
    # Load the Whisper model
    model = whisper.load_model("small")
    
    # Dictionary to hold speaker transcriptions
    speaker_transcriptions = {}

    for speaker, start, duration in diarization_segments:
        # Extract segment audio
        segment_audio = audio[start:start + duration]
        segment_file = "temp_segment.wav"
        segment_audio.export(segment_file, format="wav")
        
        # Transcribe the audio segment with Whisper
        result = model.transcribe(segment_file)
        text = result["text"]
        
        # Append transcription with speaker label
        if speaker not in speaker_transcriptions:
            speaker_transcriptions[speaker] = []
        speaker_transcriptions[speaker].append(text)
        
        print(f"Transcribed segment for {speaker}: {text}")
    
    return speaker_transcriptions

# Step 4: Print or Save the Speaker-Labeled Transcriptions
def print_transcriptions(speaker_transcriptions):
    for speaker, texts in speaker_transcriptions.items():
        print(f"\nSpeaker {speaker}:")
        for text in texts:
            print(f"  {text}")

# Main function to run all steps
def main():
    #record audio
    recorder = Recorder()
    recorder.record_audio()

    # Run diarization
    rttm_file = run_diarization(recorder.WAVE_OUTPUT_FILENAME)
    
    # Parse RTTM for speaker segments
    diarization_segments = parse_rttm(rttm_file)
    
    # Transcribe segments and label with speaker
    speaker_transcriptions = transcribe_segments(recorder.WAVE_OUTPUT_FILENAME, 
                                                 diarization_segments)
    
    # Print speaker-labeled transcriptions
    print_transcriptions(speaker_transcriptions)

# Run the script
if __name__ == "__main__":
    main()
