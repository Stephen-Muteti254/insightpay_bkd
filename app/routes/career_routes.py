from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from app.models.job import Job
from app.models.job_application import JobApplication
from app.services.career_service import create_job, submit_application
from app.utils.response_formatter import success_response, error_response
from app.utils.pagination import paginate_query
from sqlalchemy import or_, cast
from sqlalchemy.types import String
from app.extensions import db

bp = Blueprint("careers", __name__, url_prefix="/api/v1")


@bp.route("/jobs", methods=["GET"])
def list_jobs():
    q = Job.query.filter(Job.status == "active")

    search = request.args.get("search")
    if search:
        s = f"%{search.lower()}%"
        q = q.filter(
            or_(
                Job.title.ilike(s),
                Job.department.ilike(s),
                Job.description.ilike(s)
            )
        )

    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 10, type=int)

    items, pagination = paginate_query(q.order_by(Job.created_at.desc()), page, limit)

    jobs = [{
	    "id": j.id,
	    "title": j.title,
	    "department": j.department,
	    "location": j.location,
	    "type": j.type,
	    "salary": j.salary,
	    "status": j.status,
	    "createdAt": j.created_at.isoformat() + "Z",
	    "qualifications": j.qualifications or [],
	    "responsibilities": j.responsibilities or [],
        "whoWeAre": j.who_we_are or "",
        "whatWeLookFor": j.what_we_look_for or "",
        "description": j.description
	} for j in items]

    return success_response({
        "jobs": jobs,
        "pagination": pagination
    })


@bp.route("/jobs", methods=["POST"])
def create_job_route():
    data = request.get_json()
    if not data:
        return error_response("VALIDATION_ERROR", "Invalid payload", status=400)

    job = create_job(data)
    return success_response({"id": job.id}, status=201)



@bp.route("/applications", methods=["POST"])
def apply():
    if not request.files:
    	print("request files error")
    	return error_response("VALIDATION_ERROR", "Files required", status=400)

    try:
        app = submit_application(request.form, request.files)
        return success_response({
            "id": app.id,
            "status": app.status,
            "submittedAt": app.submitted_at.isoformat() + "Z"
        }, status=201)
    except Exception as e:
    	print(f"error = {str(e)}")
    	return error_response("APPLICATION_ERROR", str(e), status=400)


@bp.route("/jobs/<job_id>", methods=["GET"])
def get_job(job_id):
    job = Job.query.get(job_id)
    if not job:
        return error_response("NOT_FOUND", "Job not found", status=404)

    job_data = {
        "id": job.id,
        "title": job.title,
        "department": job.department,
        "location": job.location,
        "type": job.type,
        "salary": job.salary,
        "status": job.status,
        "whoWeAre": job.who_we_are,
        "whatWeLookFor": job.what_we_look_for,
        "qualifications": job.qualifications,
        "responsibilities": job.responsibilities,
        "createdAt": job.created_at.isoformat() + "Z",
        "description": job.description
    }
    return success_response({"job": job_data})



@bp.route("/applications", methods=["GET"])
def list_applications():
    q = JobApplication.query

    # ---- filters ----
    search = request.args.get("search")
    status = request.args.get("status")

    if status and status != "all":
        q = q.filter(JobApplication.status == status)

    if search:
        s = f"%{search.lower()}%"
        q = q.join(Job).filter(
            or_(
                cast(JobApplication.first_name, String).ilike(s),
                cast(JobApplication.last_name, String).ilike(s),
                JobApplication.email.ilike(s),
                Job.title.ilike(s),
            )
        )

    # ---- pagination ----
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 10, type=int)

    items, pagination = paginate_query(
        q.order_by(JobApplication.submitted_at.desc()),
        page,
        limit
    )

    applications = []
    for app in items:
        applications.append({
            "id": app.id,
            "name": app.name,
            "email": app.email,
            "jobTitle": app.job.title if app.job else "",
            "status": app.status,
            "submittedAt": app.submitted_at.isoformat() + "Z",

            "resumeName": app.resume_url,
            "coverLetterName": app.cover_letter_url,

            "experiences": [
                {
                    "id": e.id,
                    "title": e.title,
                    "company": e.company,
                    "startDate": e.start_date,
                    "endDate": e.end_date,
                    "current": e.is_current,
                    "description": e.description
                }
                for e in app.experiences
            ],

            "education": [
                {
                    "id": edu.id,
                    "institution": edu.institution,
                    "degree": edu.degree,
                    "field": edu.field,
                    "startDate": edu.start_date,
                    "endDate": edu.end_date,
                    "current": edu.is_current
                }
                for edu in app.education
            ]
        })

    return success_response({
        "applications": applications,
        "pagination": pagination
    })


@bp.route("/jobs/<job_id>", methods=["PUT"])
def update_job(job_id):
    job = Job.query.get(job_id)
    if not job:
        return error_response("NOT_FOUND", "Job not found", status=404)

    data = request.get_json()
    if not data:
        return error_response("VALIDATION_ERROR", "Invalid payload", status=400)

    # Update fields if present
    job.title = data.get("title", job.title)
    job.department = data.get("department", job.department)
    job.location = data.get("location", job.location)
    job.type = data.get("type", job.type)
    job.salary = data.get("salary", job.salary)
    job.description = data.get("description", job.description)
    job.who_we_are = data.get("whoWeAre", job.who_we_are)
    job.what_we_look_for = data.get("whatWeLookFor", job.what_we_look_for)
    job.qualifications = data.get("qualifications", job.qualifications)
    job.responsibilities = data.get("responsibilities", job.responsibilities)
    job.status = data.get("status", job.status)

    db.session.commit()

    return success_response({
        "id": job.id,
        "updatedAt": job.updated_at.isoformat() + "Z" if job.updated_at else None
    })


@bp.route("/jobs/<job_id>", methods=["DELETE"])
def delete_job(job_id):
    job = Job.query.get(job_id)
    if not job:
        return error_response("NOT_FOUND", "Job not found", status=404)

    try:
        db.session.delete(job)
        db.session.commit()
        return success_response({"message": f"Job {job_id} deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return error_response("DELETE_ERROR", str(e), status=500)
