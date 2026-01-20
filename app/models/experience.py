from app.extensions import db
from sqlalchemy.sql import func
import uuid

class Experience(db.Model):
    __tablename__ = "experiences"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    application_id = db.Column(
        db.String(36),
        db.ForeignKey("job_applications.id", ondelete="CASCADE"),
        nullable=False
    )

    company = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(255), nullable=False)

    start_date = db.Column(db.String(7), nullable=False)
    end_date = db.Column(db.String(7))
    is_current = db.Column(db.Boolean, default=False)

    description = db.Column(db.Text)

    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
