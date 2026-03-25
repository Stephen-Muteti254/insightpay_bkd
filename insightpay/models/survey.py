from app.extensions import db
from datetime import datetime, timedelta, timezone
import uuid


def gen_uuid(prefix="srv"):
    return f"{prefix}_{uuid.uuid4()}"

def format_datetime(dt):
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


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
    # external_url = db.Column(db.Text, nullable=False)
    questions = db.relationship(
        "SurveyQuestion",
        cascade="all, delete-orphan",
        backref="survey",
        order_by="SurveyQuestion.position"
    )

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
            "questions": [q.to_dict() for q in self.questions],
            "isActive": self.is_active,
            "createdAt": self.created_at.isoformat() + "Z",
            "expiresAt": format_datetime(self.expires_at),
            "attachments": [a.to_dict() for a in self.attachments],
        }
