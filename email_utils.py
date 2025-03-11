import smtplib
import ssl
from email.message import EmailMessage

# 🔹 **Set Your Email Credentials**
EMAIL_SENDER = "your_email@gmail.com"
EMAIL_PASSWORD = "your_app_password"
EMAIL_RECEIVER = "your_email@gmail.com"  # Change to your recipient email

def send_email(subject, body):
    """
    Sends an email with the AI-generated trading signal.
    """

    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
            print("✅ Email successfully sent!")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
