from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from insightpay.models.user import InsightPayUser
from insightpay.models.insightpay_transaction import InsightPayTransaction

bp = Blueprint(
    "insightpay_wallet",
    __name__,
    url_prefix="/api/insightpay/wallet"
)


@bp.route("", methods=["GET"])
@jwt_required()
def get_wallet():
    user_id = get_jwt_identity()

    user = InsightPayUser.query.get_or_404(user_id)

    transactions = InsightPayTransaction.query.filter_by(
        user_id=user_id
    ).order_by(InsightPayTransaction.created_at.desc()).limit(50)

    return jsonify({
        "availableBalance": float(user.available_balance),
        "pendingBalance": float(user.pending_balance),
        "transactions": [
            {
                "id": t.id,
                "amount": float(t.amount),
                "type": t.type,
                "status": t.status,
                "description": t.description,
                "createdAt": t.created_at.isoformat()
            } for t in transactions
        ]
    })


@bp.route("/withdraw", methods=["POST"])
@jwt_required()
def withdraw():
    user_id = get_jwt_identity()
    data = request.json or {}

    amount = float(data.get("amount", 0))
    paypal_email = data.get("paypalEmail")

    if not paypal_email:
        return {"message": "PayPal email required"}, 400

    if amount < 5:
        return {"message": "Minimum withdrawal is $5"}, 400

    user = InsightPayUser.query.get_or_404(user_id)

    if amount > float(user.available_balance):
        return {"message": "Insufficient balance"}, 400

    # deduct balance
    user.available_balance -= amount

    txn = InsightPayTransaction(
        user_id=user_id,
        amount=-amount,
        type="withdrawal",
        status="pending",
        description=f"Withdrawal to {paypal_email}"
    )

    db.session.add(txn)
    db.session.commit()

    return {"success": True}