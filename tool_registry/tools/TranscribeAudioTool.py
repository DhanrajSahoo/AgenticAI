from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from openai import OpenAI,OpenAIError
from dotenv import load_dotenv
from core.config import Config
from typing import Type
import os
import logging
from services.aws_services import CloudWatchLogHandler
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = CloudWatchLogHandler('agentic-ai', 'agentic-ai')
logger.addHandler(handler)

class TranscribeAudioToolSchema(BaseModel):
    pdf_path: str = Field(..., description="Full path to the audio file (e.g., audio/meeting1.mp3)")

class TranscribeAudioTool(BaseTool):
    name: str = "Audio Transcriber Tool"
    description: str = "Transcribes an audio file using OpenAI Whisper API. Input must be the path to an audio file."
    args_schema: Type[TranscribeAudioToolSchema] = TranscribeAudioToolSchema

    def _run(self, pdf_path: str) -> str:
        logger.info(f"[DEBUG] Received pdf_path: {pdf_path}")
        # Ensure the API key is set
        api_key = os.environ["OPENAI_API_KEY"] = Config.openai_key
        if not api_key:
            return "Error: OPENAI_API_KEY environment variable is not set."

        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)

        # Validate the audio file path       
        if not os.path.exists(pdf_path):
            return f"Error: File not found - {pdf_path}"

        # Optional: Validate file extension
        valid_extensions = (".mp3", ".wav", ".m4a")
        if not pdf_path.lower().endswith(valid_extensions):
            return f"Error: Unsupported file format. Supported formats are: {', '.join(valid_extensions)}"
        
        try:
            with open(pdf_path, "rb") as audio_file:
                print(f"[DEBUG] Reading file: {pdf_path}")
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
            return transcript
        except OpenAIError as e:
            return f"Transcription failed due to API error: {str(e)}"
        except Exception as e:
            return f"Transcription failed: {str(e)}"
        
    def run(self, input_data: TranscribeAudioToolSchema) -> str:
        return self._run(input_data.pdf_path)

