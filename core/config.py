from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from typing import Dict, Any
import os

from utils.aws_secrets import clean_secrets, get_secret, decrypt_message

load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str
    SERPER_API_KEY: str
    OPENAI_API_KEY: str
    OPENAI_MODEL_NAME: str = "gpt-4o-mini"

    EMAIL_HOST: str
    EMAIL_PORT: int = 587
    EMAIL_USER: str
    EMAIL_PASS: str
    access_key: str = 'access_key'
    secret_key: str = 'secret_key'

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        extra="ignore"
    )

    @model_validator(mode='after')
    def check_required_fields(cls, values: 'Settings') -> 'Settings':
        required_field_names = [
            "DATABASE_URL",
            "SERPER_API_KEY",
            "OPENAI_API_KEY",
            "EMAIL_HOST",
            "EMAIL_USER",
            "EMAIL_PASS",
            "access_key",
            "secret_key"
        ]

        missing_vars = [field for field in required_field_names if not getattr(values, field, None)]
        if missing_vars:
            raise ValueError(f"Missing critical environment variables: {', '.join(missing_vars)}")
        return values

try:
    settings = Settings()
    print("All critical environment variables are set.")
except ValueError as e:
    print(f"Configuration Error: {e}")
    raise

# ↓ These are now decoupled from the services layer
access_key = decrypt_message("Z0FBQUFBQm9iaUNqWF9KODliX1MzdG93bExHWkwxcTdkWXZ2eGs0TXA2aE5qNHBzTll3cmFOZVRqSEtIVjMxU2lrczE0c0xhOFlFSUl6cjFndWtFbVoyaUM0aHlLdTJZeWRjNHZja3VDTHdJSGNkSjJLbUVKa2c9", "d1RRdFdWd2dCQWFPeG1ZMGpWVDJScE5QQVZmM3B6ekw2ellOQTRuaHhQaz0=")
secret_key = decrypt_message("Z0FBQUFBQm9iaUlVTUFla2lndlM0REVkNFFlc3ZiX0xnN1kzZElHTnMzRTdid191TDFKeS1UMUszc0ZsaW1ySWZXUXowRndwSUJzSDFLTXNlUy14dlJMYWdQYVFtRVdZTFdyRWk2Si1NMVk3Y2RuTUV1aEVaLUYwaXZFV0tRN3g2TDlSWkc4ZFlYa1k=", "S0ZEcnR2MmpJbjZVZ3MtX25XMHlObTFqVWJEQ3o0S1hMS0lNdG9kTW92RT0=")

# access_key = clean_secrets("apexonAKI!ASC@ZMC#YZB$SZT%4TM^45")
# secret_key = clean_secrets('apexonOnR!MAj@NPo#DOq$m1c%Ywu^cJQ&GG/!TJG@uI2#v4g$Rj8%ZJpf')
db_cred = get_secret("AgenticAI-creds", access_key, secret_key)

class Config(object):
    database = 'postgres'
    host = 'localhost'
    port = 5433
    user = 'postgres'
    password = '123#'
    serper_key = "d2195e549a76d9733d309e84340126182fcf08ef"
    openai_key = db_cred.get('Open_AI_key_agentic')
    access_key = db_cred.get('access_key')
    secret_key = db_cred.get('secret_key')
    policy_access_key = db_cred.get('policy_access_key')
    policy_secret_key = db_cred.get('policy_secret_key')
    mail_pass = db_cred.get('mail_pass')

app_config = {
    'local': Config
}
