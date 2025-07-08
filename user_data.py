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
        "archived_sessions": [], 
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
    st.session_state.archived_sessions = user_data.get("archived_sessions", [])

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
        "archived_sessions": st.session_state.get("archived_sessions", []),
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

def create_new_chat_session(username):
    """Appends a new, empty chat session to the session state and saves."""
    st.session_state.chat_sessions.append([])
    new_chat_name = f"Chat {len(st.session_state.chat_sessions) + 1}"
    st.session_state.chat_session_names.append(new_chat_name)
    st.session_state.chat_pdf_paths.append([])
    st.session_state.chat_engines.append(ChatEngine(st.session_state.config))
    st.session_state.current_chat = len(st.session_state.chat_sessions) - 1
    save_user_data_from_session(username)

def delete_chat_session(username, chat_index):
    """Deletes a chat session, its associated PDF files, and updates session state."""
    if not (0 <= chat_index < len(st.session_state.chat_pdf_paths)):
        return

    pdfs_to_delete = st.session_state.chat_pdf_paths[chat_index]
    for pdf_path in pdfs_to_delete:
        if os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
            except OSError as e:
                print(f"Error deleting file {pdf_path}: {e}")

    st.session_state.chat_sessions.pop(chat_index)
    st.session_state.chat_session_names.pop(chat_index)
    st.session_state.chat_pdf_paths.pop(chat_index)
    st.session_state.chat_engines.pop(chat_index)
    
    save_user_data_from_session(username)

def archive_chat_session(username, chat_index):
    """Moves a chat from the active list to the archive list."""
    if not (0 <= chat_index < len(st.session_state.chat_session_names)):
        return
        
    archived_chat = {
        "session": st.session_state.chat_sessions[chat_index],
        "name": st.session_state.chat_session_names[chat_index],
        "pdfs": st.session_state.chat_pdf_paths[chat_index],
    }
    
    if "archived_sessions" not in st.session_state:
        st.session_state.archived_sessions = []
    st.session_state.archived_sessions.append(archived_chat)
    
    st.session_state.chat_sessions.pop(chat_index)
    st.session_state.chat_session_names.pop(chat_index)
    st.session_state.chat_pdf_paths.pop(chat_index)
    st.session_state.chat_engines.pop(chat_index)
    
    save_user_data_from_session(username)

def restore_chat_session(username, archive_index):
    """Moves a chat from the archive back to the active list."""
    if not (0 <= archive_index < len(st.session_state.archived_sessions)):
        return

    # Pop the archived chat from the list
    restored_chat = st.session_state.archived_sessions.pop(archive_index)
    
    # Append its data to the active session lists
    st.session_state.chat_sessions.append(restored_chat["session"])
    st.session_state.chat_session_names.append(restored_chat["name"])
    st.session_state.chat_pdf_paths.append(restored_chat["pdfs"])
    
    # Re-create the chat engine for the restored chat
    engine = ChatEngine(st.session_state.config)
    if restored_chat["pdfs"] and os.path.exists(restored_chat["pdfs"][0]):
        engine.attach_pdf(restored_chat["pdfs"][0])
    st.session_state.chat_engines.append(engine)

    # Set the restored chat as the current one
    st.session_state.current_chat = len(st.session_state.chat_sessions) - 1
    
    # Save the changes
    save_user_data_from_session(username)