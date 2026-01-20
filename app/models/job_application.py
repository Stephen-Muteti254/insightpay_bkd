from app.extensions import db
from sqlalchemy.sql import func
import uuid

def gen_uuid():
    return str(uuid.uuid4())

class JobApplication(db.Model):
    __tablename__ = "job_applications"

    __table_args__ = (
        db.Index("idx_applications_job_id", "job_id"),
        db.Index("idx_applications_status", "status"),
        db.Index("idx_applications_submitted_at", "submitted_at"),
    )

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)

    job_id = db.Column(
        db.String(36),
        db.ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False
    )

    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)

    resume_url = db.Column(db.Text, nullable=False)
    resume_name = db.Column(db.String(255), nullable=False)

    cover_letter_url = db.Column(db.Text, nullable=False)
    cover_letter_name = db.Column(db.String(255), nullable=False)

    status = db.Column(
        db.String(20),
        default="pending",
        nullable=False
    )

    submitted_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    experiences = db.relationship(
        "Experience",
        cascade="all, delete-orphan",
        backref="application",
        lazy=True
    )

    education = db.relationship(
        "Education",
        cascade="all, delete-orphan",
        backref="application",
        lazy=True
    )
