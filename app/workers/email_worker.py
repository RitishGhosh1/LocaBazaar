import asyncio
import json
import aio_pika
import logging
from app.core.config import config
from app.services.email import send_email

async def process_message(message: aio_pika.IncomingMessage):
    async with message.process():
        data = json.loads(message.body.decode())

        job_type = data.get("job_type")

        if job_type != "send_verification_email":
            logging.info("Job Type not email verification")
            return

        email = data.get("email")
        token = data.get("verification_token")

        frontend_url = config.FRONTEND_URL.rstrip("/")
        verificationmail = f"{frontend_url}/verify-email?token={token}"

        body = f"""Hello,

Please verify your LocaBazaar email address by clicking the link below:

{verificationmail}

Thank you,
LocaBazaar"""

        html_body = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Verify Your LocaBazaar Email</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f4f4f7; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #333333;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color: #f4f4f7; padding: 40px 0;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width: 560px; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05); margin: 0 20px;">
          <!-- Header -->
          <tr>
            <td style="background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); padding: 32px 40px; text-align: center;">
              <h1 style="color: #ffffff; margin: 0; font-size: 26px; font-weight: 700; letter-spacing: -0.5px;">LocaBazaar</h1>
              <p style="color: rgba(255, 255, 255, 0.85); margin: 6px 0 0 0; font-size: 14px;">Verified Local Services Marketplace</p>
            </td>
          </tr>
          <!-- Main Content -->
          <tr>
            <td style="padding: 40px 40px 32px 40px;">
              <h2 style="margin: 0 0 16px 0; font-size: 20px; font-weight: 600; color: #111827;">Verify your email address</h2>
              <p style="margin: 0 0 28px 0; font-size: 15px; line-height: 24px; color: #4b5563;">
                Thank you for joining LocaBazaar! To activate your account and start exploring verified local services, please confirm your email address by clicking the button below:
              </p>
              <!-- Clickable Button -->
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td align="center" style="padding: 8px 0 32px 0;">
                    <a href="{verificationmail}" target="_blank" style="display: inline-block; background-color: #4f46e5; color: #ffffff; font-size: 15px; font-weight: 600; text-decoration: none; padding: 14px 32px; border-radius: 8px; box-shadow: 0 2px 4px rgba(79, 70, 229, 0.3);">
                      Verify Email Address
                    </a>
                  </td>
                </tr>
              </table>
              <p style="margin: 0 0 12px 0; font-size: 13px; line-height: 20px; color: #6b7280;">
                If the button above doesn't work, copy and paste this link into your browser:
              </p>
              <p style="margin: 0; font-size: 12px; line-height: 18px; word-break: break-all;">
                <a href="{verificationmail}" style="color: #4f46e5; text-decoration: underline;">{verificationmail}</a>
              </p>
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="background-color: #f9fafb; padding: 24px 40px; border-top: 1px solid #e5e7eb; text-align: center;">
              <p style="margin: 0; font-size: 12px; color: #9ca3af; line-height: 18px;">
                If you did not create an account on LocaBazaar, you can safely ignore this email.
              </p>
              <p style="margin: 8px 0 0 0; font-size: 12px; color: #9ca3af;">
                &copy; LocaBazaar. All rights reserved.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

        try:
            send_email(
                to_email=email,
                subject="Verify Your LocaBazaar Email",
                body=body,
                html_body=html_body,
            )
            print("EMAIL SENT !!")
        except Exception as e:
            print(f"Error Occured {e}")

async def main():
    connection = await aio_pika.connect_robust(
        config.RABBITMQ_URL
    )

    channel = await connection.channel()

    queue = await channel.declare_queue(
        "email_verification",
        durable=True,
    )

    await queue.consume(process_message)

    print("Email worker started...")

    try:
        await asyncio.Future()
    finally:
        await connection.close()


if __name__ == "__main__":
    asyncio.run(main())