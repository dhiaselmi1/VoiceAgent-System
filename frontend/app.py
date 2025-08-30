import streamlit as st
import requests
import io
from datetime import datetime
from collections import defaultdict
import pdfkit
import os
from streamlit_mic_recorder import mic_recorder
import tempfile
import time

st.set_page_config(page_title="Voice-Controlled Agent System", layout="wide")

# --- Configuration ---
FASTAPI_URL = "http://localhost:8000"
API_URL = "http://localhost:8000"

# Configuration for PDF export only
# Attempt to find wkhtmltopdf in system's PATH
try:
    path_wkhtmltopdf = pdfkit.configuration().wkhtmltopdf
    config_pdf = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
    PDF_AVAILABLE = True
except OSError:
    # If not found, try a common Windows path as a fallback
    path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
    if os.path.exists(path_wkhtmltopdf):
        config_pdf = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
        PDF_AVAILABLE = True
    else:
        PDF_AVAILABLE = False
        st.sidebar.warning("⚠️ PDF export not available. Install wkhtmltopdf for PDF export functionality.")

# Visual settings for each agent
AGENT_VISUALS = {
    "Research": {"icon": "🔬", "color": "#4CAF50"},
    "Summarizer": {"icon": "📝", "color": "#2196F3"},
    "Insight": {"icon": "💡", "color": "#FFC107"},
    "Devil": {"icon": "😈", "color": "#F44336"},
    "default": {"icon": "🤖", "color": "#9E9E9E"}
}


# --- Helper Functions ---
@st.cache_data(ttl=30)  # Cache logs for 30 seconds
def fetch_logs(topic):
    """Fetches and returns logs for a given topic."""
    try:
        response = requests.get(f"{API_URL}/logs/{topic}")
        if response.status_code == 404:
            return []  # No logs found, return empty list
        response.raise_for_status()
        return response.json().get("logs", [])
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to connect to the API: {e}")
        return None
    except Exception as e:
        st.error(f"An error occurred while fetching logs: {e}")
        return None


def text_to_speech(text: str):
    """Send text to backend for TTS conversion and return audio."""
    try:
        response = requests.post(f"{API_URL}/tts", json={"text": text})
        response.raise_for_status()
        return response.content
    except Exception as e:
        st.error(f"Error generating speech: {e}")
        return None


def read_logs_aloud(topic: str, agent_filter: str = None):
    """Get audio of logs read aloud."""
    try:
        params = {}
        if agent_filter:
            params["agent_filter"] = agent_filter
        response = requests.get(f"{API_URL}/read-logs/{topic}", params=params)
        response.raise_for_status()
        return response.content
    except Exception as e:
        st.error(f"Error reading logs aloud: {e}")
        return None


def check_api_status():
    """Check if the FastAPI backend is running."""
    try:
        response = requests.get(f"{API_URL}/", timeout=5)
        return response.status_code == 200
    except:
        return False
    """Check if the FastAPI backend is running."""
    try:
        response = requests.get(f"{API_URL}/", timeout=5)
        return response.status_code == 200
    except:
        return False


def generate_html_report(logs_data, topic):
    """Generates an HTML string from the logs for reporting."""
    html = f"<html><head><title>Agent Collaboration Report: {topic}</title>"
    html += """
    <style>
        body { font-family: sans-serif; margin: 20px; }
        .log-container { border-left: 4px solid; padding: 15px; margin-bottom: 15px; background-color: #f9f9f9; border-radius: 5px; }
        .agent { font-weight: bold; font-size: 1.2em; color: #333; }
        .timestamp { color: #666; font-size: 0.9em; margin-top: 5px; }
        .content { margin-top: 10px; line-height: 1.6; }
        h1, h2 { color: #333; }
        h1 { border-bottom: 2px solid #333; padding-bottom: 10px; }
        .summary { background-color: #e8f4fd; padding: 10px; border-radius: 5px; margin-bottom: 20px; }
    </style>
    </head><body>"""
    html += f"<h1>🤖 Voice-Controlled Agent System Report</h1>"
    html += f"<div class='summary'><h2>Topic: {topic}</h2>"
    html += f"<p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>"
    html += f"<p>Total interactions: {len(logs_data)}</p></div>"

    for log in logs_data:
        agent_name = log.get('agent', 'Unknown')
        visuals = AGENT_VISUALS.get(agent_name, AGENT_VISUALS["default"])
        color = visuals['color']
        icon = visuals['icon']

        try:
            dt_object = datetime.fromisoformat(log['timestamp'])
            formatted_time = dt_object.strftime('%Y-%m-%d %H:%M:%S')
        except:
            formatted_time = log.get('timestamp', 'Unknown time')

        html += f'<div class="log-container" style="border-left-color: {color};">'
        html += f'<div class="agent">{icon} {agent_name}</div>'
        html += f'<div class="timestamp">🕒 {formatted_time}</div>'
        html += f'<div class="content">{log.get("content", "No content")}</div>'
        html += '</div>'

    html += "</body></html>"
    return html


