from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from app.utils.response_formatter import success_response, error_response
from app.models.payment_method import PaymentMethod
from app.extensions import db

from decimal import Decimal
import requests, uuid
import hmac
import hashlib
from datetime import datetime

from app.models.wallet import Wallet
from app.models.wallet_transaction import WalletTransaction
from app.models.withdrawal_request import WithdrawalRequest
from app.models.order import Order
from app.models.order_payment import OrderPayment

from app.services.wallet_service import credit_wallet

bp = Blueprint("payments", __name__, url_prefix="/api/v1")


def gen_uuid(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


@bp.route("/balance", methods=["GET"])
@jwt_required()
def balance():
    uid = get_jwt_identity()
    wallet = Wallet.query.filter_by(user_id=uid).first()
    return success_response({
        "balance": float(wallet.balance) if wallet else 0.0,
        "currency": wallet.currency if wallet else "USD"
    })


@bp.route("/transactions", methods=["GET"])
@jwt_required()
def transactions():
    uid = get_jwt_identity()
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))

    wallet = Wallet.query.filter_by(user_id=uid).first()
    if not wallet:
        return success_response({"transactions": [], "pagination": {}})

    q = WalletTransaction.query.filter_by(wallet_id=wallet.id)

    total = q.count()
    items = (
        q.order_by(WalletTransaction.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return success_response({
        "transactions": [
            {
                "id": t.id,
                "type": t.type,
                "amount": float(t.amount),
                "reference_type": t.reference_type,
                "reference_id": t.reference_id,
                "description": t.description,
                "created_at": t.created_at.isoformat() + "Z"
            }
            for t in items
        ],
        "pagination": {
            "total": total,
            "page": page,
            "limit": limit
        }
    })


@bp.route("/withdrawals", methods=["POST"])
@jwt_required()
def request_withdrawal():
    uid = get_jwt_identity()
    data = request.get_json() or {}

    amount = Decimal(str(data.get("amount")))
    method = data.get("payment_method")
    destination = data.get("payment_details")

    wallet = Wallet.query.filter_by(user_id=uid).first()

    wallet = (
        Wallet.query
        .filter_by(user_id=uid)
        .with_for_update()
        .first()
    )
    if not wallet or wallet.balance < amount:
        return error_response("INSUFFICIENT_FUNDS", "Not enough balance", 400)

    wr = WithdrawalRequest(
        id=gen_uuid("wd"),
        user_id=uid,
        amount=amount,
        method=method,
        destination=destination
    )

    db.session.add(wr)
    db.session.commit()

    return success_response({
        "id": wr.id,
        "status": wr.status,
        "amount": float(wr.amount)
    }, status=201)


@bp.route("/withdrawals", methods=["GET"])
@jwt_required()
def list_withdrawals():
    uid = get_jwt_identity()
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))

    q = WithdrawalRequest.query.filter_by(user_id=uid)

    total = q.count()
    items = (
        q.order_by(WithdrawalRequest.requested_at.desc())
         .offset((page - 1) * limit)
         .limit(limit)
         .all()
    )

    return success_response({
        "withdrawals": [
            {
                "id": w.id,
                "amount": float(w.amount),
                "status": w.status,
                "method": w.method,
                "destination": w.destination,
                "requested_at": w.requested_at.isoformat() + "Z",
                "processed_at": (
                    w.processed_at.isoformat() + "Z"
                    if w.processed_at else None
                )
            }
            for w in items
        ],
        "pagination": {
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit
        }
    })


@bp.route("/payment-methods", methods=["POST"])
@jwt_required()
def add_payment_method():
    from app.models.payment_method import PaymentMethod

    data = request.get_json() or {}
    print(f"incoming data = {data}")
    method = data.get("method")
    details = data.get("details")
    is_default = data.get("is_default", False)

    if not method or not details:
        return error_response("VALIDATION_ERROR", "Method and details are required")

    uid = get_jwt_identity()

    # If default: unset other defaults
    if is_default:
        PaymentMethod.query.filter_by(user_id=uid, is_default=True).update({"is_default": False})

    pm = PaymentMethod(
        user_id=uid,
        method=method,
        details=details,
        is_default=is_default
    )

    db.session.add(pm)
    db.session.commit()

    return success_response({"id": pm.id}, "Payment method added", status=201)


