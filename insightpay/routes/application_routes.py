from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from insightpay.models.user import InsightPayUser
from insightpay.models.application import UserApplication
from app.extensions import db
from werkzeug.exceptions import BadRequest
from datetime import datetime

bp = Blueprint(
    "insightpay_applications",
    __name__,
    url_prefix="/api/insightpay/application"
)


def admin_required(user: InsightPayUser):
    if not user or not user.is_admin:
        return jsonify({"message": "Admin access required"}), 403


@bp.route("/submit", methods=["POST"])
@jwt_required()
def submit_application():
    user_id = get_jwt_identity()
    user = InsightPayUser.query.get(user_id)

    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404

    if user.status != "email_verified":
        return jsonify({
            "success": False,
            "message": "Email must be verified first"
        }), 403

    if user.application:
        raise BadRequest("Application already submitted")

    data = request.get_json() or {}
    if not data:
        raise BadRequest("Application answers required")

    application = UserApplication(
        user_id=user.id,
        answers=data
    )

    user.status = "application_submitted"
    user.application_submitted_at = datetime.utcnow()

    db.session.add(application)
    db.session.commit()

    return jsonify({"success": True}), 201


@bp.route("/admin/all", methods=["GET"])
@jwt_required(optional=True)
def get_all_applications():
    print("IDENTITY:", get_jwt_identity())
    admin_id = get_jwt_identity()
    admin = InsightPayUser.query.get(admin_id)

    admin_check = admin_required(admin)
    if admin_check:
        return admin_check

    applications = (
        db.session.query(UserApplication, InsightPayUser)
        .join(InsightPayUser, UserApplication.user_id == InsightPayUser.id)
        .order_by(UserApplication.submitted_at.desc())
        .all()
    )

    results = []
    for app, user in applications:
        results.append({
            "id": app.id,
            "userId": user.id,
            "userName": user.name,
            "userEmail": user.email,
            "status": app.status,
            "submittedAt": app.submitted_at.isoformat() + "Z",
            "answers": app.answers,
        })

    return jsonify({"applications": results}), 200


@bp.route("/admin/<application_id>/approve", methods=["POST"])
@jwt_required()
def approve_application(application_id):
    admin_id = get_jwt_identity()
    admin = InsightPayUser.query.get(admin_id)

    admin_check = admin_required(admin)
    if admin_check:
        return admin_check

    application = UserApplication.query.get(application_id)
    if not application:
        return jsonify({"message": "Application not found"}), 404

    if application.status != "submitted":
        return jsonify({"message": "Application already processed"}), 400

    application.status = "approved"
    application.reviewed_at = datetime.utcnow()

    user = InsightPayUser.query.get(application.user_id)
    user.status = "application_approved"

    db.session.commit()

    return jsonify({"success": True}), 200


@bp.route("/admin/<application_id>/reject", methods=["POST"])
@jwt_required()
def reject_application(application_id):
    admin_id = get_jwt_identity()
    admin = InsightPayUser.query.get(admin_id)

    admin_check = admin_required(admin)
    if admin_check:
        return admin_check

    data = request.get_json() or {}
    rejection_reason = data.get("reason")

    application = UserApplication.query.get(application_id)
    if not application:
        return jsonify({"message": "Application not found"}), 404

    if application.status != "submitted":
        return jsonify({"message": "Application already processed"}), 400

    application.status = "rejected"
    application.reviewed_at = datetime.utcnow()

    user = InsightPayUser.query.get(application.user_id)
    user.status = "application_rejected"

    # optional: store rejection reason later

    db.session.commit()

    return jsonify({"success": True}), 200
