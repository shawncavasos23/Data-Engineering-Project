import smtplib
import ssl
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load email credentials securely
EMAIL_SENDER = "5214project@gmail.com"
EMAIL_PASSWORD = "oekx qhns irap bgna"
EMAIL_RECEIVER = "5214project@gmail.com"

def send_email(subject, body):
    """Sends an email notification when an AI trading alert is triggered."""
    try:
        if not EMAIL_SENDER or not EMAIL_PASSWORD or not EMAIL_RECEIVER:
            raise ValueError("Missing email credentials. Set environment variables.")

        msg = MIMEMultipart()
        msg["From"] = EMAIL_SENDER
        msg["To"] = EMAIL_RECEIVER
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        # Establish secure connection with Gmail SMTP server
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER.split(","), msg.as_string())

        print(f"Analysis successfully sent to {EMAIL_RECEIVER}!")

    except smtplib.SMTPAuthenticationError:
        print("Authentication error: Check your email credentials.")
    except smtplib.SMTPConnectError:
        print("Connection error: Unable to reach Gmail SMTP server.")
    except Exception as e:
        print(f"Failed to send email: {e}")

