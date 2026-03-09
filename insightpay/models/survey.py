from app.extensions import db
from datetime import datetime
import uuid


def gen_uuid(prefix="srv"):
    return f"{prefix}_{uuid.uuid4()}"


class Survey(db.Model):
    __tablename__ = "insightpay_surveys"

    id = db.Column(db.String(50), primary_key=True, default=gen_uuid)
    title = db.Column(db.String(255), nullable=False)
    topic = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    duration_minutes = db.Column(db.Integer, nullable=False)
    reward = db.Column(db.Numeric(10, 2), nullable=False)
    total_slots = db.Column(db.Integer, nullable=False)
    slots_remaining = db.Column(db.Integer, nullable=False)
    external_url = db.Column(db.Text, nullable=False)

    is_active = db.Column(db.Boolean, default=True)

    created_by = db.Column(
        db.String(50),
        db.ForeignKey("insightpay_users.id"),
        nullable=False
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)

    attachments = db.relationship(
        "SurveyAttachment",
        backref="survey",
        cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "topic": self.topic,
            "description": self.description,
            "durationMinutes": self.duration_minutes,
            "reward": float(self.reward),
            "totalSlots": self.total_slots,
            "slotsRemaining": self.slots_remaining,
            "externalUrl": self.external_url,
            "isActive": self.is_active,
            "createdAt": self.created_at.isoformat() + "Z",
            "expiresAt": self.expires_at.isoformat() + "Z" if self.expires_at else None,
            "attachments": [a.to_dict() for a in self.attachments],
        }
