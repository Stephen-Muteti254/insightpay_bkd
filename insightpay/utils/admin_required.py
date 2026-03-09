from flask_jwt_extended import get_jwt_identity
from flask import jsonify
from functools import wraps
from insightpay.models.user import InsightPayUser


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user = InsightPayUser.query.get(user_id)

        if not user or not user.is_admin:
            return jsonify({"success": False, "message": "Admin access required"}), 403

        return fn(*args, **kwargs)

    return wrapper