@bp.route("/payment-methods/<pm_id>/default", methods=["PATCH"])
@jwt_required()
def set_default(pm_id):
    from app.models.payment_method import PaymentMethod
    uid = get_jwt_identity()

    pm = PaymentMethod.query.filter_by(id=pm_id, user_id=uid).first()
    if not pm:
        return error_response("NOT_FOUND", "Payment method not found", status=404)

    # Reset defaults
    PaymentMethod.query.filter_by(user_id=uid).update({"is_default": False})

    pm.is_default = True
    db.session.commit()

    return success_response({"message": "Default method updated"})



@bp.route("/payment-methods", methods=["GET"])
@jwt_required()
def list_payment_methods():
    uid = get_jwt_identity()
    methods = PaymentMethod.query.filter_by(user_id=uid).all()

    return success_response([
        {
            "id": m.id,
            "method": m.method,
            "details": m.details,
            "is_default": m.is_default
        } for m in methods
    ])


@bp.route("/payment-methods/<pm_id>", methods=["PATCH"])
@jwt_required()
def update_payment_method(pm_id):
    data = request.get_json() or {}
    new_details = data.get("details")

    if not new_details:
        return error_response("VALIDATION_ERROR", "Details are required")

    uid = get_jwt_identity()

    pm = PaymentMethod.query.filter_by(id=pm_id, user_id=uid).first()
    if not pm:
        return error_response("NOT_FOUND", "Payment method not found", status=404)

    pm.details = new_details
    db.session.commit()

    return success_response({"message": "Payment method updated"})


@bp.route("/init", methods=["POST"])
@jwt_required()
def init_order_payment():
    uid = get_jwt_identity()
    data = request.get_json() or {}

    order_id = data.get("order_id")
    order = Order.query.get(order_id)

    if not order or order.client_id != uid:
        return error_response("FORBIDDEN", "Invalid order", 403)

    if order.payment_status == "paid":
        return error_response("ALREADY_PAID", "Order already paid", 400)

    amount_usd = order.client_budget

    reference = f"order_{order.id}_{uuid.uuid4().hex[:8]}"

    payment = OrderPayment(
        order_id=order.id,
        client_id=uid,
        reference=reference,
        amount_usd=amount_usd,
        status="pending"
    )

    db.session.add(payment)
    db.session.commit()

    return success_response({
        "public_key": current_app.config["PAYSTACK_PUBLIC_KEY"],
        "email": order.client.email,
        "amount": amount_usd,
        "currency": "USD",
        "reference": reference,
        "callback_url": current_app.config["PAYSTACK_CALLBACK_URL"],
        "metadata": {
            "order_id": order.id,
            "payment_id": payment.id,
            "client_id": uid,
            "usd_amount": amount_usd
        }
    })


@bp.route("/webhooks/paystack", methods=["POST"])
def handle_paystack_webhook():
    secret = current_app.config["PAYSTACK_SECRET_KEY"]
    signature = request.headers.get("x-paystack-signature")
    body = request.get_data()

    # Verify signature
    computed = hmac.new(secret.encode(), body, hashlib.sha512).hexdigest()
    if not signature or computed != signature:
        return "Invalid signature", 401

    payload = request.json
    event = payload.get("event")
    data = payload.get("data", {})
    meta = data.get("metadata", {})

    # Only handle wallet deposits
    if meta.get("type") != "wallet_deposit":
        return "OK", 200

    uid = meta.get("user_id")
    amount = Decimal(meta.get("amount", "0"))
    reference = data.get("reference")

    # Check if transaction exists
    tx = WalletTransaction.query.filter_by(reference_id=reference).first()

    try:
        if event == "charge.success":
            if tx and tx.status == "completed":
                # Already processed, avoid double credit
                return "OK", 200

            # Credit wallet and create transaction
            credit_wallet(
                user_id=uid,
                amount=amount,
                tx_type="deposit",
                description="Wallet deposit via Paystack",
                ref_type="paystack",
                ref_id=reference
            )

            db.session.commit()
            print(f"[WalletDeposit] User {uid} credited {amount} USD, reference={reference}")

        elif event == "charge.failed":
            if tx:
                # Update existing transaction to failed
                tx.status = "failed"
                tx.description = "Wallet deposit failed"
            else:
                # Create failed transaction
                tx = WalletTransaction(
                    id=gen_tx_id(),
                    wallet_id=get_or_create_wallet(uid).id,
                    amount=amount,
                    type="deposit",
                    reference_type="paystack",
                    reference_id=reference,
                    description="Wallet deposit failed",
                    status="failed"
                )
                db.session.add(tx)

            db.session.commit()
            print(f"[WalletDeposit][FAILED] User {uid}, reference={reference}")

        else:
            # Ignore other events
            return "OK", 200

    except Exception as e:
        db.session.rollback()
        print(f"[WalletDeposit][ERROR] {e}")
        return "Internal Server Error", 500

    return "OK", 200


