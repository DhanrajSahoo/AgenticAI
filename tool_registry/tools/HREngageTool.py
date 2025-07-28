import base64
import requests
from datetime import datetime
import re
from pydantic import BaseModel, Field
from typing import Type
from crewai.tools import BaseTool
from email.message import EmailMessage
import smtplib


class HREngageSchema(BaseModel):
    output_file: str = Field("newsletter.html", description="Output HTML file name for the newsletter")
    email_to: str = Field(..., description="Recipient email address")


def get_image_base64(url):
    response = requests.get(url)
    if response.status_code == 200:
        encoded_string = base64.b64encode(response.content).decode('utf-8')
        # Guess MIME type
        if url.endswith('.png'):
            mime = 'image/png'
        elif url.endswith('.jpg') or url.endswith('.jpeg'):
            mime = 'image/jpeg'
        elif url.endswith('.gif'):
            mime = 'image/gif'
        else:
            mime = 'image/png'
        return f"data:{mime};base64,{encoded_string}"
    else:
        print(f"⚠️ Failed to download image: {url}")
        return None


class HREngageTool(BaseTool):
    name: str = "HREngageTool"
    description: str = "Fetches top posts from Viva Engage and creates an HTML newsletter and sends it"

    args_schema: Type[BaseModel] = HREngageSchema

    def _run(self, output_file: str, email_to: str) -> str:
        access_token = "9653-6WqdEW40o8I2Wa7BmYgFg"
        group_id = "152610791424"
        print("✅ HREngageTool running...")
        print(output_file)
        print(email_to)
        try:
            url = f"https://www.yammer.com/api/v1/messages/in_group/{group_id}.json"
            headers = {"Authorization": f"Bearer {access_token}"}

            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                return f"❌ ERROR: {response.status_code} - {response.text}"

            data = response.json()
            messages = data.get("messages", [])[:10]

            html_content = """
            <html>
            <head>
              <title>All about Apexon</title>
              <style>
                body {
                  font-family: Arial, sans-serif;
                  font-size: 16px;
                  line-height: 1.6;
                  color: #333;
                  max-width: 800px;
                  margin: 20px auto;
                  padding: 20px;
                }
                h1 {
                  color: #005a9c;
                  font-size: 28px;
                }
                h2 {
                  color: #0078d4;
                  font-size: 20px;
                  border-bottom: 1px solid #ccc;
                  padding-bottom: 5px;
                }
                p {
                  margin-bottom: 10px;
                }
                img {
                  margin-top: 10px;
                  max-width: 100%;
                  height: auto;
                  border: 1px solid #ddd;
                }
              </style>
            </head>
            <body>
            """
            html_content += "<h1>All about Apexon</h1>"

            for i, msg in enumerate(messages, start=1):
                raw_date = msg["created_at"]
                dt = datetime.strptime(raw_date.split(" +")[0], "%Y/%m/%d %H:%M:%S")
                formatted_date = dt.strftime("%B %d, %Y at %I:%M %p")

                raw_body = msg["body"].get("parsed", "")
                clean_body = re.sub(r'\[\[tag:\d+\]\]', '', raw_body).strip()

                html_content += f"<h2>Post #{i}</h2>"
                html_content += f"<p><strong>Date:</strong> {formatted_date}</p>"
                html_content += f"<p>{clean_body}</p>"
                for att in msg.get("attachments", []):
                    if att.get("type") == "image":
                        image_url = att.get("download_url")
                        if image_url:
                            img_data = get_image_base64(image_url)
                            if img_data:
                                html_content += f"<img src='{img_data}'><br>"

            html_content += "</body></html>"

            # Write to file
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(html_content)

            # Send email
           # self._send_email(html_content, email_to)

            #@return f"✅ Newsletter created successfully: {output_file} and sent to {email_to}"
            return html_content
        except Exception as e:
            return f"❌ ERROR: {e}"

    def _send_email(self, html_content: str, recipient: str):
        smtp_server = "smtp.office365.com"
        smtp_port = 587
        smtp_username = "harshada.kothe@apexon.com"
        smtp_password = "kvfnshpxmtwtpfpw"

        msg = EmailMessage()
        msg["Subject"] = "All about Apexon - HR Engage Newsletter"
        msg["From"] = smtp_username
        msg["To"] = recipient

        msg.set_content("Your email client does not support HTML.")
        msg.add_alternative(html_content, subtype="html")

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)

        print(f"✅ Email sent to {recipient}")

    def run(self, input_data: HREngageSchema) -> str:
        return self._run(input_data.output_file, input_data.email_to)

