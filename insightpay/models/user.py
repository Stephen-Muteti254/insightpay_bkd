# app/models/user.py
from app.extensions import db
from datetime import datetime
import uuid
from werkzeug.security import generate_password_hash, check_password_hash


def gen_uuid(prefix="usr"):
    return f"{prefix}_{uuid.uuid4()}"


class InsightPayUser(db.Model):
    __tablename__ = "insightpay_users"

    id = db.Column(db.String(50), primary_key=True, default=gen_uuid)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)

    email_verified = db.Column(db.Boolean, default=False)

    status = db.Column(
        db.String(50),
        default="email_unverified",
        nullable=False
    )

    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ---- password helpers ----
    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    # ---- serializer ----
    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "emailVerified": self.email_verified,
            "status": self.status,
            "isAdmin": self.is_admin,
            "createdAt": self.created_at.isoformat() + "Z",
        }