@bp.route("/wallet", methods=["GET"])
@jwt_required()
def wallet_summary():
    uid = get_jwt_identity()
    wallet = Wallet.query.filter_by(user_id=uid).first()

    return success_response({
        "available": float(wallet.balance) if wallet else 0.0,
        "currency": wallet.currency if wallet else "USD"
    })


@bp.route("/wallet/transactions", methods=["GET"])
@jwt_required()
def wallet_transactions():
    uid = get_jwt_identity()
    tx_type = request.args.get("type")
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))

    wallet = Wallet.query.filter_by(user_id=uid).first()
    if not wallet:
        return success_response({"transactions": [], "pagination": {}})

    q = WalletTransaction.query.filter_by(wallet_id=wallet.id)

    if tx_type:
        q = q.filter(WalletTransaction.type == tx_type)

    total = q.count()
    items = (
        q.order_by(WalletTransaction.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return success_response({
        "transactions": [
            {
                "id": t.id,
                "type": t.type,
                "amount": float(t.amount),
                "description": t.description,
                "reference": t.reference_id,
                "created_at": t.created_at.isoformat() + "Z"
            }
            for t in items
        ],
        "pagination": {
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit
        }
    })


@bp.route("/wallet/deposit/init", methods=["POST"])
@jwt_required()
def init_wallet_deposit():
    uid = get_jwt_identity()
    data = request.get_json() or {}
    amount = Decimal(str(data.get("amount")))

    if amount <= 0:
        return error_response("INVALID_AMOUNT", "Invalid deposit amount", 400)

    user = User.query.get(uid)
    if not user:
        return error_response("USER_NOT_FOUND", "User not found", 404)

    reference = f"wallet_{uid}_{uuid.uuid4().hex[:8]}"

    # PAYSTACK payload for hosted page
    payload = {
        "email": user.email,
        "amount": int(amount * 100),
        "currency": "USD",
        "reference": reference,
        "callback_url": f"{current_app.config['FRONTEND_URL']}/client/wallet?deposit=success",
        "metadata": {
            "type": "wallet_deposit",
            "user_id": uid,
            "amount": str(amount)
        }
    }

    headers = {
        "Authorization": f"Bearer {current_app.config['PAYSTACK_SECRET_KEY']}",
        "Content-Type": "application/json",
    }

    # Call Paystack to initialize transaction
    r = requests.post(
        "https://api.paystack.co/transaction/initialize",
        json=payload,
        headers=headers
    )

    res = r.json()
    print("Paystack init response →", res)

    if not r.ok or not res.get("status"):
        return error_response("PAYSTACK_INIT_FAILED", res.get("message", "Initialization failed"), 400)

    # Return only authorization_url and reference to frontend
    return success_response({
        "authorization_url": res["data"]["authorization_url"],
        "reference": res["data"]["reference"]
    })


@bp.route("/wallet/deposit/verify", methods=["POST"])
@jwt_required()
def verify_wallet_deposit():
    data = request.get_json() or {}
    reference = data.get("reference")
    if not reference:
        return error_response("INVALID_REQUEST", "Reference is required", 400)

    # You may verify via Paystack API
    import requests
    secret = current_app.config["PAYSTACK_SECRET_KEY"]
    res = requests.get(
        f"https://api.paystack.co/transaction/verify/{reference}",
        headers={"Authorization": f"Bearer {secret}"}
    )
    result = res.json()
    if not result.get("status"):
        return error_response("VERIFICATION_FAILED", "Could not verify payment", 400)

    # Check if it's a wallet deposit and credit
    metadata = result["data"].get("metadata", {})
    if metadata.get("type") == "wallet_deposit":
        uid = metadata["user_id"]
        amount = Decimal(metadata["amount"])
    return success_response({"message": "Deposit verified"})
