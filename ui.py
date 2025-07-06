import os
import time
import json
import base64
import streamlit as st
from fpdf import FPDF
from chat_engine import ChatEngine
from auth import login_user, register_user
from user_data import handle_pdf_upload, save_user_data_from_session, delete_pdf_for_user
from config import save_config
from voice import speak_text, start_recording, stop_recording, transcribe_audio
from quiz_generator import QuizGenerator


# --- UI Enhancement Functions ---

def add_bg_from_local(image_file):
    """Adds a background image from a local file to the Streamlit app."""
    if not os.path.exists(image_file):
        # Don't apply background if file doesn't exist
        return
    with open(image_file, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url(data:image/jpeg;base64,{encoded_string});
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        /* --- General Text & Headers --- */
        .stApp h1, .stApp h2, .stApp h3, .stApp p, .stApp .st-emotion-cache-16idsys p {{
            color: #FFFFFF !important; /* White text for better contrast */
        }}
        /* --- Login/Register Form Specifics --- */
        /* Target the container of the login form for the glass effect */
        div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]:nth-of-type(2) > div {{
            background: rgba(30, 30, 30, 0.7); /* Semi-transparent dark background */
            backdrop-filter: blur(10px);      /* Frosted glass effect */
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;              /* Rounded corners */
        }}
        /* Make input labels white */
        .stTextInput label {{
            color: #FFFFFF !important;
        }}
        /* Style the tabs for the dark background */
        .stTabs [data-baseweb="tab-list"] button {{
            color: #D0D0D0 !important; /* Light gray for inactive tabs */
        }}
        .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {{
            color: #FFFFFF !important; /* White for the active tab */
            border-bottom: 2px solid #FFFFFF;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# --- PDF Generation Helper ---
def create_quiz_pdf(quiz_data):
    """Generates a two-page PDF with questions and an answer key."""
    pdf = FPDF()
    
    # --- Page 1: Questions ---
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, 'Quiz Questions', 0, 1, 'C')
    pdf.ln(10)
    
    # Get the initial left margin for indentation control
    initial_x = pdf.get_x()
    indent = 5 # Indent by 5 units

    for i, q in enumerate(quiz_data):
        # Use a consistent 'latin-1' encoding with replacement for unsupported characters
        question_text = f"Q{i+1}: {q['question']}".encode('latin-1', 'replace').decode('latin-1')
        options = [opt.encode('latin-1', 'replace').decode('latin-1') for opt in q['options']]
        
        pdf.set_font("Arial", 'B', 12)
        pdf.set_x(initial_x) # Ensure we start at the margin
        pdf.multi_cell(0, 6, question_text)
        pdf.ln(2)
        
        pdf.set_font("Arial", '', 12)
        for opt in options:
            pdf.set_x(initial_x)   # Go to the left margin
            pdf.cell(indent)       # Create the indent space
            pdf.multi_cell(0, 6, f"- {opt}") # Write the option text
        pdf.ln(6)

    # --- Page 2: Answer Key ---
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, 'Answer Key', 0, 1, 'C')
    pdf.ln(10)
    
    pdf.set_font("Arial", '', 12)
    for i, q in enumerate(quiz_data):
        answer_text = f"Q{i+1}: {q['answer']}".encode('latin-1', 'replace').decode('latin-1')
        pdf.set_x(initial_x) # Start at the margin
        pdf.multi_cell(0, 6, answer_text)
        pdf.ln(4)
        
    # FIX: Convert the bytearray output to bytes for Streamlit
    return bytes(pdf.output())


