# utils/aws_secrets.py

import json
import boto3
from typing import Dict

def clean_secrets(secret: str) -> str:
    s = secret.replace("apexon", "")
    to_remove = "!@#$%^&*"
    trans = str.maketrans("", "", to_remove)
    return s.translate(trans)

def get_secret(secret_name: str, access_key: str, secret_key: str, region_name: str = "us-east-1") -> Dict:
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region_name
    )
    try:
        response = client.get_secret_value(SecretId=secret_name)
        return json.loads(response['SecretString'])
    except Exception as e:
        raise e
