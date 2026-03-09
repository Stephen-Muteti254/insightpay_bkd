from app.extensions import db
from datetime import datetime, timedelta
import secrets
import hashlib


def generate_otp():
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode()).hexdigest()


class EmailVerificationOTP(db.Model):
    __tablename__ = "insightpay_email_verification_otps"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.String(50),
        db.ForeignKey("insightpay_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    otp_hash = db.Column(db.String(64), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def create_for_user(user_id, minutes=10):
        otp = generate_otp()
        record = EmailVerificationOTP(
            user_id=user_id,
            otp_hash=hash_otp(otp),
            expires_at=datetime.utcnow() + timedelta(minutes=minutes),
        )
        return otp, record

    def is_expired(self):
        return datetime.utcnow() > self.expires_at
