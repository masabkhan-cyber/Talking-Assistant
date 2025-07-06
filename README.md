# 🤖 Dialogix: Your AI-Powered Learning Assistant

<p align="center">
  <img src="https://raw.githubusercontent.com/masabkhan-cyber/Dialogix/master/assets/screenshot.png" alt="Dialogix Screenshot" width="800">
  <br/>
  <em>A modern, multi-user e-learning platform built with Streamlit that leverages Retrieval-Augmented Generation (RAG) to chat with documents, generate quizzes, and provide voice-enabled interaction.</em>
</p>

---

## ✨ Key Features

Dialogix combines several powerful AI features into a single, user-friendly web interface:

* **Secure User Authentication**: A modern login and registration system to manage user-specific chats and documents.
* **Conversational AI Chat**: Engage in dynamic conversations with an AI assistant powered by Meta AI.
* **Chat with Your Documents**: Upload PDF files and ask questions directly about their content using a sophisticated RAG pipeline with LangChain and FAISS.
* **AI-Powered Quiz Generation**: Instantly create quizzes from either uploaded PDF documents or any user-provided topic, with adjustable difficulty levels (Easy, Medium, Hard).
* **Voice Interaction**: Use your voice to ask questions with real-time transcription (via Whisper) and hear the AI's responses spoken back to you (via ElevenLabs).
* **Export & Print Quizzes**: Download generated quizzes and their answer keys as a print-friendly, two-page PDF document.
* **Modern, Customizable UI**: A visually appealing interface built with Streamlit, featuring a custom background and a clean, tab-based design.

---

## 🛠️ Technology Stack

This project integrates a range of modern technologies to deliver its features:

* **Backend & Frontend**: Python, Streamlit
* **LLM & Chat Logic**: `meta_ai_api`
* **Document Intelligence (RAG)**: LangChain, FAISS, PyPDF2
* **Speech-to-Text**: `faster-whisper`
* **Text-to-Speech**: `elevenlabs`
* **PDF Generation**: `fpdf2`
* **Packaging**: PyInstaller, Inno Setup

---

## 🚀 Getting Started

Follow these instructions to set up and run Dialogix on your local machine.

### Prerequisites

* Python 3.10 or higher
* `git` for cloning the repository

### Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/masabkhan-cyber/Dialogix.git](https://github.com/masabkhan-cyber/Dialogix.git)
    cd Dialogix
    ```

2.  **Install all dependencies:**
    Make sure you have the master `requirements.txt` file from the project. Then, run:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure API Keys:**
    * The first time you run the app, a `config.json` file will be created.
    * Open `config.json` and add your ElevenLabs API key if you wish to use the text-to-speech feature.
    ```json
    {
        "system_prompt": "Your name is Sophia...",
        "whisper_model": "tiny",
        "elevenlabs_api": "YOUR_ELEVENLABS_API_KEY_HERE"
    }
    ```

### Running the Application

To launch the Dialogix web interface, run the following command in your terminal:
```bash
streamlit run app.py
