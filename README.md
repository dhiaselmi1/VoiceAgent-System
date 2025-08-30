# Voice-Controlled Agent System 🗣️🤖

A sophisticated voice-controlled multi-agent system that enables natural language interaction with specialized AI agents through speech-to-text and text-to-speech capabilities.

## Project Description

This project provides a comprehensive solution for monitoring and understanding AI agent workflows. It features a **Streamlit** frontend 🖥️ for user interaction and a **FastAPI** backend that manages the core agent logic. The application captures and timestamps all agent outputs, presenting them in a clear, chronological timeline. It leverages the **Llama 3** model to power multiple specialized AI agents that collaborate to complete tasks. Users can run these agents and observe their collaboration in real-time, making it an ideal tool for debugging and analyzing multi-agent systems.

## Features ✨

* **Voice Input** 🎙️: Record voice commands using speech-to-text (**Whisper**).
* **Multi-Agent System** 🤝: Four specialized agents with distinct roles.
* **Voice Output** 🔊: Text-to-speech responses for all agent interactions.
* **Persistent Memory** 🧠: Conversation history stored with audio logs.
* **Web Interface** 🌐: Intuitive **Streamlit** frontend.
* **REST API** 🚀: **FastAPI** backend with comprehensive endpoints.
* **Export Functionality** 📄: PDF reports of agent conversations.

## Architecture 🏗️
VoiceAgent-System/
├── backend/
│   ├── main.py              # FastAPI server
│   ├── agents/
│   │   ├── init.py
│   │   ├── base.py          # Core agent functionality
│   │   ├── devil_agent.py   # Critical analysis agent
│   │   ├── insight_agent.py # Pattern recognition agent
│   │   ├── research_agent.py# Information gathering agent
│   │   └── summarizer_agent.py # Content summarization agent
│   ├── memory/
│   │   └── memory_store.json # Persistent conversation storage
│   └── audio_logs/          # Generated audio files
├── frontend/
│   └── app.py              # Streamlit web interface
└── venv/                   # Python virtual environment
## Agents 🧑‍💼

* **Research Agent** 🔬: Gathers and analyzes information on specified topics with targeted queries.
* **Devil Agent** 😈: Provides critical analysis and challenges assumptions to strengthen arguments.
* **Insight Agent** 💡: Identifies patterns, connections, and deeper meanings within discussions.
* **Summarizer Agent** 📝: Condenses conversations and extracts key points for clarity.

## Installation ⚙️

### Prerequisites

* Python 3.8+
* Virtual environment (recommended)
* Ollama with `llama3` model (for local LLM)
* `wkhtmltopdf` (optional, for PDF export)

### Setup

1.  **Clone the repository**
    ```bash
    git clone [https://github.com/yourusername/VoiceAgent-System.git](https://github.com/yourusername/VoiceAgent-System.git)
    cd VoiceAgent-System
    ```
2.  **Create virtual environment**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Install Ollama and `llama3`**
    ```bash
    # Install Ollama from [https://ollama.ai](https://ollama.ai)
    ollama pull llama3
    ```
5.  **Optional: Install `wkhtmltopdf` for PDF export**
    * **Windows**: Download from [https://wkhtmltopdf.org/downloads.html](https://wkhtmltopdf.org/downloads.html)
    * **macOS**: `brew install wkhtmltopdf`
    * **Linux**: `sudo apt-get install wkhtmltopdf`

### `requirements.txt` file

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
streamlit==1.28.1
streamlit-mic-recorder==0.0.5
openai-whisper==20250625
pyttsx3==2.90
tinydb==4.8.0
requests==2.31.0
python-multipart==0.0.6
pdfkit==1.0.0
torch==2.1.0
torchaudio==2.1.0
