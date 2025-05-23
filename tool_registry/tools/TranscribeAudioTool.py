from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from openai import OpenAI,OpenAIError
from dotenv import load_dotenv
from typing import Type
import os

class TranscribeAudioToolSchema(BaseModel):
    audio_file_path: str = Field(..., description="Full path to the audio file (e.g., audio/meeting1.mp3)")

class TranscribeAudioTool(BaseTool):
    name: str = "Audio Transcriber Tool"
    description: str = "Transcribes an audio file using OpenAI Whisper API. Input must be the path to an audio file."
    args_schema: Type[TranscribeAudioToolSchema] = TranscribeAudioToolSchema

    def _run(self, audio_file_path: str) -> str:
        # Ensure the API key is set
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return "Error: OPENAI_API_KEY environment variable is not set."

        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)

        # Validate the audio file path       
        if not os.path.exists(audio_file_path):
            return f"Error: File not found - {audio_file_path}"

        # Optional: Validate file extension
        valid_extensions = (".mp3", ".wav", ".m4a")
        if not audio_file_path.lower().endswith(valid_extensions):
            return f"Error: Unsupported file format. Supported formats are: {', '.join(valid_extensions)}"
        
        try:
            with open(audio_file_path, "rb") as audio_file:
                print(f"[DEBUG] Reading file: {audio_file_path}")
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
        return self._run(input_data.audio_file_path)
