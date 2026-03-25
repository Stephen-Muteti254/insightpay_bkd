from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from insightpay.models.user import InsightPayUser
from insightpay.models.insightpay_transaction import InsightPayTransaction
from app.extensions import db

bp = Blueprint(
    "insightpay_dashboard",
    __name__,
    url_prefix="/api/insightpay/dashboard"
)


@bp.route("", methods=["GET"])
@jwt_required()
def get_dashboard():
    user_id = get_jwt_identity()

    user = InsightPayUser.query.get_or_404(user_id)

    # latest 3 earnings ONLY (exclude withdrawals)
    earnings = (
        InsightPayTransaction.query
        .filter(
            InsightPayTransaction.user_id == user_id,
            InsightPayTransaction.type == "survey_reward"
        )
        .order_by(InsightPayTransaction.created_at.desc())
        .limit(3)
        .all()
    )

    return jsonify({
        "availableBalance": float(user.available_balance),
        "pendingBalance": float(user.pending_balance),
        "recentEarnings": [
            {
                "id": t.id,
                "amount": float(t.amount),
                "status": t.status,
                "description": t.description,
                "createdAt": t.created_at.isoformat()
            } for t in earnings
        ]
    })