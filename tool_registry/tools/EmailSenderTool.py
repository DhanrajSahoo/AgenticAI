from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from dotenv import load_dotenv
from email.mime.text import MIMEText
from core.config import settings
import smtplib
from typing import Type
import os

# Step 1: Define the input schema
class EmailSendSchema(BaseModel):
    recipient: str = Field(..., description="Email address of the recipient")
    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Plain text email body content")

# Step 2: The actual tool logic
class EmailSenderTool(BaseTool):
    name: str = "Email Sender Tool"
    description: str = "Sends a real email to the recipient using SMTP."
    args_schema: Type[BaseModel] = EmailSendSchema

    def _run(self, recipient: str, subject: str, body: str) -> str:
        try:
            # Load email config from .env
            load_dotenv()
            smtp_host = settings.EMAIL_HOST
            smtp_port = settings.EMAIL_PORT
            smtp_user = settings.EMAIL_USER
            smtp_pass = settings.EMAIL_PASS

            # Build email message
            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = smtp_user
            msg["To"] = recipient

            # Send using SMTP
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)

            return f"✅ Email sent successfully to {recipient}"
        except Exception as e:
            return f"❌ Failed to send email: {str(e)}"

    def run(self, input_data: EmailSendSchema) -> str:
        return self._run(input_data.recipient, input_data.subject, input_data.body)
