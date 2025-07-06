import json
import os
import shutil
import streamlit as st
from chat_engine import ChatEngine

# --- Constants ---
CHATS_FILE = "user_chats.json"
UPLOADS_DIR = "user_uploads"

# --- Helper Functions ---

def get_default_user_data():
    """Returns the default data structure for a new user."""
    return {
        "chat_sessions": [[]],
        "chat_session_names": ["New Chat"],
        "chat_pdf_paths": [[]],
    }

# --- Main Data Functions ---

def load_all_user_data():
    """Loads all user chat data from the main JSON file."""
    if not os.path.exists(CHATS_FILE):
        return {}
    try:
        with open(CHATS_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_all_user_data(all_data):
    """Saves all user chat data to the main JSON file."""
    with open(CHATS_FILE, 'w') as f:
        json.dump(all_data, f, indent=4)

def load_user_data_into_session(username):
    """Loads a specific user's data into the Streamlit session state."""
    all_data = load_all_user_data()
    user_data = all_data.get(username, get_default_user_data())

    st.session_state.chat_sessions = user_data.get("chat_sessions", [[]])
    st.session_state.chat_session_names = user_data.get("chat_session_names", ["New Chat"])
    st.session_state.chat_pdf_paths = user_data.get("chat_pdf_paths", [[]])

    num_sessions = len(st.session_state.chat_sessions)
    st.session_state.chat_session_names.extend(["New Chat"] * (num_sessions - len(st.session_state.chat_session_names)))
    st.session_state.chat_pdf_paths.extend([[]] * (num_sessions - len(st.session_state.chat_pdf_paths)))

    st.session_state.chat_engines = []
    for pdf_list in st.session_state.chat_pdf_paths:
        engine = ChatEngine(st.session_state.config)
        if pdf_list and os.path.exists(pdf_list[0]):
            engine.attach_pdf(pdf_list[0])
        st.session_state.chat_engines.append(engine)
    
    if not st.session_state.chat_engines:
        st.session_state.chat_sessions = [[]]
        st.session_state.chat_session_names = ["New Chat"]
        st.session_state.chat_pdf_paths = [[]]
        st.session_state.chat_engines.append(ChatEngine(st.session_state.config))

    st.session_state.current_chat = 0

def save_user_data_from_session(username):
    """Saves the current user's session data to the main JSON file."""
    if not username:
        return

    all_data = load_all_user_data()
    all_data[username] = {
        "chat_sessions": st.session_state.get("chat_sessions", [[]]),
        "chat_session_names": st.session_state.get("chat_session_names", ["New Chat"]),
        "chat_pdf_paths": st.session_state.get("chat_pdf_paths", [[]]),
    }
    save_all_user_data(all_data)

def handle_pdf_upload(username, uploaded_file, chat_index):
    """Saves an uploaded PDF to a user-specific directory and returns its path."""
    user_dir = os.path.join(UPLOADS_DIR, username)
    os.makedirs(user_dir, exist_ok=True)
    
    file_path = os.path.join(user_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    if file_path not in st.session_state.chat_pdf_paths[chat_index]:
        st.session_state.chat_pdf_paths[chat_index].append(file_path)
    
    return file_path

def delete_pdf_for_user(pdf_path_to_delete):
    """Deletes a specific PDF file from the filesystem."""
    if pdf_path_to_delete is None:
        return False, "Invalid PDF path."

    try:
        if os.path.exists(pdf_path_to_delete):
            os.remove(pdf_path_to_delete)
            return True, f"Successfully deleted '{os.path.basename(pdf_path_to_delete)}'."
        else:
            return False, "File not found."
    except Exception as e:
        return False, f"Error deleting file: {e}"
