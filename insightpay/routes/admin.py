# app/routes/admin.py

from flask import Blueprint, jsonify
from sqlalchemy import func
from app.extensions import db

from insightpay.models.user import InsightPayUser
from insightpay.models.application import UserApplication
from insightpay.models.survey import Survey
from insightpay.models.insightpay_transaction import InsightPayTransaction
from insightpay.models.survey_attempt import SurveyAttempt

admin_bp = Blueprint("admin", __name__, url_prefix="/api/insightpay/admin")

@admin_bp.get("/dashboard-stats")
def dashboard_stats():

    pending_applications = db.session.query(UserApplication)\
        .filter(UserApplication.status == "submitted").count()

    pending_withdrawals = db.session.query(InsightPayTransaction)\
        .filter(InsightPayTransaction.type == "withdrawal")\
        .filter(InsightPayTransaction.description == "pending")\
        .count()

    active_surveys = db.session.query(Survey)\
        .filter(Survey.is_active == True).count()

    total_users = db.session.query(InsightPayUser).count()

    total_paid_out = db.session.query(
        func.coalesce(func.sum(InsightPayTransaction.amount), 0)
    ).filter(
        InsightPayTransaction.type == "withdrawal"
    ).scalar()

    completed_surveys = db.session.query(SurveyAttempt)\
        .filter(SurveyAttempt.status == "completed").count()

    return jsonify({
        "pendingApplications": pending_applications,
        "pendingWithdrawals": pending_withdrawals,
        "activeSurveys": active_surveys,
        "totalUsers": total_users,
        "totalPaidOut": float(total_paid_out),
        "completedSurveys": completed_surveys
    })


@admin_bp.get("/withdrawals")
def get_withdrawals():

    withdrawals = db.session.query(
        InsightPayTransaction,
        InsightPayUser
    ).join(
        InsightPayUser,
        InsightPayUser.id == InsightPayTransaction.user_id
    ).filter(
        InsightPayTransaction.type == "withdrawal"
    ).order_by(
        InsightPayTransaction.created_at.desc()
    ).all()

    result = []

    for txn, user in withdrawals:
        result.append({
            "id": txn.id,
            "userId": user.id,
            "userName": user.name,
            "userEmail": user.email,
            "paypalEmail": txn.reference_id,  # assuming PayPal stored here
            "amount": float(txn.amount),
            "status": txn.description or "pending",
            "requestedAt": txn.created_at.isoformat(),
        })

    return jsonify(result)


from flask import request

@admin_bp.post("/withdrawals/<txn_id>/action")
def withdrawal_action(txn_id):

    data = request.json
    action = data.get("action")

    txn = InsightPayTransaction.query.get_or_404(txn_id)

    if action == "approve":
        txn.description = "approved"

    elif action == "reject":
        txn.description = "rejected"

    elif action == "paid":
        txn.description = "paid"

    db.session.commit()

    return jsonify({"message": "Withdrawal updated"})