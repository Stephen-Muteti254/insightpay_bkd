from app.extensions import db
from sqlalchemy.sql import func
import uuid

def gen_uuid():
    return str(uuid.uuid4())

class Job(db.Model):
    __tablename__ = "jobs"

    __table_args__ = (
        db.Index("idx_jobs_status", "status"),
        db.Index("idx_jobs_department", "department"),
        db.Index("idx_jobs_location", "location"),
        db.Index("idx_jobs_type", "type"),
        db.Index("idx_jobs_created_at", "created_at"),
    )

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)

    title = db.Column(db.String(255), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)

    type = db.Column(
        db.String(20),
        nullable=False
    )

    salary = db.Column(db.String(100))
    description = db.Column(db.Text, nullable=False)
    who_we_are = db.Column(db.Text)
    what_we_look_for = db.Column(db.Text)

    qualifications = db.Column(db.ARRAY(db.String), default=list, nullable=False)
    responsibilities = db.Column(db.ARRAY(db.String), default=list, nullable=False)

    status = db.Column(
        db.String(20),
        default="draft",
        nullable=False
    )

    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    applications = db.relationship(
        "JobApplication",
        backref="job",
        cascade="all, delete-orphan",
        lazy=True
    )
