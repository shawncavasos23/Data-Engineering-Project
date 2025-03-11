import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Email credentials
EMAIL_SENDER = "5214project@gmail.com"
EMAIL_PASSWORD = "itee roju ludy ipsk"  # App password (replace if needed)
EMAIL_RECEIVER = "5214project@gmail.com"

def send_email(subject, body):
    """Sends an email with AI trading analysis results."""
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_SENDER
        msg["To"] = EMAIL_RECEIVER
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        # Establish connection with Gmail SMTP server
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())

        print(f"Email successfully sent to {EMAIL_RECEIVER}!")

    except Exception as e:
        print(f"Failed to send email: {e}")
