import json
import hashlib
import os
import streamlit as st

# --- Constants ---
USERS_FILE = "users.json"

# --- Password Hashing and Verification ---

def hash_password(password):
    """Hashes a password with a salt using PBKDF2."""
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    # Store salt and key as hex strings
    return salt.hex() + key.hex()

def verify_password(stored_password_hash, provided_password):
    """Verifies a stored password hash against the one provided by the user."""
    try:
        # Extract salt and key from the stored hash
        salt = bytes.fromhex(stored_password_hash[:64])
        stored_key = bytes.fromhex(stored_password_hash[64:])
        # Hash the provided password with the same salt
        new_key = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
        # Compare the hashes
        return new_key == stored_key
    except (ValueError, TypeError):
        # Handle cases with incorrect hash format or empty passwords
        return False

# --- User Data Management ---

def load_users():
    """Loads the user data from the JSON file."""
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            # If the file is corrupted or empty, return an empty dict
            return {}

def save_users(users):
    """Saves the user data to the JSON file."""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

# --- Authentication Functions ---

def register_user(username, password):
    """Registers a new user if the username is not taken."""
    if not username or not password:
        return False, "Username and password cannot be empty."
    
    users = load_users()
    if username in users:
        return False, "Username already exists. Please choose another one."
    
    users[username] = {"password": hash_password(password)}
    save_users(users)
    return True, "Registration successful! You can now log in."

def login_user(username, password):
    """Logs in a user by verifying their credentials."""
    if not username or not password:
        return False, "Username and password cannot be empty."

    users = load_users()
    user_data = users.get(username)
    
    if user_data and verify_password(user_data["password"], password):
        st.session_state.logged_in = True
        st.session_state.username = username
        return True, "Login successful!"
    
    return False, "Invalid username or password."