# --- Main Application ---
st.title("🤖 Voice-Controlled Agent System")

# Check API status
if not check_api_status():
    st.error("❌ FastAPI backend is not running! Please start the backend server first.")
    st.code("cd backend\nuvicorn main:app --reload --port 8000")
    st.stop()
else:
    st.success("✅ Connected to FastAPI backend")

# --- Sidebar ---
st.sidebar.title("⚙️ Controls")

# Topic input
topic = st.sidebar.text_input("Topic", value="IA", help="Enter the topic for agent discussion")

# Main Content Area - Topic Header
st.subheader(f"📜 Timeline for topic: **{topic}**")

# Add TTS controls
col1, col2, col3 = st.columns([2, 2, 2])
with col1:
    if st.button("🔊 Read All Logs Aloud"):
        with st.spinner("Generating audio for all logs..."):
            audio_data = read_logs_aloud(topic)
            if audio_data:
                st.audio(audio_data, format="audio/wav")
                st.success("✅ All logs audio generated!")

with col2:
    selected_agent_for_tts = st.selectbox(
        "Agent to read:",
        ["All"] + list(AGENT_VISUALS.keys())[:-1],
        key="tts_agent_select"
    )

with col3:
    if st.button(f"🔊 Read {selected_agent_for_tts} Logs"):
        agent_filter = None if selected_agent_for_tts == "All" else selected_agent_for_tts
        with st.spinner(f"Generating audio for {selected_agent_for_tts} logs..."):
            audio_data = read_logs_aloud(topic, agent_filter)
            if audio_data:
                st.audio(audio_data, format="audio/wav")
                st.success(f"✅ {selected_agent_for_tts} logs audio generated!")

st.markdown("---")

# Agent selection
agent_choice = st.sidebar.selectbox(
    "Choose an Agent",
    list(AGENT_VISUALS.keys())[:-1],  # Exclude default
    help="Select which agent to run"
)

# Show agent info
if agent_choice in AGENT_VISUALS:
    visuals = AGENT_VISUALS[agent_choice]
    st.sidebar.markdown(f"**Selected Agent:** {visuals['icon']} {agent_choice}")

st.sidebar.markdown("---")

# Research query (only for Research agent)
query = ""
if agent_choice == "Research":
    query = st.sidebar.text_input("Research Query", help="Required for Research agent")

# Text-based interaction
st.sidebar.subheader("📝 Text Input")
if st.sidebar.button("Run Agent (Text)", type="primary"):
    if agent_choice == "Research" and not query:
        st.sidebar.error("❌ Research agent requires a query.")
    else:
        with st.spinner(f"Running {agent_choice} agent..."):
            payload = {"topic": topic}
            if agent_choice == "Research" and query:
                payload["query"] = query

            try:
                response = requests.post(f"{FASTAPI_URL}/run/{agent_choice}", json=payload)
                response.raise_for_status()
                result = response.json()
                st.sidebar.success(f"✅ {agent_choice} agent completed!")
                # Clear cache to refresh logs
                st.cache_data.clear()
                # Force rerun to show new logs
                st.rerun()
            except requests.exceptions.RequestException as e:
                st.sidebar.error(f"❌ Error running {agent_choice}: {e}")

st.sidebar.markdown("---")

# Voice-based interaction
st.sidebar.subheader("🎙️ Voice Input")
st.sidebar.markdown("Click the microphone to record your message.")

# Voice recorder
audio = mic_recorder(
    start_prompt="🎤 Start Recording",
    stop_prompt="⏹️ Stop Recording",
    key="voice_recorder",
    format="wav"
)

if audio:
    st.sidebar.info("🔄 Processing voice command...")

    with st.spinner(f"Processing voice command for {agent_choice} agent..."):
        try:
            # Create a temporary file for the audio
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                tmp_file.write(audio['bytes'])
                tmp_file_path = tmp_file.name

            # Prepare the request
            with open(tmp_file_path, 'rb') as audio_file:
                files = {'audio_file': ("voice_command.wav", audio_file, "audio/wav")}
                data = {'topic': topic}

                response = requests.post(f"{FASTAPI_URL}/voice/{agent_choice}", data=data, files=files)
                response.raise_for_status()

                # Get audio response and play it back
                response_audio_bytes = response.content
                st.sidebar.audio(response_audio_bytes, format="audio/mpeg")
                st.sidebar.success("✅ Voice command processed successfully!")

                # Clear cache and refresh
                st.cache_data.clear()
                time.sleep(1)  # Small delay to ensure backend has processed
                st.rerun()

        except requests.exceptions.RequestException as e:
            st.sidebar.error(f"❌ Error processing voice command: {e}")
        except Exception as e:
            st.sidebar.error(f"❌ Unexpected error: {e}")
        finally:
            # Clean up temporary file
            try:
                if 'tmp_file_path' in locals():
                    os.unlink(tmp_file_path)
            except:
                pass

