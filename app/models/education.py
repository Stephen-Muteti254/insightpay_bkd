from app.extensions import db
from sqlalchemy.sql import func
import uuid

class Education(db.Model):
    __tablename__ = "education"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    application_id = db.Column(
        db.String(36),
        db.ForeignKey("job_applications.id", ondelete="CASCADE"),
        nullable=False
    )

    institution = db.Column(db.String(255), nullable=False)
    degree = db.Column(db.String(100), nullable=False)
    field = db.Column(db.String(255), nullable=False)

    start_date = db.Column(db.String(7), nullable=False)
    end_date = db.Column(db.String(7))
    is_current = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
