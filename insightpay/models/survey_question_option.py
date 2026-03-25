from app.extensions import db
from datetime import datetime
import uuid

class SurveyQuestionOption(db.Model):
    __tablename__ = "insightpay_survey_question_options"

    id = db.Column(db.String(50), primary_key=True, default=lambda: f"opt_{uuid.uuid4()}")

    question_id = db.Column(
        db.String(50),
        db.ForeignKey("insightpay_survey_questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    label = db.Column(db.String(255), nullable=False)

    value = db.Column(db.String(255), nullable=False)

    position = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "label": self.label,
            "value": self.value
        }