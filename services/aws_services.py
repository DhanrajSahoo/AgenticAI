import boto3
from fastapi import UploadFile

s3 = boto3.client('s3')

def upload_pdf_to_s3_direct(file: UploadFile, bucket_name: str, s3_key: str) -> str:
    s3.upload_fileobj(file.file, bucket_name, s3_key)
    public_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"
    return public_url


# upload_pdf_to_s3('/Users/mohan.kumar2/Downloads/Webassessor.pdf','apexon-agentic-ai','Webassessor.pdf')