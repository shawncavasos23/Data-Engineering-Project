import smtplib
import ssl
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

# Load email credentials with environment variable fallback
EMAIL_SENDER = os.getenv("EMAIL_SENDER", "5214project@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "oekx qhns irap bgna")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER", "5214project@gmail.com")

def send_email(subject: str, body: str, html: bool = False, attachment_path: str = None) -> bool:
    """
    Send an email with the specified subject, body, and optional file attachment.

    Parameters:
        subject (str): Email subject line.
        body (str): Email content (plain text or HTML).
        html (bool): Whether to send the body as HTML. Defaults to False.
        attachment_path (str): Optional path to a file to attach.

    Returns:
        bool: True if email was sent successfully, False otherwise.
    """
    try:
        if not EMAIL_SENDER or not EMAIL_PASSWORD or not EMAIL_RECEIVER:
            raise ValueError("Missing email credentials. Please set them as environment variables or in the script.")

        msg = MIMEMultipart()
        msg["From"] = EMAIL_SENDER
        msg["To"] = EMAIL_RECEIVER
        msg["Subject"] = subject

        mime_type = "html" if html else "plain"
        msg.attach(MIMEText(body, mime_type))

        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as f:
                part = MIMEApplication(f.read(), Name=os.path.basename(attachment_path))
                part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment_path)}"'
                msg.attach(part)

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER.split(","), msg.as_string())

        logging.info(f"Email sent to {EMAIL_RECEIVER} with subject '{subject}'")
        return True

    except smtplib.SMTPAuthenticationError:
        logging.error("SMTP authentication failed. Please verify email and password.")
    except smtplib.SMTPConnectError:
        logging.error("Failed to connect to the SMTP server.")
    except Exception as e:
        logging.error(f"Unexpected error occurred while sending email: {e}")

    return False