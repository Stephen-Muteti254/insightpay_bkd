# app/routes/auth_routes.py
from flask import Blueprint, request, jsonify
from insightpay.services.auth_service import AuthService
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from werkzeug.exceptions import BadRequest, HTTPException
from insightpay.models.user import InsightPayUser

bp = Blueprint("insightpay_auth", __name__, url_prefix="/api/insightpay/auth")


@bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")
    name = data.get("name")

    if not all([email, password, name]):
        return jsonify({
            "success": False,
            "message": "Email, password and name are required"
        }), 400

    try:
        result = AuthService.register_user(email=email, password=password, name=name)

        # Send verification email
        user = InsightPayUser.query.get(result["user"]["id"])
        AuthService.send_verification(user)

    except HTTPException as he:
        return jsonify({
            "success": False,
            "message": he.description
        }), he.code or 400
    except Exception as e:
        print("Unexpected registration error:", e)
        return jsonify({
            "success": False,
            "message": "Server error. Please try again later."
        }), 500

    return jsonify({
        "success": True,
        "data": result
    }), 201

@bp.route("/verify-email", methods=["POST"])
@jwt_required()
def verify_email():
    data = request.get_json() or {}
    otp = data.get("code")

    if not otp or len(otp) != 6:
        return jsonify({"success": False, "message": "Invalid OTP"}), 400

    # Get user ID from JWT token
    user_id = get_jwt_identity()
    if not user_id:
        return jsonify({"success": False, "message": "User not authenticated"}), 401

    # Fetch the user from DB
    user = InsightPayUser.query.get(user_id)
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404

    try:
        success = AuthService.verify_email(user, otp)
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400

    return jsonify({
        "success": success,
        "data": {
            "user": user.to_dict()
        }
    })


@bp.route("/resend-verification", methods=["POST"])
@jwt_required()
def resend_verification():
    # Get user ID from JWT
    user_id = get_jwt_identity()
    if not user_id:
        return jsonify({"success": False, "message": "User not authenticated"}), 401

    # Fetch the user from the database
    user = InsightPayUser.query.get(user_id)
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404

    # If already verified, just return success
    if user.email_verified:
        return jsonify({"success": True, "message": "Email already verified"}), 200

    try:
        print(f"user to receive verification = {user}")
        AuthService.send_verification(user)
    except Exception as e:
        # Catch any issues during OTP creation or email sending
        return jsonify({"success": False, "message": f"Failed to send verification code: {str(e)}"}), 500

    return jsonify({"success": True, "message": "Verification code sent"})


@bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"success": False, "message": "Email and password required"}), 400

    user = InsightPayUser.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"success": False, "message": "Invalid credentials"}), 401

    token = create_access_token(identity=user.id)

    return jsonify({
        "success": True,
        "data": {
            "user": user.to_dict(),
            "token": token
        }
    }), 200
