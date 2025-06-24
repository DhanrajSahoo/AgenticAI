from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from openai import OpenAI,OpenAIError
from core.config import Config
from typing import Type
import os

class TranscribeAudioToolSchema(BaseModel):
    audio_file_path: str = Field(..., description="Full path to the audio file (e.g., audio/meeting1.mp3)")

class TranscribeAudioTool(BaseTool):
    name: str = "Audio Transcriber Tool"
    description: str = "Transcribes an audio file using OpenAI Whisper API. Input must be the path to an audio file."
    args_schema: Type[TranscribeAudioToolSchema] = TranscribeAudioToolSchema

    def _run(self, audio_file_path: str) -> str:
        api_key = os.environ["OPENAI_API_KEY"] = Config.openai_key

        if not os.path.exists(audio_file_path):
            return f"File not found: {audio_file_path}"

        if not audio_file_path.lower().endswith((".mp3", ".wav", ".m4a")):
            return "Unsupported audio format."

        try:
            client = OpenAI(api_key=api_key)
            with open(audio_file_path, "rb") as audio_file:
                result = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
            return result
        except OpenAIError as e:
            return f"OpenAI API error: {str(e)}"
        except Exception as e:
            return f"Transcription failed: {str(e)}"

    def run(self, input_data: TranscribeAudioToolSchema) -> str:
        return self._run(input_data.audio_file_path)
