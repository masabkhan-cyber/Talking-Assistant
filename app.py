import streamlit as st
from config import load_config
from ui import (
    show_login_form, 
    sidebar_session_selector, 
    show_pdf_manager_in_sidebar,
    sidebar_navigation,
    show_settings_page,
    show_chat_page,
    show_quiz_page # Import the new quiz page function
)
from user_data import save_user_data_from_session, load_user_data_into_session

# --- Page Configuration ---
# Set the page title and icon. This is the official way to name your Streamlit app.
st.set_page_config(page_title="Dialogix", page_icon="🤖")

# --- Session State Initialization ---
def initialize_session_state():
    """Initializes the basic session state variables if they don't exist."""
    if "config" not in st.session_state:
        st.session_state.config = load_config()
    if "recording" not in st.session_state:
        st.session_state.recording = False
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = None
    if "page" not in st.session_state:
        st.session_state.page = "chat"

# --- Main Application Logic ---
initialize_session_state()

# If the user is not logged in, show the login/registration form.
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>Welcome to Dialogix 🤖</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Your intelligent E Learning chat companion.</p>", unsafe_allow_html=True)
    show_login_form()

# If the user is logged in, show the main application.
else:
    # Load user-specific data if it's not already in the session.
    if 'chat_sessions' not in st.session_state:
        load_user_data_into_session(st.session_state.username)

    # --- Sidebar ---
    st.sidebar.title("Dialogix")
    st.sidebar.markdown(f"Welcome, **{st.session_state.username}**!")
    
    sidebar_session_selector()
    show_pdf_manager_in_sidebar(st.session_state)
    sidebar_navigation()

    if st.sidebar.button("Logout", use_container_width=True):
        save_user_data_from_session(st.session_state.username)
        # Clear the session state upon logout
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        initialize_session_state()
        st.rerun()

    # --- Page Routing ---
    if st.session_state.page == "settings":
        show_settings_page(st.session_state)
    
    elif st.session_state.page == "quiz":
        # Add routing for the new quiz page
        show_quiz_page(st.session_state)

    elif st.session_state.page == "chat":
        # All chat page logic is now handled by this function from ui.py
        show_chat_page(st.session_state)