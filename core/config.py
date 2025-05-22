from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    SERPER_API_KEY: str = os.getenv("SERPER_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL_NAME: str = os.getenv("OPENAI_MODEL_NAME", "gpt-4-turbo-preview") # Default model

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = "ignore"


settings = Settings()

if not settings.DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set.") #todo: check for other keys
