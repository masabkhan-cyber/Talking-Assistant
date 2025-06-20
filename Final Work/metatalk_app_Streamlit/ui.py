import os
import time
import streamlit as st
from chat_engine import ChatEngine
from auth import login_user, register_user
from user_data import handle_pdf_upload, save_user_data_from_session, delete_pdf_for_user
from config import save_config
from voice import speak_text, start_recording, stop_recording, transcribe_audio

# --- Authentication UI ---
def show_login_form():
    """Displays the login and registration forms in a more centered and modern layout."""
    st.title("🤖 Welcome to MetaTalk")
    st.markdown("Please log in or register to continue.")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        choice = st.radio("Choose an action:", ["Login", "Register"], horizontal=True, label_visibility="collapsed")

        with st.form(key=f"{choice}_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit_button = st.form_submit_button(label=choice, use_container_width=True)

            if submit_button:
                if choice == "Login":
                    success, message = login_user(username, password)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                elif choice == "Register":
                    success, message = register_user(username, password)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)

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
    """Adds a settings navigation button to the sidebar."""
    st.sidebar.markdown("---")
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

def show_settings_page(state):
    """Renders the global application settings on a dedicated page."""
    st.title("⚙️ Application Settings")

    if st.button("⬅️ Back to Chat"):
        st.session_state.page = "chat"
        st.rerun()

    st.header("System Prompt")
    state.config["system_prompt"] = st.text_area(
        "This prompt guides the AI's personality and responses.", 
        value=state.config.get("system_prompt", ""), 
        height=150,
        key="system_prompt_settings"
    )
    
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

def welcome_message():
    """Displays a welcome message in the main chat area."""
    st.markdown("## 👋 Welcome to MetaTalk!")
    st.markdown("Start a conversation by typing below, or upload a PDF in the sidebar to chat with your document.")
