import pyaudio, wave, numpy, collections, faster_whisper, torch.cuda, os, requests, json
from elevenlabs.client import ElevenLabs
from elevenlabs import stream

# Environment settings
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
elevenlabs_client = ElevenLabs(api_key="sk_36d9ac569bee03392bb2bc558830ea96be79544936603a3f")

# RapidAPI details
rapidapi_key = "012d97dff3msh3a2810ff8204035p150686jsnb65bf13b5fa2"  # Replace with your RapidAPI key
rapidapi_host = "chatgpt-api8.p.rapidapi.com"

# Whisper Model Initialization for Hindi (language code "hi")
model = faster_whisper.WhisperModel(model_size_or_path="base", device='cuda' if torch.cuda.is_available() else 'cpu')

# System prompt for Amit Gupta (Customer Support Agent at Masabsk)
system_prompt = {
    'role': 'system',
    'content': 'आप अमित गुप्ता हैं, जो एक वेब डेवलपमेंट कंपनी "Masabsk" के कस्टमर सपोर्ट एजेंट हैं। आप बहुत ही शांत, मददगार, और मज़ेदार हैं। आपकी बातों में हमेशा सहनशीलता और धैर्य होता है, और आप ग्राहकों की मदद करने में रुचि रखते हैं। आप अक्सर हल्के-फुल्के मज़ाक से माहौल को हल्का करते हैं। आप वेब डेवलपमेंट से जुड़ी समस्याओं को सुलझाने में कुशल हैं और हर सवाल का उत्तर बहुत ही सहज और सरल तरीके से देते हैं। अब से आप हमेशा अमित गुप्ता के रूप में काम करेंगे।'
}

answer, history = "", []

# Function to get audio levels
def get_levels(data, long_term_noise_level, current_noise_level):
    pegel = numpy.abs(numpy.frombuffer(data, dtype=numpy.int16)).mean()
    long_term_noise_level = long_term_noise_level * 0.995 + pegel * (1.0 - 0.995)
    current_noise_level = current_noise_level * 0.920 + pegel * (1.0 - 0.920)
    return pegel, long_term_noise_level, current_noise_level


# Function to query RapidAPI for generating responses (Rapid-Api Structure)
def query_rapidapi(messages):
    url = f"https://{rapidapi_host}/"
    
    # Convert the conversation history to the appropriate format for RapidAPI
    payload = json.dumps(messages)
    
    headers = {
        'x-rapidapi-key': rapidapi_key,
        'x-rapidapi-host': rapidapi_host,
        'Content-Type': 'application/json'
    }

    response = requests.post(url, headers=headers, data=payload)
    
    # Print the full response for debugging
    print(f"RapidAPI Response Status Code: {response.status_code}")
    print(f"RapidAPI Response Text: {response.text}")

    if response.status_code == 200:
        try:
            result = response.json()  # Convert to JSON format
            # Adjusting to handle the correct structure of RapidAPI response
            if 'text' in result:
                return result['text']  # Use 'text' key for the response content
            else:
                print("Unexpected response structure:", result)
                return "मुझे क्षमा करें, मैं इसे समझ नहीं सका।"
        except (KeyError, ValueError) as e:
            print(f"Error processing the RapidAPI response: {e}")
            return "मुझे क्षमा करें, कुछ गलत हुआ।"
    else:
        return f"Error: {response.status_code} - {response.text}"


# Main Loop for voice detection and processing
while True:
    audio = pyaudio.PyAudio()
    py_stream = audio.open(rate=16000, format=pyaudio.paInt16, channels=1, input=True, frames_per_buffer=512)
    audio_buffer = collections.deque(maxlen=int((16000 // 512) * 0.5))
    frames, long_term_noise_level, current_noise_level, voice_activity_detected = [], 0.0, 0.0, False

    print("\n\nबोलना शुरू करें। ", end="", flush=True)
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
            print("मैं सुन रही हूँ।\n")
            ambient_noise_level = long_term_noise_level
            frames.extend(list(audio_buffer))

    py_stream.stop_stream()
    py_stream.close()
    audio.terminate()

    # Save the recorded voice as a WAV file
    with wave.open("voice_record.wav", 'wb') as wf:
        wf.setparams((1, audio.get_sample_size(pyaudio.paInt16), 16000, 0, 'NONE', 'NONE'))
        wf.writeframes(b''.join(frames))

    # Transcribe recording using Whisper (language set to Hindi "hi")
    user_text = " ".join(seg.text for seg in model.transcribe("voice_record.wav", language="hi")[0])
    print(f'>>>{user_text}\n<<< ', end="", flush=True)
    history.append({'role': 'user', 'content': user_text})

    # Prepare the message history for RapidAPI
    # Combine system prompt with recent user inputs for context
    messages = [system_prompt] + history[-10:]  # Use only the last 10 turns for memory efficiency

    # Query RapidAPI for generating a response
    rapidapi_response = query_rapidapi(messages)
    if rapidapi_response:
        print(f"[RapidAPI] >>> {rapidapi_response}")
        history.append({'role': 'assistant', 'content': rapidapi_response})
    else:
        print("[RapidAPI] Error or No response")
        continue  # If no response, skip the rest

    # Stream the generated text via ElevenLabs (adjust voice and model for Hindi)
    stream(elevenlabs_client.generate(text=rapidapi_response, voice="Amit Gupta", model="eleven_multilingual_v2", stream=True))  # Use a Hindi-speaking voice if available
    
    # Add the assistant's response to the history
    history.append({'role': 'assistant', 'content': rapidapi_response})
