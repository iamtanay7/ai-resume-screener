import smtplib
from email.message import EmailMessage

from server.config import settings


def send_email(to_email: str, subject: str, body: str) -> dict[str, str]:
    if not settings.email_enabled:
        return {"status": "skipped", "detail": "email_enabled is false. Email was not sent."}

    if not settings.smtp_host or not settings.smtp_username or not settings.smtp_password:
        raise ValueError("SMTP configuration is incomplete.")

    sender = settings.smtp_sender or settings.smtp_username or "no-reply@example.com"

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = to_email
    message.set_content(body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.smtp_username, settings.smtp_password)
        server.send_message(message)

    return {"status": "sent", "detail": f"Email sent to {to_email}."}