# --- Authentication UI ---
def show_login_form():
    """Displays a modern, centered login and registration form using tabs."""
    
    # Apply the background image and custom styles
    add_bg_from_local('background.jpg')

    # Center the login form
    col1, col2, col3 = st.columns([1, 1.5, 1])

    with col2:
        # Create a card-like container for the form
        with st.container(border=True):
            st.markdown("<h1 style='text-align: center;'>🤖 Dialogix</h1>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; margin-bottom: 20px;'>Your AI-powered learning assistant.</p>", unsafe_allow_html=True)

            login_tab, register_tab = st.tabs(["**Login**", "**Register**"])

            # --- Login Tab ---
            with login_tab:
                with st.form(key="login_form"):
                    st.text_input("Username", placeholder="Enter your username", key="login_user")
                    st.text_input("Password", type="password", placeholder="Enter your password", key="login_pass")
                    
                    st.markdown("</br>", unsafe_allow_html=True) # Add some spacing
                    
                    login_button = st.form_submit_button(label="Login", use_container_width=True, type="primary")

                    if login_button:
                        username = st.session_state["login_user"]
                        password = st.session_state["login_pass"]
                        success, message = login_user(username, password)
                        if success:
                            st.toast(message, icon="🎉")
                            st.rerun() 
                        else:
                            st.error(message, icon="❌")

            # --- Register Tab ---
            with register_tab:
                with st.form(key="register_form"):
                    st.text_input("Username", placeholder="Create a new username", key="reg_user")
                    st.text_input("Password", type="password", placeholder="Create a strong password", key="reg_pass")
                    
                    st.markdown("</br>", unsafe_allow_html=True) # Add some spacing

                    register_button = st.form_submit_button(label="Register", use_container_width=True)

                    if register_button:
                        username = st.session_state["reg_user"]
                        password = st.session_state["reg_pass"]
                        success, message = register_user(username, password)
                        if success:
                            st.success(message, icon="✅")
                        else:
                            st.error(message, icon="❌")


# --- Sidebar UI Components ---

def sidebar_session_selector():
    """Manages the chat session selection, renaming, and deletion in the sidebar."""
    st.sidebar.title("💬 My Chats")

    def handle_rename(index):
        new_name = st.session_state[f"rename_input_{index}"]
        if new_name:
            st.session_state.chat_session_names[index] = new_name
            save_user_data_from_session(st.session_state.username)
        st.session_state.editing_chat_index = None

    def handle_delete_chat(index):
        if len(st.session_state.chat_session_names) > 1:
            deleted_name = st.session_state.chat_session_names.pop(index)
            st.session_state.chat_sessions.pop(index)
            st.session_state.chat_pdf_paths.pop(index)
            st.session_state.chat_engines.pop(index)

            if st.session_state.current_chat >= index:
                st.session_state.current_chat = max(0, st.session_state.current_chat - 1)
            
            save_user_data_from_session(st.session_state.username)
            st.session_state.editing_chat_index = None 
            st.toast(f"Chat '{deleted_name}' deleted.", icon="🗑️")
        else:
            st.toast("Cannot delete the last chat.", icon="⚠️")


    for i, name in enumerate(st.session_state.chat_session_names):
        col1, col2, col3 = st.sidebar.columns([0.7, 0.15, 0.15])

        with col1:
            if st.session_state.get("editing_chat_index") == i:
                st.text_input(
                    label="Rename chat",
                    value=name,
                    key=f"rename_input_{i}",
                    on_change=handle_rename,
                    args=(i,),
                    label_visibility="collapsed"
                )
            else:
                button_type = "primary" if st.session_state.current_chat == i and st.session_state.page == "chat" else "secondary"
                if st.button(name, key=f"chat_{i}", use_container_width=True, type=button_type):
                    st.session_state.current_chat = i
                    st.session_state.page = "chat"
                    st.session_state.editing_chat_index = None
                    st.rerun()

        with col2:
            if st.session_state.get("editing_chat_index") == i:
                if st.button("✅", key=f"done_{i}", help="Confirm rename"):
                    st.session_state.editing_chat_index = None
                    st.rerun()
            else:
                if st.button("✏️", key=f"edit_{i}", help="Rename chat"):
                    st.session_state.editing_chat_index = i
                    st.rerun()
        
        with col3:
            if st.session_state.get("editing_chat_index") != i:
                if st.button("🗑️", key=f"delete_{i}", help="Delete chat"):
                    handle_delete_chat(i)
                    st.rerun()

    if st.sidebar.button("➕ New Chat", use_container_width=True):
        st.session_state.chat_sessions.append([])
        st.session_state.chat_session_names.append(f"Chat {len(st.session_state.chat_sessions)}")
        st.session_state.chat_pdf_paths.append([])
        st.session_state.chat_engines.append(ChatEngine(st.session_state.config))
        st.session_state.current_chat = len(st.session_state.chat_sessions) - 1
        st.session_state.page = "chat"
        st.session_state.editing_chat_index = None
        save_user_data_from_session(st.session_state.username)
        st.rerun()