st.sidebar.markdown("---")

# Custom TTS Section
st.sidebar.subheader("🎵 Text-to-Speech")
custom_text = st.sidebar.text_area("Enter text to speak:", placeholder="Type any text here...")

if st.sidebar.button("🔊 Speak Custom Text") and custom_text:
    with st.spinner("Generating speech..."):
        audio_data = text_to_speech(custom_text)
        if audio_data:
            st.sidebar.audio(audio_data, format="audio/wav")
            st.sidebar.success("✅ Custom text spoken!")

# Auto-read new responses
if st.sidebar.checkbox("🔄 Auto-read agent responses", help="Automatically read new agent responses aloud"):
    st.session_state.auto_read = True
else:
    st.session_state.auto_read = False

# Main Content Area

# Refresh button
col1, col2 = st.columns([1, 4])
with col1:
    if st.button("🔄 Refresh Logs"):
        st.cache_data.clear()
        st.rerun()

# Fetch and display logs
logs = fetch_logs(topic)

if logs is None:
    st.warning("⚠️ Could not retrieve logs from the server. Please check your connection.")
elif not logs:
    st.info(f"ℹ️ No logs found yet for the topic: '**{topic}**'. Run an agent to begin!")
else:
    # Group logs by agent
    grouped_logs = defaultdict(list)
    for log in logs:
        grouped_logs[log['agent']].append(log)

    # Display summary
    st.markdown(f"**Total interactions:** {len(logs)} | **Active agents:** {len(grouped_logs)}")
    st.markdown("---")

    # Render grouped logs in a timeline format
    for agent_name, agent_logs in grouped_logs.items():
        visuals = AGENT_VISUALS.get(agent_name, AGENT_VISUALS["default"])

        # Agent header
        st.markdown(
            f"<h3 style='color: {visuals['color']};'>{visuals['icon']} Agent: {agent_name} ({len(agent_logs)} interactions)</h3>",
            unsafe_allow_html=True
        )

        # Sort logs by timestamp
        sorted_logs = sorted(agent_logs, key=lambda x: x.get('timestamp', ''), reverse=True)

        for idx, log in enumerate(sorted_logs):
            try:
                dt_object = datetime.fromisoformat(log['timestamp'])
                formatted_time = dt_object.strftime('%Y-%m-%d %H:%M:%S')

                # Create expandable section for each log
                with st.expander(f"🕒 {formatted_time} (Interaction #{len(sorted_logs) - idx})", expanded=(idx == 0)):
                    st.markdown(log.get('content', 'No content available'))

                    # Add TTS button for individual log
                    col1, col2 = st.columns([3, 1])
                    with col2:
                        if st.button(f"🔊 Read", key=f"tts_{agent_name}_{idx}"):
                            content = log.get('content', 'No content available')
                            audio_data = text_to_speech(f"Agent {agent_name} said: {content}")
                            if audio_data:
                                st.audio(audio_data, format="audio/wav")

            except (ValueError, TypeError) as e:
                st.warning(f"⚠️ Could not parse timestamp '{log.get('timestamp')}'. Error: {e}")
                with st.expander(f"🕒 Unknown time (Interaction #{len(sorted_logs) - idx})", expanded=False):
                    st.markdown(log.get('content', 'No content available'))

                    # Add TTS button for individual log
                    col1, col2 = st.columns([3, 1])
                    with col2:
                        if st.button(f"🔊 Read", key=f"tts_{agent_name}_unknown_{idx}"):
                            content = log.get('content', 'No content available')
                            audio_data = text_to_speech(f"Agent {agent_name} said: {content}")
                            if audio_data:
                                st.audio(audio_data, format="audio/wav")

    # --- Export Section ---
    if PDF_AVAILABLE:
        st.markdown("---")
        st.subheader("📄 Export Timeline")

        col1, col2 = st.columns([2, 3])

        with col1:
            if st.button("📥 Generate PDF Report", type="secondary"):
                with st.spinner("Generating PDF report..."):
                    try:
                        report_html = generate_html_report(logs, topic)
                        report_pdf = pdfkit.from_string(report_html, False, configuration=config_pdf)

                        st.download_button(
                            label="⬇️ Download PDF Report",
                            data=report_pdf,
                            file_name=f"agent_report_{topic}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf",
                            type="primary"
                        )
                        st.success("✅ PDF report generated successfully!")
                    except Exception as e:
                        st.error(f"❌ Could not generate PDF: {e}")

        with col2:
            st.markdown("**Export includes:**")
            st.markdown("- Complete conversation timeline")
            st.markdown("- Agent interactions and responses")
            st.markdown("- Timestamps and metadata")
            st.markdown("- Professional formatting")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; font-size: 0.8em;'>"
    "Voice-Controlled Agent System | Powered by FastAPI & Streamlit"
    "</div>",
    unsafe_allow_html=True
)