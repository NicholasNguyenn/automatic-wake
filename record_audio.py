#this is what chatGPT gave me. Let's compare this to DobbyLib
# and seperate into methods

import pyaudio
import wave
import pocketsphinx as ps

# Set audio recording parameters
FORMAT = pyaudio.paInt16  # 16-bit resolution
CHANNELS = 1              # 1 channel (mono)
RATE = 16000              # 16kHz sampling rate
CHUNK = 1024              # 1024 samples per frame
RECORD_SECONDS = 5        # Record for 5 seconds
WAVE_OUTPUT_FILENAME = "recorded_audio.wav"

# Initialize PyAudio
audio = pyaudio.PyAudio()

# Start recording
stream = audio.open(format=FORMAT, channels=CHANNELS,
                    rate=RATE, input=True,
                    frames_per_buffer=CHUNK)

print("Recording...")
frames = []

for _ in range(int(RATE / CHUNK * RECORD_SECONDS)):
    data = stream.read(CHUNK)
    frames.append(data)

print("Finished recording.")

# Stop and close the stream
stream.stop_stream()
stream.close()
audio.terminate()

# Save the recorded data as a WAV file
wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
wf.setnchannels(CHANNELS)
wf.setsampwidth(audio.get_sample_size(FORMAT))
wf.setframerate(RATE)
wf.writeframes(b''.join(frames))
wf.close()

# Speech-to-text using PocketSphinx
# Initialize the PocketSphinx decoder
decoder = ps.Decoder()

# Open the recorded audio file
with open(WAVE_OUTPUT_FILENAME, 'rb') as audio_file:
    decoder.start_utt()
    while True:
        buf = audio_file.read(1024)
        if not buf:
            break
        decoder.process_raw(buf, False, False)
    decoder.end_utt()

# Print the decoded text
print("Speech-to-text result:")
print(decoder.hyp().hypstr)
