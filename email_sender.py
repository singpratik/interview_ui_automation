# email_sender.py
import os
import time
import logging
import json
import requests
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class EmailSender:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.api_endpoint = "https://sandbox.api.mailtrap.io/api/send/3802080"
        self.max_retries = 3    
        self.timeout = 10
    
    def send_html_report(self, html_file_path: str, json_file_path: Optional[str] = None,
                       recipient_email: str = 'kuldeep.kushwaha@vmock.com',
                       sender_email: str = 'pratik.singh@vmock.com') -> bool:
        """Send email with HTML and JSON attachments"""
        if not os.path.exists(html_file_path):
            self.logger.error(f"HTML file not found: {html_file_path}")
            return False

        for attempt in range(self.max_retries):
            try:
                attachments = []
                with open(html_file_path, 'rb') as f:
                    attachments.append({
                        "content": self._encode_base64(f.read()),
                        "filename": os.path.basename(html_file_path),
                        "type": "text/html",
                        "disposition": "attachment"
                    })

                if json_file_path and os.path.exists(json_file_path):
                    with open(json_file_path, 'rb') as f:
                        attachments.append({
                            "content": self._encode_base64(f.read()),
                            "filename": os.path.basename(json_file_path),
                            "type": "application/json",
                            "disposition": "attachment"
                        })

                payload = {
                    "from": {"email": sender_email},
                    "to": [{"email": recipient_email}],
                    "subject": f"VMock Report {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    "text": "API Monitoring Report attached",
                    "attachments": attachments
                }

                headers = {
                    "Authorization": f"Bearer {self.config['api_token']}",
                    "Content-Type": "application/json"
                }

                session = requests.Session()
                session.verify = True
                response = session.post(
                    self.api_endpoint,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    self.logger.info("Email sent successfully via Mailtrap API")
                    return True
                else:
                    error_msg = f"API Error {response.status_code}: {response.text}"
                    self.logger.warning(f"Attempt {attempt + 1} failed. {error_msg}")
                    if attempt < self.max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    return False

            except Exception as e:
                self.logger.warning(f"Error on attempt {attempt + 1}: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                self.logger.error("Failed after retries")
        
        return False
            
    def _encode_base64(self, data: bytes) -> str:
        """Helper method for base64 encoding"""
        import base64
        return base64.b64encode(data).decode('utf-8')