from flask import Blueprint, request, current_app, render_template
from datetime import datetime
from app.utils.exceptions import ServiceError

from app.services.auth_service import (
    register_user,
    authenticate_user,
    generate_tokens_for_user,
    build_account_state
)

from app.utils.response_formatter import success_response, error_response
from app.extensions import db, jwt
from app.models.user import User
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
    unset_jwt_cookies
)

from app.utils.auth_utils import hash_password, check_password
from app.utils.email_tokens import generate_email_verification_token
from app.services.email_service import (
    send_verification_email,
    send_login_otp_email
)
from app.utils.email_tokens import decode_email_verification_token
from app.models.login_otp import LoginOTP
from app.utils.otp import (
    generate_otp,
    hash_otp,
    verify_otp,
    otp_expiry
    )


bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")

@bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    full_name = data.get("full_name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "writer")
    country = data.get("country")
    phone = data.get("phone")

    if not role in ("client", "writer"):
        return error_response("VALIDATION_ERROR", f"Could not register {role}", status=403)

    if not all([full_name, email, password]):
        return error_response("VALIDATION_ERROR", "Missing required fields", status=422)

    try:
        user = register_user(email, password, full_name, role=role, country=country)
        token = generate_email_verification_token(user.id)
        send_verification_email(user, token)
        access, refresh = generate_tokens_for_user(user)
        return success_response({
            "user": {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "role": user.role,
                "application_status": user.application_status,
                "is_verified": user.is_verified,
            },
            "access_token": access,
            "refresh_token": refresh
        }, status=200)
    except Exception as e:
        return error_response("USER_REGISTER_ERROR", str(e), status=400)


@bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    try:
        user = authenticate_user(email, password)
    except ServiceError as e:
        return error_response(e.code, e.message, status=401)

    otp = generate_otp()

    print(f"otp = {otp}")

    otp_record = LoginOTP(
        user_id=user.id,
        otp_hash=hash_otp(otp),
        expires_at=otp_expiry(),
    )

    db.session.add(otp_record)
    db.session.commit()

    send_login_otp_email(user, otp)

    return success_response({
        "otp_required": True,
        "otp_session_id": otp_record.id,
        "message": "OTP sent to your email"
    })


@bp.route("/login/verify-otp", methods=["POST"])
def verify_login_otp():
    data = request.get_json() or {}
    otp = data.get("otp")
    session_id = data.get("otp_session_id")

    record = LoginOTP.query.get(session_id)

    if not record or record.used or record.is_expired():
        return error_response("INVALID_OTP", "OTP expired or invalid", 400)

    if record.attempts >= 5:
        return error_response("LOCKED", "Too many attempts", 403)

    if not verify_otp(otp, record.otp_hash):
        record.attempts += 1
        db.session.commit()
        return error_response("INVALID_OTP", "Incorrect OTP", 400)

    record.used = True
    db.session.commit()

    user = User.query.get(record.user_id)
    access, refresh = generate_tokens_for_user(user)

    return success_response({
        "access_token": access,
        "refresh_token": refresh,
        "user": user.to_dict(),
    })


@bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    resp = success_response({"message": "Successfully logged out"})
    # unset cookies if you were using cookies; client should discard tokens.
    response, status = resp
    # NOTE: flask-jwt-extended provides helper to unset cookies if stored in cookies
    # Here we'll just return message; clients should delete tokens client-side
    return success_response({"message": "Successfully logged out"})

@bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    uid = get_jwt_identity()
    user = User.query.get(uid)

    if not user:
        return error_response("NOT_FOUND", "User not found", 404)

    account_state = build_account_state(user)

    return success_response({
        **user.to_dict(),
        "account_state": account_state,
    })


@bp.route("/verify-email", methods=["POST"])
def verify_email():
    data = request.get_json() or {}
    token = data.get("token")

    if not token:
        return error_response(
            code="MISSING_TOKEN",
            message="Verification token is required",
            status=400
        )

    try:
        user_id = decode_email_verification_token(token)
    except Exception:
        return error_response(
            code="INVALID_TOKEN",
            message="Verification link is invalid or expired",
            status=400
        )

    user = User.query.get(user_id)
    print(f"user_id = {user_id}")
    if not user:
        return error_response(
            code="USER_NOT_FOUND",
            message="User not found",
            status=404
        )

    if not user.is_verified:
        user.is_verified = True
        db.session.commit()

    return success_response(
        payload={"verified": True},
        message="Email successfully verified",
        status=200
    )


@bp.route("/resend-verification", methods=["POST"])
@jwt_required()
def resend_verification():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return error_response("NOT_FOUND", "User not found", 404)

    if user.is_verified:
        return error_response(
            "ALREADY_VERIFIED",
            "Email is already verified",
            400
        )

    # OPTIONAL (recommended): rate limit resend
    if user.last_verification_sent_at:
        delta = (datetime.utcnow() - user.last_verification_sent_at).total_seconds()
        if delta < 60:
            return error_response(
                "RATE_LIMITED",
                "Please wait before requesting another verification email",
                429
            )

    token = generate_email_verification_token(user.id)
    send_verification_email(user, token)

    user.last_verification_sent_at = datetime.utcnow()
    db.session.commit()

    return success_response(
        message="Verification email resent successfully"
    )
