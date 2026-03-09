from app.extensions import db
from datetime import datetime
import uuid

def gen_app_id():
    return f"app_{uuid.uuid4()}"

class UserApplication(db.Model):
    __tablename__ = "insightpay_applications"

    id = db.Column(db.String(50), primary_key=True, default=gen_app_id)
    user_id = db.Column(
        db.String(50),
        db.ForeignKey("insightpay_users.id"),
        nullable=False,
        unique=True
    )

    answers = db.Column(db.JSON, nullable=False)

    status = db.Column(
        db.String(50),
        default="submitted",
        nullable=False
    )

    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)

    user = db.relationship("InsightPayUser", backref="application", uselist=False)
