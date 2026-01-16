from app.extensions import db
from datetime import datetime
import uuid

def gen_uuid(prefix=None):
    uid = str(uuid.uuid4())
    return f"{prefix}-{uid}" if prefix else uid

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.String(50), primary_key=True, default=lambda: gen_uuid("usr"))
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255))
    role = db.Column(db.String(50), nullable=False, default="unknown")
    profile_image = db.Column(db.String(1024), nullable=True)
    rating = db.Column(db.Float, default=0.0)
    completed_orders = db.Column(db.Integer, default=0)
    bio = db.Column(db.Text, nullable=True)
    total_earned = db.Column(db.Float, default=0.0)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    application_status = db.Column(db.String(50), default="not_applied")
    is_verified = db.Column(db.Boolean, default=False)
    country = db.Column(db.String(100), nullable=True)
    account_status = db.Column(db.String(50), default="awaiting_initial_deposit")
    last_verification_sent_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role,
            "profile_image": self.profile_image,
            "rating": self.rating,
            "completed_orders": self.completed_orders,
            "bio": self.bio,
            "total_earned": self.total_earned,
            "country": self.country,
            "joined_at": self.joined_at.isoformat() + "Z" if self.joined_at else None,
            "is_verified": self.is_verified,
            "account_status": self.account_status,
            "application_status": self.application_status,
        }
