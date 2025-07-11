# utils/email_utils.py
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os

async def send_email(to_email: str, subject: str, html_content: str):
    message = Mail(
        from_email='xxx@yyy.com',
        to_emails=to_email,
        subject=subject,
        html_content=html_content
    )
    try:
        sg = SendGridAPIClient(os.environ.get("SG.xxxxxxxxxxxxxxx.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"))
        response = sg.send(message)
        return response.status_code
    except Exception as e:
        print(f"SendGrid Error: {str(e)}")
