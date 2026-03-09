from app.extensions import db
from datetime import datetime
import uuid

def gen_uuid(prefix="srv"):
    return f"{prefix}_{uuid.uuid4()}"

class SurveyAttempt(db.Model):
    __tablename__ = "insightpay_survey_attempts"

    id = db.Column(db.String(50), primary_key=True, default=gen_uuid)

    user_id = db.Column(
        db.String(50),
        db.ForeignKey("insightpay_users.id"),
        nullable=False
    )

    survey_id = db.Column(
        db.String(50),
        db.ForeignKey("insightpay_surveys.id"),
        nullable=False
    )

    started_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)

    completed_at = db.Column(db.DateTime)
    status = db.Column(db.String(20), default="active", index=True)

    reward_snapshot = db.Column(db.Numeric(10, 2), nullable=False)

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "survey_id",
            name="uq_user_survey_once"
        ),
    )

    def duration_seconds(self):
        if not self.completed_at:
            return None
        return (self.completed_at - self.started_at).total_seconds()
