import wave
import pyaudio
import streamlit as st
import torch
import numpy as np
import noisereduce as nr
from elevenlabs import ElevenLabs, stream as el_stream
from faster_whisper import WhisperModel

# --- Recording State ---
audio_frames = []
is_recording = False
record_thread = None

def start_recording(filename="voice_record.wav"):
    """
    Starts recording audio in a separate thread.
    The nested 'record' function now includes a noise reduction step.
    """
    global is_recording, audio_frames, record_thread
    is_recording = True
    audio_frames = []

    def record():
        chunk = 1024
        format = pyaudio.paInt16
        channels = 1
        rate = 16000
        p = pyaudio.PyAudio()
        stream = p.open(format=format,
                        channels=channels,
                        rate=rate,
                        input=True,
                        frames_per_buffer=chunk)
        
        while is_recording:
            data = stream.read(chunk)
            audio_frames.append(data)
            
        stream.stop_stream()
        stream.close()
        p.terminate()

        # --- OPTIMIZATION 1: Noise Reduction Step ---
        # Combine all recorded frames into a single byte string
        raw_data = b''.join(audio_frames)
        
        # Convert the raw audio data to a NumPy array for processing
        audio_np = np.frombuffer(raw_data, dtype=np.int16)
        
        # Perform noise reduction
        # The library automatically isolates and removes stationary noise
        reduced_noise_audio = nr.reduce_noise(y=audio_np, sr=rate)
        
        # Convert the cleaned NumPy array back to bytes
        cleaned_bytes = reduced_noise_audio.astype(np.int16).tobytes()

        # Save the cleaned audio data to the WAV file
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(p.get_sample_size(format))
            wf.setframerate(rate)
            wf.writeframes(cleaned_bytes)

    import threading
    record_thread = threading.Thread(target=record)
    record_thread.start()

def stop_recording(filename="voice_record.wav"):
    """Stops the recording thread and returns the filename."""
    global is_recording, record_thread
    is_recording = False
    if record_thread:
        record_thread.join()
    return filename

def transcribe_audio(path, model_name="tiny"):
    """
    Transcribes the audio file using faster-whisper.
    Now includes Voice Activity Detection (VAD) to ignore non-speech segments.
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"
    st.markdown(f"🛠️ Using Whisper model: `{model_name}` on `{device}`")

    try:
        # Load the model (using int8 for better performance on CPU)
        model = WhisperModel(model_name, device=device, compute_type="int8")

        # --- OPTIMIZATION 2: Voice Activity Detection (VAD) ---
        # Transcribe with VAD filter enabled to only process speech segments
        with st.spinner("🎧 Analyzing speech and transcribing..."):
            segments, _ = model.transcribe(
                path,
                beam_size=5,
                language="en",
                vad_filter=True,  # Enable the VAD filter
                vad_parameters=dict(min_silence_duration_ms=500), # Configure VAD
            )
            return " ".join([seg.text for seg in segments])
    except Exception as e:
        st.error(f"Error during transcription: {e}")
        return ""

def speak_text(response_text, api_key):
    """Converts text to speech using ElevenLabs API."""
    if not api_key:
        st.warning("🔇 ElevenLabs API key not set.")
        return
    try:
        client = ElevenLabs(api_key=api_key)
        audio = client.generate(
            text=response_text,
            voice="hGb0Exk8cp4vQEnwolxa",  # Replace with your voice ID
            model="eleven_multilingual_v2",
            stream=True
        )
        el_stream(audio)
    except Exception as e:
        st.error(f"🛑 TTS Error: {e}")