def show_pdf_manager_in_sidebar(state):
    """Renders the PDF uploader and manager in a sidebar expander."""
    idx = state.current_chat
    engine = state.chat_engines[idx]

    with st.sidebar.expander("📄 PDF Management", expanded=False):
        st.subheader("Add PDF to this Chat")
        
        uploaded_file = st.file_uploader("Upload a new PDF", type=["pdf"], key=f"pdf_uploader_{idx}")
        
        if uploaded_file:
            processed_pdf_names = [os.path.basename(p) for p in state.chat_pdf_paths[idx]]
            if uploaded_file.name not in processed_pdf_names:
                with st.spinner(f"Processing '{uploaded_file.name}'..."):
                    handle_pdf_upload(state.username, uploaded_file, idx)
                    save_user_data_from_session(state.username)
                st.success(f"✅ PDF '{uploaded_file.name}' added.")
                st.rerun()

        st.markdown("---")
        st.subheader("Activate & Manage PDFs")

        if state.chat_pdf_paths and state.chat_pdf_paths[idx]:
            pdf_options = [os.path.basename(p) for p in state.chat_pdf_paths[idx]]
            
            active_pdf_index = 0
            if hasattr(engine, 'rag') and engine.rag and engine.rag.pdf_path in state.chat_pdf_paths[idx]:
                active_pdf_index = state.chat_pdf_paths[idx].index(engine.rag.pdf_path)

            selected_pdf_name = st.selectbox("Select a PDF to make it active:", pdf_options, index=active_pdf_index)

            selected_pdf_path = next((p for p in state.chat_pdf_paths[idx] if os.path.basename(p) == selected_pdf_name), None)

            if selected_pdf_path and (not hasattr(engine, 'rag') or not engine.rag or engine.rag.pdf_path != selected_pdf_path):
                with st.spinner(f"Activating '{selected_pdf_name}'..."):
                    ok, msg = engine.attach_pdf(selected_pdf_path)
                    st.toast(f"Activated '{selected_pdf_name}'" if ok else msg, icon="✅" if ok else "❌")
            
            st.markdown("---")
            
            st.write(f"**Selected for deletion:** `{selected_pdf_name}`")
            if st.button("🗑️ Delete this PDF", type="secondary", use_container_width=True, key=f"delete_pdf_{idx}_{selected_pdf_name}"):
                if selected_pdf_path:
                    # Deactivate if it's the current one
                    if hasattr(engine, 'rag') and engine.rag and engine.rag.pdf_path == selected_pdf_path:
                        engine.rag = None
                    
                    # Delete the file and update session state
                    success, message = delete_pdf_for_user(selected_pdf_path)
                    if success:
                        state.chat_pdf_paths[idx].remove(selected_pdf_path)
                        save_user_data_from_session(state.username)
                        st.toast(message, icon="🗑️")
                    else:
                        st.toast(message, icon="❌")
                    
                    st.rerun()
        else:
            st.info("No PDFs have been uploaded for this chat yet.")

def sidebar_navigation():
    """Adds navigation buttons to the sidebar for settings and quiz generator."""
    st.sidebar.markdown("---")
    if st.sidebar.button("💬 Back to Chat", use_container_width=True):
        st.session_state.page = "chat"
        st.rerun()

    if st.sidebar.button("🧠 Quiz Generator", use_container_width=True):
        st.session_state.page = "quiz"
        st.rerun()

    if st.sidebar.button("⚙️ Settings", use_container_width=True):
        st.session_state.page = "settings"
        st.rerun()


# --- Main Page UI ---

def stream_response(response):
    """Yields words from a response string with a delay to simulate typing."""
    for word in response.split():
        yield word + " "
        time.sleep(0.05)

