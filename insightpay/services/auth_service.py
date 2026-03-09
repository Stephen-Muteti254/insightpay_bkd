# app/services/auth_service.py
from app.extensions import db
from insightpay.models.user import InsightPayUser
from werkzeug.exceptions import BadRequest
from flask_jwt_extended import create_access_token

from insightpay.models.user import InsightPayUser
from insightpay.models.email_verification import EmailVerificationOTP, hash_otp
from insightpay.services.email_service import send_email_verification_otp

class AuthService:

    @staticmethod
    def register_user(email: str, password: str, name: str):
        if len(password) < 8:
            raise BadRequest("Password must be at least 8 characters")

        existing_user = InsightPayUser.query.filter_by(email=email).first()
        if existing_user:
            raise BadRequest("Email already registered")

        user = InsightPayUser(
            email=email,
            name=name,
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        token = create_access_token(identity=user.id)

        return {
            "user": user.to_dict(),
            "token": token,
        }

    @staticmethod
    def send_verification(user):
        EmailVerificationOTP.query.filter_by(user_id=user.id).delete()

        otp, record = EmailVerificationOTP.create_for_user(user.id)
        db.session.add(record)
        db.session.commit()

        print(f"otp = {otp} record = {record}")

        send_email_verification_otp(user, otp)

    @staticmethod
    def verify_email(user, otp: str):
        record = EmailVerificationOTP.query.filter_by(user_id=user.id).first()

        if not record:
            raise BadRequest("Verification code not found")

        if record.is_expired():
            raise BadRequest("Verification code expired")

        if record.otp_hash != hash_otp(otp):
            return False

        user.email_verified = True
        user.status = "email_verified"

        db.session.delete(record)
        db.session.commit()

        return True
