from app.extensions import db
from datetime import datetime
import uuid

class SurveyQuestion(db.Model):
    __tablename__ = "insightpay_survey_questions"

    id = db.Column(db.String(50), primary_key=True, default=lambda: f"q_{uuid.uuid4()}")

    survey_id = db.Column(
        db.String(50),
        db.ForeignKey("insightpay_surveys.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    question_text = db.Column(db.Text, nullable=False)

    question_type = db.Column(db.String(50), nullable=False)

    help_text = db.Column(db.Text)

    required = db.Column(db.Boolean, default=True)

    position = db.Column(db.Integer, default=0)

    min_value = db.Column(db.Integer)
    max_value = db.Column(db.Integer)

    max_length = db.Column(db.Integer)

    randomize_options = db.Column(db.Boolean, default=False)

    options = db.relationship(
        "SurveyQuestionOption",
        cascade="all, delete-orphan",
        backref="question"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "text": self.question_text,
            "type": self.question_type,
            "required": self.required,
            "position": self.position,
            "options": [o.to_dict() for o in self.options]
        }