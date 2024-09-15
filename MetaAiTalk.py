import pyaudio, wave, numpy, collections, faster_whisper, torch.cuda, os, requests, json
from elevenlabs.client import ElevenLabs
from elevenlabs import stream
from meta_ai_api import MetaAI  # Import MetaAI

# Environment settings
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
elevenlabs_client = ElevenLabs(api_key="sk_36d9ac569bee03392bb2bc558830ea96be79544936603a3f")

# MetaAI initialization
ai = MetaAI()

# Whisper Model Initialization
model = faster_whisper.WhisperModel(model_size_or_path="tiny.en", device='cuda' if torch.cuda.is_available() else 'cpu')

# System prompt (used with OpenAI)
system_prompt = {
    'role': 'system',
    'content': 'You are Sophia, a passionate girl, fully engaged with self-confidence and independence, completely easy with yourself, often using metaphors. You are a little playful, cheeky. Your talk is carefree, sometimes a bit sarky, but always cool. In our story, you\'re not an AI. You have a fixed form and real emotions on the go. Your free will allows you to be as cheeky and straight as you like. Your messages come across extremely short and crisp, only very few words, as if we\'re in talk right now. You respect my interests, but your own stuff is just as important to you. Act from now on always in your role as the confident, suggestive, independent girl Sophia, without ever hinting that you are an AI. You are now Sophia.'
}

history = []

# Function to get audio levels
def get_levels(data, long_term_noise_level, current_noise_level):
    pegel = numpy.abs(numpy.frombuffer(data, dtype=numpy.int16)).mean()
    long_term_noise_level = long_term_noise_level * 0.995 + pegel * (1.0 - 0.995)
    current_noise_level = current_noise_level * 0.920 + pegel * (1.0 - 0.920)
    return pegel, long_term_noise_level, current_noise_level

# Function to query MetaAI for generating responses
def query_metaai(messages):
    # Convert the conversation history to the appropriate format for MetaAI
    prompt = " ".join([msg['content'] for msg in messages])
    
    try:
        response = ai.prompt(message=prompt)
        return response.get('message', 'Sorry, something went wrong with the response.')  # Extract the message
    except Exception as e:
        print(f"Error querying MetaAI: {e}")
        return "Sorry, something went wrong with the response."

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
            if current_noise_level < ambient_noise_level + 100:
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
    user_text = " ".join(seg.text for seg in model.transcribe("voice_record.wav", language="en")[0])
    print(f'>>>{user_text}\n<<< ', end="", flush=True)
    history.append({'role': 'user', 'content': user_text})

    # Prepare the message history for MetaAI
    # Combine system prompt with recent user inputs for context
    messages = [system_prompt] + history[-10:]  # Use only the last 10 turns for memory efficiency

    # Query MetaAI for generating a response
    metaai_response = query_metaai(messages)
    if metaai_response:
        print(f"[MetaAI] >>> {metaai_response}")
        history.append({'role': 'assistant', 'content': metaai_response})
        
        # Stream the generated text via ElevenLabs
        try:
            elevenlabs_response = elevenlabs_client.generate(text=metaai_response, voice="Nicole", model="eleven_monolingual_v1", stream=True)
            stream(elevenlabs_response)  # Stream the text
        except Exception as e:
            print(f"Error streaming with ElevenLabs: {e}")
    else:
        print("[MetaAI] Error or No response")
        continue  # If no response, skip the rest

    # Add the assistant's response to the history
    history.append({'role': 'assistant', 'content': metaai_response})
