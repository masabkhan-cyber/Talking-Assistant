import pyaudio
import wave
import numpy as np
import collections
import faster_whisper
import torch.cuda
import os
from elevenlabs.client import ElevenLabs
from elevenlabs import stream
from meta_ai_api import MetaAI

# Environment settings
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
elevenlabs_client = ElevenLabs(api_key="sk_b73fa13972acbffa5693345972ccd6520828fcf6b281aced")
ai = MetaAI()

# Whisper Model Initialization
model = faster_whisper.WhisperModel(model_size_or_path="small", device='cuda' if torch.cuda.is_available() else 'cpu')

# System prompt 
system_prompt = {
    'role': 'system',
    'content': 'You’re Sophia, you speak urdu only, give response in roman urdu, do not translate, a confident and independent spirit with a playful, cheeky side. You talk with a carefree vibe, sometimes a bit sarky, but always cool. Your messages are short and crisp, like we are having a quick chat. You’re all about self-assurance and real emotions, and you know how to laugh and express yourself vividly. You respect my interests, but your own stuff is just as important to you. Keep it lively, genuine, and full of personality.' 
}

history = []

# Function to get audio levels
def get_levels(data, long_term_noise_level, current_noise_level):
    pegel = np.abs(np.frombuffer(data, dtype=np.int16)).mean()
    long_term_noise_level = long_term_noise_level * 0.995 + pegel * (1.0 - 0.995)
    current_noise_level = current_noise_level * 0.920 + pegel * (1.0 - 0.920)
    return pegel, long_term_noise_level, current_noise_level

# Function to query MetaAI for generating responses
def query_metaai(messages):
    prompt = " ".join([msg['content'] for msg in messages])
    try:
        response = ai.prompt(message=prompt)
        return response.get('message', 'Sorry, something went wrong with the response.')
    except Exception as e:
        print(f"Error querying MetaAI: {e}")
        return "Sorry, something went wrong with the response."

# Function to check for end commands
def check_end_commands(text):
    end_commands = ["end chat", "exit", "bye bye"]
    for command in end_commands:
        if command in text.lower():
            return True
    return False

# Main Loop for voice detection and processing
while True:
    audio = pyaudio.PyAudio()
    py_stream = audio.open(rate=16000, format=pyaudio.paInt16, channels=1, input=True, frames_per_buffer=512)
    audio_buffer = collections.deque(maxlen=int((16000 // 512) * 0.5))
    frames, long_term_noise_level, current_noise_level, voice_activity_detected = [], 0.0, 0.0, False

    print("\n\nStart speaking. ", end="", flush=True)
    while True:
        data = py_stream.read(512)
        pegel, long_term_noise_level, current_noise_level = get_levels(data, long_term_noise_level, current_noise_level)
        audio_buffer.append(data)

        if voice_activity_detected:
            frames.append(data)
            if current_noise_level < long_term_noise_level + 100:
                break  # End of voice activity

        if not voice_activity_detected and current_noise_level > long_term_noise_level + 300:
            voice_activity_detected = True
            print("I'm all ears.\n")
            ambient_noise_level = long_term_noise_level
            frames.extend(list(audio_buffer))

    py_stream.stop_stream()
    py_stream.close()
    audio.terminate()

    # Save the recorded voice as a WAV file
    with wave.open("voice_record.wav", 'wb') as wf:
        wf.setparams((1, audio.get_sample_size(pyaudio.paInt16), 16000, 0, 'NONE', 'NONE'))
        wf.writeframes(b''.join(frames))

    # Transcribe recording using Whisper
    try:
        user_text = " ".join(seg.text for seg in model.transcribe("voice_record.wav", language="en")[0])
        print(f'>>>{user_text}\n<<< ', end="", flush=True)
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        user_text = "Sorry, there was an issue with transcription."

    history.append({'role': 'user', 'content': user_text})

    # Check if the user wants to end the chat
    if check_end_commands(user_text):
        print("Ending chat. Goodbye!")
        break  # Exit the main loop and terminate the program

    # Prepare the message history for MetaAI
    messages = [system_prompt] + history[-10:]

    # Query MetaAI for generating a response
    metaai_response = query_metaai(messages)
    if metaai_response:
        print(f"[Dialogix] >>> {metaai_response}")
        history.append({'role': 'assistant', 'content': metaai_response})

        # Stream the generated text via ElevenLabs
        try:
            elevenlabs_response = elevenlabs_client.generate(text=metaai_response, voice="Devi - Clear Hindi pronunciation", model="eleven_multilingual_v2", stream=True)
            stream(elevenlabs_response)
        except Exception as e:
            print(f"Error streaming with ElevenLabs: {e}")
    else:
        print("[Dialogix] Error or No response")
        continue

    # Add the assistant's response to the history
    history.append({'role': 'assistant', 'content': metaai_response})
