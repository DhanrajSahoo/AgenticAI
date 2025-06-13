import boto3
import logging
from fastapi import UploadFile
from core.config import Config
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

access_key = Config.access_key
secret_key = Config.secret_key

s3 = boto3.client('s3',aws_access_key_id=access_key,aws_secret_access_key=secret_key,region_name='us-east-1')

def upload_pdf_to_s3_direct(file: UploadFile, bucket_name: str, s3_key: str) -> str:
    s3.upload_fileobj(file.file, bucket_name, s3_key)
    public_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"
    return public_url

class CloudWatchLogHandler(logging.Handler):
    def __init__(self, log_group, stream_name, aws_region='us-east-1'):
        logging.Handler.__init__(self)
        self.cw_client = boto3.client('logs', region_name=aws_region,aws_access_key_id=access_key,aws_secret_access_key=secret_key)
        self.log_group = log_group
        self.stream_name = stream_name
        self.sequence_token = None
        self.ensure_log_stream() #stream log
    def ensure_log_stream(self):
        """Ensure that the CloudWatch log stream exists."""
        try:
            self.cw_client.create_log_stream(logGroupName=self.log_group, logStreamName=self.stream_name)
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceAlreadyExistsException':
                raise
    def emit(self, record):
        """Emit a log record to CloudWatch Logs."""
        message = self.format(record)
        kwargs = {
            'logGroupName': self.log_group,
            'logStreamName': self.stream_name,
            'logEvents': [
                {
                    'timestamp': int(record.created * 1000),  # milliseconds
                    'message': message
                },
            ],
        }
        if self.sequence_token:
            kwargs['sequenceToken'] = self.sequence_token

        try:
            response = self.cw_client.put_log_events(**kwargs)
        except self.cw_client.exceptions.InvalidSequenceTokenException as e:
            self.sequence_token = e.response['expectedSequenceToken']
            kwargs['sequenceToken'] = self.sequence_token
            response = self.cw_client.put_log_events(**kwargs)

        self.sequence_token = response['nextSequenceToken']


# upload_pdf_to_s3('/Users/mohan.kumar2/Downloads/Webassessor.pdf','apexon-agentic-ai','Webassessor.pdf')