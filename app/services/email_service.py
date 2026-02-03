import smtplib
from email.message import EmailMessage
from flask import current_app, render_template
from datetime import datetime
from app.utils.mailer import send_email
from app.models.user import User

COMPANY_NAME = "Academic Hub"

from markupsafe import Markup

def format_message(message: str):
    """
    Converts a message string into safe HTML for emails.
    Replaces newlines with <br> and ensures HTML tags are rendered safely.
    """
    # Replace newlines with <br>
    safe_msg = message.replace("\n", "<br>")
    # Wrap as Markup so Jinja does not escape it again
    return Markup(safe_msg)


def send_verification_email(user, token):
    verify_url = f"{current_app.config['FRONTEND_URL']}/verify-email?token={token}"
    html = render_template(
        "emails/verify_email.html",
        full_name=user.full_name,
        verify_url=verify_url,
        year=datetime.utcnow().year
    )
    try:
        send_email(
            to=user.email,
            subject="Verify your Academic Hub account",
            html=html
        )
    except Exception as e:
        print(f"Failed to send email to {user.email}: {e}")


def send_application_received_email(user):
    try:
        send_email(
            to=user.email,
            subject="We’ve received your writer application",
            html=render_template(
                "emails/application_received.html",
                title="Application Received",
                full_name=user.full_name,
                company_name=COMPANY_NAME,
            ),
        )
    except Exception as e:
        print(f"Failed to send email to {to}: {e}")


def send_application_approved_email(user, feedback=None):
    onboarding_url = f"{current_app.config['FRONTEND_URL']}/writer"

    try:
        send_email(
            to=user.email,
            subject="Your writer application has been approved",
            html=render_template(
                "emails/application_approved.html",
                title="Application Approved",
                full_name=user.full_name,
                feedback=format_message(feedback),
                onboarding_url=onboarding_url,
                company_name=COMPANY_NAME,
                year=datetime.utcnow().year,
            ),
        )
    except Exception as e:
        current_app.logger.error(
            f"Failed to send approval email to {user.email}: {e}"
        )


def send_application_rejected_email(user, feedback=None):
    try:
        send_email(
            to=user.email,
            subject="Update on your writer application",
            html=render_template(
                "emails/application_rejected.html",
                title="Application Update",
                full_name=user.full_name,
                feedback=format_message(feedback),
                company_name=COMPANY_NAME,
                year=datetime.utcnow().year,
            ),
        )
    except Exception as e:
        current_app.logger.error(
            f"Failed to send rejection email to {user.email}: {e}"
        )


def send_deposit_approved_email(user):
    """
    Notify the writer that their initial deposit has been approved,
    and they now have access to orders after completing their profile.
    """
    try:
        send_email(
            to=user.email,
            subject="Your initial deposit has been approved",
            html=render_template(
                "emails/deposit_approved.html",
                title="Deposit Approved",
                full_name=user.full_name,
                company_name=COMPANY_NAME,
            ),
        )
    except Exception as e:
        print(f"Failed to send deposit approval email to {user.email}: {e}")

def send_bid_accepted_email(user, order):
    try:
        html = render_template(
            "emails/bid_accepted.html",
            full_name=user.full_name,
            order_title=order.title,
            company_name=COMPANY_NAME,
            year=datetime.utcnow().year
        )
        send_email(
            to=user.email,
            subject=f"Your bid was accepted for {order.title}",
            html=html
        )
    except Exception as e:
        print(f"Failed to send bid accepted email to {user.email}: {e}")


def send_withdrawal_paid_email(user, amount):
    try:
        html = render_template(
            "emails/withdrawal_paid.html",
            full_name=user.full_name,
            amount=amount,
            company_name=COMPANY_NAME,
            year=datetime.utcnow().year
        )
        send_email(
            to=user.email,
            subject=f"Your withdrawal of ${amount:.2f} has been paid",
            html=html
        )
    except Exception as e:
        print(f"Failed to send withdrawal paid email to {user.email}: {e}")


def send_withdrawal_rejected_email(user, amount, reason=None):
    reason_text = f": {reason}" if reason else ""
    try:
        html = render_template(
            "emails/withdrawal_rejected.html",
            full_name=user.full_name,
            amount=amount,
            reason_text=reason_text,
            company_name=COMPANY_NAME,
            year=datetime.utcnow().year
        )
        send_email(
            to=user.email,
            subject=f"Your withdrawal of ${amount:.2f} was rejected",
            html=html
        )
    except Exception as e:
        print(f"Failed to send withdrawal rejected email to {user.email}: {e}")


