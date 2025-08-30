import os
import sys

# Add the current directory to Python path to ensure imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from agents import devil_agent, insight_agent, research_agent, summarizer_agent
from agents.base import get_topic_log, transcribe_audio, log_agent_response, generate_audio_response, read_log_aloud

app = FastAPI(title="Voice-Controlled Agent System API")


# ---------- Request Models ----------
class RunAgentRequest(BaseModel):
    topic: str
    query: Optional[str] = None


class TTSRequest(BaseModel):
    text: str


class ReadLogsRequest(BaseModel):
    topic: str
    agent_filter: Optional[str] = None


# ---------- Routes ----------
@app.get("/")
def root():
    return {"message": "Voice-Controlled Agent System API is running 🚀"}


@app.post("/run/{agent_name}")
def run_agent(agent_name: str, request: RunAgentRequest):
    """
    Run a specific agent on a topic.
    """
    topic = request.topic

    try:
        if agent_name == "Devil":
            output = devil_agent.run(topic)
        elif agent_name == "Insight":
            output = insight_agent.run(topic)
        elif agent_name == "Research":
            if not request.query:
                raise HTTPException(status_code=400, detail="Research agent requires a query")
            output = research_agent.run(topic, request.query)
        elif agent_name == "Summarizer":
            output = summarizer_agent.run(topic)
        else:
            raise HTTPException(status_code=404, detail=f"Unknown agent: {agent_name}")

        return {"agent": agent_name, "topic": topic, "output": output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running agent: {str(e)}")


@app.post("/voice/{agent_name}")
async def process_voice_input(
        agent_name: str,
        topic: str = Form(...),
        audio_file: UploadFile = File(...)
):
    """
    Process a voice command: transcribe, pass to agent, and return audio response.
    """
    # Create a temporary file to save the uploaded audio
    temp_audio_path = f"temp_user_input_{audio_file.filename}"
    audio_response_path = None

    try:
        # Save uploaded audio file
        with open(temp_audio_path, "wb") as buffer:
            content = await audio_file.read()
            buffer.write(content)

        # Transcribe the audio to text
        user_query = transcribe_audio(temp_audio_path)

        if not user_query or user_query.strip() == "":
            raise HTTPException(status_code=400, detail="Could not transcribe audio or audio was empty.")

        # Pass transcribed text to the appropriate agent
        agent_response = ""

        if agent_name == "Devil":
            # Check if devil_agent.run accepts 2 parameters
            try:
                agent_response = devil_agent.run(topic, user_query)
            except TypeError:
                # If it only accepts 1 parameter, use just topic
                agent_response = devil_agent.run(topic)
        elif agent_name == "Insight":
            try:
                agent_response = insight_agent.run(topic, user_query)
            except TypeError:
                agent_response = insight_agent.run(topic)
        elif agent_name == "Research":
            agent_response = research_agent.run(topic, user_query)
        elif agent_name == "Summarizer":
            try:
                agent_response = summarizer_agent.run(topic, user_query)
            except TypeError:
                agent_response = summarizer_agent.run(topic)
        else:
            raise HTTPException(status_code=404, detail=f"Unknown agent: {agent_name}")

        # Log the full interaction
        log_agent_response(topic, agent_name, agent_response)

        # Generate audio response from the agent's text
        audio_response_path = generate_audio_response(agent_response)

        return FileResponse(
            audio_response_path,
            media_type="audio/wav",
            filename=os.path.basename(audio_response_path),
            background=None  # Don't delete the file automatically
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing voice input: {str(e)}")

    finally:
        # Clean up temporary input file
        if os.path.exists(temp_audio_path):
            try:
                os.remove(temp_audio_path)
            except:
                pass  # Ignore cleanup errors


@app.get("/logs/{topic}")
def get_logs(topic: str):
    """Retrieve all logs for a given topic."""
    try:
        logs = get_topic_log(topic)
        if not logs:
            raise HTTPException(status_code=404, detail="No logs found for this topic")
        return {"topic": topic, "logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving logs: {str(e)}")


@app.post("/tts")
def text_to_speech(request: TTSRequest):
    """Convert text to speech and return audio file."""
    try:
        if not request.text or request.text.strip() == "":
            raise HTTPException(status_code=400, detail="Text cannot be empty")

        audio_path = generate_audio_response(request.text)
        return FileResponse(
            audio_path,
            media_type="audio/wav",
            filename=os.path.basename(audio_path)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating speech: {str(e)}")


@app.post("/read-logs")
def read_logs_aloud_post(request: ReadLogsRequest):
    """Read all logs for a topic aloud and return audio."""
    try:
        audio_path = read_log_aloud(request.topic, request.agent_filter)
        return FileResponse(
            audio_path,
            media_type="audio/wav",
            filename=f"logs_audio_{request.topic}.wav"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading logs: {str(e)}")


@app.get("/read-logs/{topic}")
def read_logs_aloud_get(topic: str, agent_filter: Optional[str] = None):
    """Read all logs for a topic aloud (GET endpoint)."""
    try:
        audio_path = read_log_aloud(topic, agent_filter)
        return FileResponse(
            audio_path,
            media_type="audio/wav",
            filename=f"logs_audio_{topic}.wav"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading logs: {str(e)}")