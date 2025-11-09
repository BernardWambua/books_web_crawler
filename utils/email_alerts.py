import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict, Any
from utils.logger import get_logger

logger = get_logger()

class EmailAlerter:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = os.getenv("ALERT_EMAIL")
        self.sender_password = os.getenv("ALERT_EMAIL_PASSWORD")
        self.recipient_email = os.getenv("RECIPIENT_EMAIL")

    def send_alert(self, subject: str, changes: List[Dict[str, Any]]) -> bool:
        """Send email alert for significant changes"""
        if not all([self.sender_email, self.sender_password, self.recipient_email]):
            logger.error("Email configuration missing. Check environment variables.")
            return False

        try:
            msg = MIMEMultipart()
            msg["From"] = self.sender_email
            msg["To"] = self.recipient_email
            msg["Subject"] = subject

            # Create HTML body with changes table
            body = self._format_changes_html(changes)
            msg.attach(MIMEText(body, "html"))

            # Connect and send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)

            logger.info(f"Alert email sent successfully to {self.recipient_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email alert: {str(e)}")
            return False

    def _format_changes_html(self, changes: List[Dict[str, Any]]) -> str:
        """Format changes as HTML table"""
        html = f"""
        <html>
        <body>
        <h2>Book Changes Detected - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</h2>
        <table border="1" style="border-collapse: collapse; width: 100%;">
        <tr style="background-color: #f2f2f2;">
            <th style="padding: 8px;">Book</th>
            <th style="padding: 8px;">Change Type</th>
            <th style="padding: 8px;">Details</th>
        </tr>
        """

        for change in changes:
            book_url = change.get('url', '#')
            book_title = change.get('title', 'Unknown Book')
            change_type = change.get('type', 'unknown')
            details = change.get('changes', {})

            html += f"""
            <tr>
                <td style="padding: 8px;"><a href="{book_url}">{book_title}</a></td>
                <td style="padding: 8px;">{change_type}</td>
                <td style="padding: 8px;">{self._format_changes_details(details)}</td>
            </tr>
            """

        html += """
        </table>
        </body>
        </html>
        """
        return html

    def _format_changes_details(self, details: Dict[str, Any]) -> str:
        """Format change details as HTML list"""
        if not details:
            return "No details available"

        html = "<ul style='margin: 0; padding-left: 20px;'>"
        for key, value in details.items():
            if isinstance(value, dict) and 'old' in value and 'new' in value:
                html += f"<li>{key}: {value['old']} → {value['new']}</li>"
            else:
                html += f"<li>{key}: {value}</li>"
        html += "</ul>"
        return html