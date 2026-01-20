from app.extensions import db
from app.models.job import Job
from app.models.job_application import JobApplication
from app.models.experience import Experience
from app.models.education import Education
from flask import current_app
from werkzeug.utils import secure_filename
import os, uuid, json

def save_career_file(file, folder):
    root = current_app.config.get("CAREERS_UPLOAD_FOLDER")
    os.makedirs(root, exist_ok=True)

    filename = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    path = os.path.join(root, folder)
    os.makedirs(path, exist_ok=True)

    full_path = os.path.join(path, unique_name)
    file.save(full_path)

    return unique_name, full_path


def create_job(data):
    job = Job(
        title=data["title"],
        department=data["department"],
        location=data["location"],
        type=data["type"],
        salary=data.get("salary"),
        description=data["description"],
        who_we_are=data.get("whoWeAre"),
        what_we_look_for=data.get("whatWeLookFor"),
        qualifications=data.get("qualifications", []),
        responsibilities=data.get("responsibilities", []),
        status=data.get("status", "draft")
    )
    db.session.add(job)
    db.session.commit()
    return job


def submit_application(form, files):
    # Save files
    resume = files.get("resume")
    cover = files.get("coverLetter")  # match front-end FormData key

    if not resume or not cover:
        raise ValueError("Resume and cover letter are required")

    resume_name, resume_path = save_career_file(resume, "resumes")
    cover_name, cover_path = save_career_file(cover, "cover_letters")

    # Create main application record
    app = JobApplication(
        job_id=form["job_id"],
        name=form["name"],
        email=form["email"],
        resume_url=resume_path,
        resume_name=resume.filename,
        cover_letter_url=cover_path,
        cover_letter_name=cover.filename,
        status="pending"
    )
    db.session.add(app)
    db.session.flush()  # ensures app.id is populated before adding related records

    # Experiences
    experiences = json.loads(form.get("experiences", "[]"))
    for e in experiences:
        db.session.add(Experience(
            application_id=app.id,
            company=e["company"],
            title=e["title"],
            start_date=e["startDate"],
            end_date=e.get("endDate"),
            is_current=e.get("current", False),
            description=e.get("description")
        ))

    # Education
    education = json.loads(form.get("education", "[]"))
    for ed in education:
        db.session.add(Education(
            application_id=app.id,
            institution=ed["institution"],
            degree=ed["degree"],
            field=ed["field"],
            start_date=ed["startDate"],
            end_date=ed.get("endDate"),
            is_current=ed.get("current", False)
        ))

    db.session.commit()  # commit everything at once

    return app
