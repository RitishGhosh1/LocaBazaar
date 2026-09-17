import smtplib
from email.message import EmailMessage
from app.core.config import smtpconfig
from app.core.rabbitmq import rabbitmq_manager
from app.core.verification import generate_verification_token


async def queue_verification_email(
    user_id: int,
    email: str,
):
    verification_token = generate_verification_token(email)

    await rabbitmq_manager.publish(
        {
            "job_type": "send_verification_email",
            "user_id": user_id,
            "email": email,
            "verification_token": verification_token,
        }
    )

def send_email(
    to_email: str,
    subject: str,
    body: str,
    html_body: str | None = None,
):
    message = EmailMessage()

    message["From"] = smtpconfig.SMTP_FROM_EMAIL
    message["To"] = to_email
    message["Subject"] = subject

    message.set_content(body)

    if html_body:
        message.add_alternative(html_body, subtype="html")

    with smtplib.SMTP(
        smtpconfig.SMTP_HOST,
        smtpconfig.SMTP_PORT,
    ) as smtp:
        smtp.starttls()

        smtp.login(
            smtpconfig.SMTP_USERNAME,
            smtpconfig.SMTP_PASSWORD,
        )

        smtp.send_message(message)