def send_order_cancelled_email(user, order, reason=None):
    try:
        html = render_template(
            "emails/order_cancelled.html",
            full_name=user.full_name,
            order_title=order.title,
            reason=reason,
            company_name=COMPANY_NAME,
            year=datetime.utcnow().year
        )
        send_email(
            to=user.email,
            subject=f"Order {order.title} has been cancelled",
            html=html
        )
    except Exception as e:
        print(f"Failed to send order cancelled email to {user.email}: {e}")


def send_order_completed_email(user, order, amount):
    try:
        html = render_template(
            "emails/order_completed.html",
            full_name=user.full_name,
            order_title=order.title,
            amount=amount,
            company_name=COMPANY_NAME,
            year=datetime.utcnow().year
        )
        send_email(
            to=user.email,
            subject=f"Order {order.title} marked as completed",
            html=html
        )
    except Exception as e:
        print(f"Failed to send order completed email to {user.email}: {e}")


OTP_EXPIRY_MINUTES = 10

def send_login_otp_email(user, otp):
    try:
        html = render_template(
            "emails/login_otp.html",
            full_name=user.full_name,
            otp=otp,
            expires_in_minutes=OTP_EXPIRY_MINUTES,
            company_name=COMPANY_NAME,
            year=datetime.utcnow().year,
        )

        send_email(
            to=user.email,
            subject="Your Academic Hub login code",
            html=html,
        )

        current_app.logger.info(
            f"Login OTP email sent to user_id={user.id}"
        )

    except Exception as e:
        current_app.logger.error(
            f"Failed to send OTP email to user_id={user.id}: {str(e)}"
        )


def send_notification_email(
    user: User,
    title: str,
    message: str,
    sender_team: str
):
    try:
        html = render_template(
            "emails/notification.html",
            full_name=user.full_name,
            title=title,
            message=format_message(message),
            sender_team=sender_team,
            company_name=COMPANY_NAME,
            year=datetime.utcnow().year,
        )

        send_email(
            to=user.email,
            subject=title,
            html=html
        )
    except Exception as e:
        current_app.logger.error(
            f"Failed to send notification email to user_id={user.id}: {e}"
        )


def send_account_suspension_email(
    user,
    suspension_type: str,
    reasons: list,
    notes: str = None,
    suspended_until=None
):
    duration_text = (
        suspended_until.strftime("%B %d, %Y")
        if suspension_type == "temporary" and suspended_until
        else "Indefinite"
    )

    try:
        send_email(
            to=user.email,
            subject="Academic Hub Account Update",
            html=render_template(
                "emails/account_suspended.html",
                title="Account Suspension",
                full_name=user.full_name,
                suspension_type=suspension_type,
                reasons=reasons,
                notes=format_message(notes),
                duration_text=duration_text,
                company_name=COMPANY_NAME,
                year=datetime.utcnow().year,
            ),
        )
    except Exception as e:
        current_app.logger.error(
            f"Failed to send suspension email to {user.email}: {e}"
        )


def send_account_reactivated_email(user):
    try:
        send_email(
            to=user.email,
            subject="Your Academic Hub Account Has Been Reactivated",
            html=render_template(
                "emails/account_reactivated.html",
                title="Account Reactivated",
                full_name=user.full_name,
                company_name=COMPANY_NAME,
                year=datetime.utcnow().year,
            ),
        )
    except Exception as e:
        current_app.logger.error(
            f"Failed to send reactivation email to {user.email}: {e}"
        )


def send_order_restored_email(user, order, restored_status):
    try:
        dashboard_url = (
            f"{current_app.config['FRONTEND_URL']}/writer/orders/in-progress/all"
        )

        html = render_template(
            "emails/order_restored.html",
            title="Order Restored",
            full_name=user.full_name,
            order_title=order.title,
            restored_status=restored_status,
            dashboard_url=dashboard_url,
            company_name=COMPANY_NAME,
            year=datetime.utcnow().year,
        )

        send_email(
            to=user.email,
            subject=f"Order {order.title} has been restored",
            html=html
        )
    except Exception as e:
        current_app.logger.error(
            f"Failed to send order restored email to {user.email}: {e}"
        )