def show_chat_page(state):
    """Renders the main chat interface, including messages and input controls."""
    if state.current_chat >= len(state.chat_engines):
        state.current_chat = 0
    
    chat_index = state.current_chat
    chat_engine = state.chat_engines[chat_index]

    if not state.chat_sessions[chat_index]:
        welcome_message()

    for msg in state.chat_sessions[chat_index]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if user_input := st.chat_input("Type your message here..."):
        state.chat_sessions[chat_index].append({"role": "user", "content": user_input})
        st.rerun()

    if state.chat_sessions[chat_index] and state.chat_sessions[chat_index][-1]["role"] == "user":
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = chat_engine.get_response(state.chat_sessions[chat_index][-1]["content"])
            
            st.write_stream(stream_response(response))
        
        state.chat_sessions[chat_index].append({"role": "assistant", "content": response})
        save_user_data_from_session(state.username)
        
        if state.config.get("elevenlabs_api"):
            speak_text(response, state.config["elevenlabs_api"])
            
        st.rerun()

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if not state.recording:
            if st.button("🎙️ Start Recording", use_container_width=True):
                state.recording = True
                start_recording()
                st.toast("Recording started... Speak now!")
                st.rerun()
        else:
            if st.button("⏹️ Stop Recording", use_container_width=True, type="primary"):
                audio_path = stop_recording()
                state.recording = False
                
                with st.spinner("Transcribing audio..."):
                    transcription = transcribe_audio(audio_path, state.config["whisper_model"])
                
                if transcription:
                    state.chat_sessions[chat_index].append({"role": "user", "content": transcription})
                    st.rerun()
                else:
                    st.warning("Could not transcribe audio. Please try again.")
                
                st.rerun()

# --- Settings and Quiz Page UI ---

def show_settings_page(state):
    """Renders the global application settings on a dedicated page."""
    st.title("⚙️ Application Settings")

    with st.container(border=True):
        st.header("System Prompt")
        state.config["system_prompt"] = st.text_area(
            "This prompt guides the AI's personality and responses.", 
            value=state.config.get("system_prompt", ""), 
            height=150,
            key="system_prompt_settings"
        )
    
    with st.container(border=True):
        st.header("Whisper Model")
        whisper_models = ["tiny", "base", "small", "medium", "large"]
        current_whisper_model = state.config.get("whisper_model", "tiny")
        if current_whisper_model not in whisper_models:
            current_whisper_model = "tiny"
        
        state.config["whisper_model"] = st.selectbox(
            "Select the model size for audio transcription. Larger models are more accurate but slower.",
            whisper_models,
            index=whisper_models.index(current_whisper_model),
            key="whisper_model_settings"
        )
    
    with st.container(border=True):
        st.header("ElevenLabs API Key")
        state.config["elevenlabs_api"] = st.text_input(
            "Enter your API key for text-to-speech functionality.", 
            value=state.config.get("elevenlabs_api", ""), 
            type="password",
            key="elevenlabs_api_settings"
        )

    if st.button("💾 Save Settings", use_container_width=True, type="primary"):
        save_config(state.config)
        st.success("✅ Settings saved successfully.")
        st.toast("Settings have been updated!")


