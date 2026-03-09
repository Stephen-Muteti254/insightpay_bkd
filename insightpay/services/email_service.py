from flask import current_app, render_template
from datetime import datetime
from insightpay.utils.mailer import send_insightpay_email


COMPANY_NAME = "InsightPay"
OTP_EXPIRY_MINUTES = 10


def send_email_verification_otp(user, otp):
    html = render_template(
        "insightpay/verify_email.html",
        full_name=user.name,
        otp=otp,
        expires_in=OTP_EXPIRY_MINUTES,
        company_name=COMPANY_NAME,
        year=datetime.utcnow().year,
    )

    send_insightpay_email(
        to=user.email,
        subject="Verify your InsightPay email",
        html=html,
    )
