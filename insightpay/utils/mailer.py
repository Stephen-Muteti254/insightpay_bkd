import smtplib
from email.message import EmailMessage
from email.utils import make_msgid
from flask import current_app


def send_insightpay_email(to: str, subject: str, html: str):
    """
    Sends transactional emails for InsightPay using Zoho SMTP
    """

    msg = EmailMessage()

    msg["From"] = (
        f"{current_app.config['INSIGHTPAY_EMAIL_FROM_NAME']} "
        f"<{current_app.config['INSIGHTPAY_EMAIL_FROM_ADDRESS']}>"
    )
    msg["To"] = to
    msg["Subject"] = subject
    msg["Reply-To"] = current_app.config["INSIGHTPAY_EMAIL_FROM_ADDRESS"]
    msg["Message-ID"] = make_msgid(domain="insightpay.com")

    # Fallback plain text
    msg.set_content(
        "This is an automated message from InsightPay. "
        "Please view this email in an HTML-capable email client."
    )

    # HTML body
    msg.add_alternative(html, subtype="html")

    try:
        with smtplib.SMTP_SSL(
            current_app.config["ZOHO_SMTP_HOST"],
            current_app.config["ZOHO_SMTP_PORT"],
        ) as server:
            server.login(
                current_app.config["INSIGHTPAY_EMAIL_FROM_ADDRESS"],
                current_app.config["INSIGHTPAY_ZOHO_APP_PASSWORD"],
            )
            server.send_message(msg)

        print(f"InsightPay email sent to {to}")

    except Exception as e:
        print(f"Failed to send InsightPay email to {to}: {e}")
        raise