def show_quiz_page(state):
    """Renders the quiz generation page and handles quiz logic."""
    st.title("🧠 Quiz Generator")
    st.markdown("Create a quiz from a topic or a PDF document.")

    # --- State Cleanup ---
    if 'page' in st.session_state and st.session_state.page != 'quiz':
        keys_to_clear = ['quiz_data', 'user_answers', 'show_score']
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
    
    # --- Quiz Configuration ---
    if not st.session_state.get('quiz_data'):
        with st.container(border=True):
            st.subheader("1. Configure Your Quiz")
            
            source_type = st.radio("Quiz Source:", ("Topic", "PDF"), horizontal=True, key="quiz_source")
            
            col1, col2 = st.columns(2)
            with col1:
                difficulty = st.select_slider("Difficulty:", ("Easy", "Medium", "Hard"), value="Medium", key="quiz_difficulty")
            with col2:
                num_questions = st.number_input("Number of Questions:", min_value=3, max_value=15, value=5, key="quiz_num_questions")

            source_input_valid = False
            if source_type == "Topic":
                topic = st.text_input("Enter quiz topic:", placeholder="e.g., 'The History of Space Exploration'")
                if topic:
                    source_input_valid = True
            else: # PDF
                current_chat_pdfs = state.chat_pdf_paths[state.current_chat]
                if not current_chat_pdfs:
                    st.warning("No PDFs in this chat. Please upload one via the sidebar.", icon="⚠️")
                else:
                    pdf_options = {os.path.basename(p): p for p in current_chat_pdfs}
                    selected_pdf_name = st.selectbox("Select a PDF:", options=list(pdf_options.keys()))
                    pdf_path = pdf_options.get(selected_pdf_name)
                    if pdf_path:
                        source_input_valid = True
            
            if st.button("✨ Generate Quiz", use_container_width=True, type="primary", disabled=not source_input_valid):
                generator = QuizGenerator(state.config)
                with st.spinner("Generating your quiz... This may take a moment."):
                    if source_type == "Topic":
                        response = generator.generate_from_topic(topic, difficulty, num_questions)
                    else: # PDF
                        response = generator.generate_from_pdf(pdf_path, difficulty, num_questions)

                # Process and store quiz data
                try:
                    cleaned_str = response.strip().lstrip("```json").rstrip("```").strip()
                    quiz_data = json.loads(cleaned_str)
                    if quiz_data and all('question' in q for q in quiz_data):
                        st.session_state.quiz_data = quiz_data
                        st.rerun()
                    else:
                        st.error("The AI returned an invalid quiz format. Please try again.", icon="🚨")
                except (json.JSONDecodeError, TypeError):
                    st.error("Failed to parse the quiz from the AI's response.", icon="🚨")
                    st.code(response)


    # --- Quiz Taking ---
    if st.session_state.get('quiz_data') and not st.session_state.get('show_score'):
        with st.container(border=True):
            st.subheader("2. Take the Quiz")
            with st.form("quiz_form"):
                user_answers = []
                for i, q in enumerate(st.session_state.quiz_data):
                    st.markdown(f"**Question {i+1}: {q['question']}**")
                    options = q.get('options', [])
                    if q['answer'] not in options:
                        options.append(q['answer'])
                    
                    user_choice = st.radio("Options:", options, key=f"q_{i}", label_visibility="collapsed")
                    user_answers.append(user_choice)
                
                if st.form_submit_button("Submit Answers", use_container_width=True, type="primary"):
                    st.session_state.user_answers = user_answers
                    st.session_state.show_score = True
                    st.rerun()

    # --- Score and Results ---
    if st.session_state.get('show_score'):
        with st.container(border=True):
            st.subheader("3. Your Results")
            
            quiz_data = st.session_state.quiz_data
            user_answers = st.session_state.user_answers
            score = sum(1 for i, u_ans in enumerate(user_answers) if u_ans == quiz_data[i]['answer'])

            st.metric(label="Your Score", value=f"{score}/{len(quiz_data)}", delta=f"{score/len(quiz_data)*100:.1f}%")

            with st.expander("📝 Review Your Answers", expanded=False):
                for i, q in enumerate(quiz_data):
                    user_ans = user_answers[i]
                    correct_ans = q['answer']
                    
                    if user_ans == correct_ans:
                        st.success(f"**Q{i+1}: Correct!** {q['question']}", icon="✅")
                    else:
                        st.error(f"**Q{i+1}: Incorrect!** {q['question']}", icon="❌")
                        st.info(f"Your answer: `{user_ans}` | Correct answer: `{correct_ans}`")
            
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("↻ Retry Quiz", use_container_width=True):
                    keys_to_clear = ['user_answers', 'show_score']
                    for key in keys_to_clear:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()
            with col2:
                if st.button("🎉 Create New Quiz", use_container_width=True, type="primary"):
                    keys_to_clear = ['quiz_data', 'user_answers', 'show_score']
                    for key in keys_to_clear:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()
            
            with col3:
                pdf_data = create_quiz_pdf(st.session_state.quiz_data)
                st.download_button(
                    label="📄 Download PDF",
                    data=pdf_data,
                    file_name="quiz_with_answers.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )


def welcome_message():
    """Displays a welcome message in the main chat area."""
    st.markdown("## 👋 Welcome to Dialogix!")
    st.markdown("Start a conversation by typing below, or upload a PDF in the sidebar to chat with your document.")