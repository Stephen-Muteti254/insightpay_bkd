from app.extensions import db
from datetime import datetime
import uuid


class SurveyResponse(db.Model):
    __tablename__ = "insightpay_survey_responses"

    id = db.Column(db.String(50), primary_key=True, default=lambda: f"res_{uuid.uuid4()}")

    attempt_id = db.Column(
        db.String(50),
        db.ForeignKey("insightpay_survey_attempts.id"),
        nullable=False,
        index=True
    )

    question_id = db.Column(
        db.String(50),
        db.ForeignKey("insightpay_survey_questions.id"),
        nullable=False
    )

    option_id = db.Column(
        db.String(50),
        db.ForeignKey("insightpay_survey_question_options.id"),
        nullable=True
    )

    answer = db.Column(db.JSON)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)