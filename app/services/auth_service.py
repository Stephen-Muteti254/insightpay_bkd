from app.extensions import db
from app.models.user import User
from app.models.account_suspensions import AccountSuspension
from app.utils.auth_utils import hash_password, check_password
from app.utils.exceptions import ServiceError
from flask_jwt_extended import create_access_token, create_refresh_token
from datetime import timedelta
from flask import current_app

def register_user(email, password, full_name, role="client", country=None):
    if User.query.filter_by(email=email).first():
        raise ServiceError(
            code="USER_EXISTS",
            message="User with that email already exists",
            details={"field": "email"}
        )

    user = User(
        email=email,
        password_hash=hash_password(password),
        full_name=full_name,
        role=role,
        country=country
    )
    db.session.add(user)
    db.session.commit()
    return user

def authenticate_user(email, password):
    user = User.query.filter_by(email=email).first()
    if not user or not check_password(password, user.password_hash):
        raise ServiceError(code="AUTH_FAILED", message="Invalid credentials")
    return user

def generate_tokens_for_user(user):
    access = create_access_token(identity=user.id, expires_delta=timedelta(seconds=current_app.config.get("ACCESS_EXPIRES", 86400)))
    refresh = create_refresh_token(identity=user.id, expires_delta=timedelta(seconds=current_app.config.get("REFRESH_EXPIRES", 86400)))
    return access, refresh



def build_account_state(user: User):
    active_suspension = (
        AccountSuspension.query
        .filter_by(user_id=user.id, is_active=True)
        .order_by(AccountSuspension.suspended_at.desc())
        .first()
    )

    if not active_suspension:
        return {
            "status": user.account_status,
            "is_suspended": False,
            "suspension": None,
        }

    return {
        "status": (
            "suspended_permanent"
            if active_suspension.suspension_type == "permanent"
            else "suspended_temporary"
        ),
        "is_suspended": True,
        "suspension": {
            "type": active_suspension.suspension_type,
            "reasons": active_suspension.reasons,
            "notes": active_suspension.notes,
            "suspended_at": active_suspension.suspended_at.isoformat(),
            "suspended_until": (
                active_suspension.suspended_until.isoformat()
                if active_suspension.suspended_until
                else None
            ),
        },
    }
