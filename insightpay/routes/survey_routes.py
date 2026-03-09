from flask import (
    Blueprint,
    request,
    jsonify,
    send_from_directory,
    current_app,
    abort,
)
from flask_jwt_extended import jwt_required, get_jwt_identity
from insightpay.services.survey_service import SurveyService
from insightpay.models.survey import Survey
from insightpay.utils.admin_required import admin_required
from datetime import datetime, timedelta
from app.extensions import db
from insightpay.models.survey_attempt import SurveyAttempt
from insightpay.models.user import InsightPayUser

bp = Blueprint(
    "insightpay_surveys",
    __name__,
    url_prefix="/api/insightpay/admin/surveys"
)


@bp.route("", methods=["GET"])
@jwt_required()
@admin_required
def list_surveys():
    surveys = SurveyService.list_surveys()
    return jsonify({
        "success": True,
        "data": [s.to_dict() for s in surveys]
    })


@bp.route("", methods=["POST"])
@jwt_required()
@admin_required
def create_survey():
    data = request.form.to_dict()
    files = request.files.getlist("attachments")
    admin_id = get_jwt_identity()

    survey = SurveyService.create_survey(data, files, admin_id)
    return jsonify({
        "success": True,
        "data": survey.to_dict()
    }), 201


@bp.route("/<survey_id>", methods=["PUT"])
@jwt_required()
@admin_required
def update_survey(survey_id):
    survey = Survey.query.get_or_404(survey_id)
    data = request.get_json()

    survey = SurveyService.update_survey(survey, data)
    return jsonify({
        "success": True,
        "data": survey.to_dict()
    })


@bp.route("/<survey_id>", methods=["DELETE"])
@jwt_required()
@admin_required
def delete_survey(survey_id):
    survey = Survey.query.get_or_404(survey_id)
    SurveyService.delete_survey(survey)

    return jsonify({"success": True})


user_surveys_bp = Blueprint(
    "insightpay_user_surveys",
    __name__,
    url_prefix="/api/insightpay/surveys"
)

@user_surveys_bp.route("/<survey_id>/complete", methods=["POST"])
@jwt_required()
def complete_survey(survey_id):
    user_id = get_jwt_identity()
    now = datetime.utcnow()

    attempt = (
        SurveyAttempt.query
        .filter_by(
            user_id=user_id,
            survey_id=survey_id,
            status="active"
        )
        .first_or_404()
    )

    if now > attempt.expires_at:
        attempt.status = "expired"

        survey = Survey.query.get(survey_id)
        survey.slots_remaining += 1

        db.session.commit()
        abort(400, "Survey time expired")

    attempt.status = "completed"
    attempt.completed_at = now

    # credit reward
    user = InsightPayUser.query.get_or_404(user_id)
    user.pending_balance += attempt.reward_snapshot

    db.session.commit()

    return jsonify({
        "success": True,
        "data": {
            "rewardCredited": float(attempt.reward_snapshot)
        }
    })


@user_surveys_bp.route("/<survey_id>/start", methods=["POST"])
@jwt_required()
def start_survey(survey_id):
    user_id = get_jwt_identity()

    # Check if already attempted
    existing_attempt = SurveyAttempt.query.filter_by(
        user_id=user_id,
        survey_id=survey_id
    ).first()

    if existing_attempt:
        abort(400, "You have already attempted this survey.")

    survey = (
        Survey.query
        .filter_by(id=survey_id, is_active=True)
        .with_for_update()
        .first_or_404()
    )

    if survey.slots_remaining <= 0:
        abort(400, "No slots remaining")

    now = datetime.utcnow()
    expires_at = now + timedelta(minutes=survey.duration_minutes)

    survey.slots_remaining -= 1

    attempt = SurveyAttempt(
        user_id=user_id,
        survey_id=survey.id,
        expires_at=expires_at,
        reward_snapshot=survey.reward
    )

    db.session.add(attempt)
    db.session.commit()

    return jsonify({
        "success": True,
        "attempt": {
            "expiresAt": expires_at.isoformat() + "Z"
        }
    })


@user_surveys_bp.route("/public", methods=["GET"])
@jwt_required()
def list_active_surveys():
    user_id = get_jwt_identity()
    surveys = SurveyService.list_active_surveys_for_users(user_id)
    return jsonify({
        "success": True,
        "data": [s.to_dict() for s in surveys]
    })

@user_surveys_bp.route("/attachments/<path:filename>", methods=["GET"])
@jwt_required()
def get_survey_attachment(filename):
    root = current_app.config["UPLOAD_ROOT"]
    return send_from_directory(root, filename, as_attachment=False)


@user_surveys_bp.route("/<survey_id>", methods=["GET"])
@jwt_required()
def get_survey(survey_id):
    survey = Survey.query.filter_by(
        id=survey_id,
        is_active=True
    ).first_or_404()

    return jsonify({
        "success": True,
        "data": survey.to_dict()
    })