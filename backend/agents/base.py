import os
import requests
from datetime import datetime
from tinydb import TinyDB, Query
import pyttsx3
import whisper  # Standard import for openai-whisper package

db = TinyDB(os.path.join(os.path.dirname(__file__), "../../memory/memory_store.json"))
Topic = Query()

# Initialize Whisper and pyttsx3 once at the start
whisper_model = whisper.load_model("base")
tts_engine = pyttsx3.init()


def call_llm(prompt: str) -> str:
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": "llama3", "prompt": prompt, "stream": False}
    )
    return response.json()["response"].strip()


def log_agent_response(topic: str, agent: str, content: str):
    entry = {
        "agent": agent,
        "content": content,
        "timestamp": datetime.utcnow().isoformat()
    }
    if db.contains(Topic.name == topic):
        db.update(lambda t: t["log"].append(entry), Topic.name == topic)
    else:
        db.insert({"name": topic, "log": [entry]})

    # Also create a spoken audio log of the response
    log_audio_response(topic, agent, content)


def log_audio_response(topic: str, agent: str, content: str):
    """Saves the agent's text response as an audio file."""
    timestamp = datetime.utcnow().isoformat().replace(':', '_').replace('.', '_')
    audio_dir = os.path.join(os.path.dirname(__file__), f"../audio_logs/{topic}")
    os.makedirs(audio_dir, exist_ok=True)
    audio_path = os.path.join(audio_dir, f"agent_{agent}_{timestamp}.wav")

    # Configure TTS settings for better quality
    tts_engine.setProperty('rate', 150)  # Speed of speech
    tts_engine.setProperty('volume', 0.8)  # Volume level

    tts_engine.save_to_file(content, audio_path)
    tts_engine.runAndWait()
    return audio_path


def get_topic_log(topic: str):
    result = db.search(Topic.name == topic)
    return result[0]["log"] if result else []


def transcribe_audio(audio_path: str) -> str:
    """Transcribes an audio file using the Whisper model."""
    result = whisper_model.transcribe(audio_path)
    return result["text"]


def generate_audio_response(text: str) -> str:
    """Generates an audio file from text and returns the file path."""
    timestamp = datetime.utcnow().isoformat().replace(':', '_').replace('.', '_')
    audio_path = f"temp_response_{timestamp}.wav"

    # Configure TTS settings
    tts_engine.setProperty('rate', 150)  # Speed of speech
    tts_engine.setProperty('volume', 0.8)  # Volume level

    tts_engine.save_to_file(text, audio_path)
    tts_engine.runAndWait()
    return audio_path


def read_log_aloud(topic: str, agent_filter: str = None) -> str:
    """Generate audio file reading all logs for a topic."""
    logs = get_topic_log(topic)
    if not logs:
        speech_text = f"No logs found for topic {topic}"
    else:
        # Filter by agent if specified
        if agent_filter:
            logs = [log for log in logs if log.get('agent', '').lower() == agent_filter.lower()]

        if not logs:
            speech_text = f"No logs found for agent {agent_filter} in topic {topic}"
        else:
            speech_parts = [f"Reading logs for topic {topic}."]

            for i, log in enumerate(logs, 1):
                agent = log.get('agent', 'Unknown')
                content = log.get('content', 'No content')
                timestamp = log.get('timestamp', '')

                # Parse timestamp for speaking
                try:
                    dt_object = datetime.fromisoformat(timestamp)
                    time_str = dt_object.strftime('%B %d at %I:%M %p')
                except:
                    time_str = 'unknown time'

                speech_parts.append(f"Log {i}. Agent {agent} on {time_str} said: {content}")

            speech_text = " ".join(speech_parts)

    return generate_audio_response(speech_text)