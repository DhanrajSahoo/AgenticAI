import json
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, model_validator, Field  # Import validator
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import os
import boto3
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
    access_key: str
    secret_key: str

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

        missing_vars = []
        all_fields: Dict[str, Any] = values.__dict__

        for field_name in required_field_names:
            value = all_fields.get(field_name)
            if not value:
                missing_vars.append(field_name)

        if missing_vars:
            raise ValueError(f"Missing critical environment variables: {', '.join(missing_vars)}")
        return values


try:
    settings = Settings()
    print("All critical environment variables are set.")
except ValueError as e:  # Catch the ValueError raised by our validator or Pydantic
    print(f"Configuration Error: {e}")
    raise  # Re-raise to stop the application if needed

def get_secret(secret_name):
    region_name = "us-east-1"
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        aws_access_key_id=settings.access_key,
        aws_secret_access_key=settings.secret_key,
        region_name=region_name
    )
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except Exception as e:
        raise e
    secret = get_secret_value_response['SecretString']
    return json.loads(secret)


db_cred = get_secret("Dev3_credentials")

class Config(object):
    database = 'postgres'  # cf["db"]["database"]
    host = 'localhost'  # cf["db"]["host"]
    port = 5433  # cf["db"]["port"]
    user = 'postgres'  # cf["db"]["user"]
    password = '123#'
    openai_key = db_cred.get('Open_AI_key')


app_config = {
    'local': Config
}