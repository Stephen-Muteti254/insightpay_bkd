from app.extensions import db
from app.models.notification import Notification
from app.models.user import User
from datetime import datetime
from app.services.email_service import send_notification_email

def get_user_notifications(user_id, is_read=None):
    q = Notification.query.filter_by(user_id=user_id)
    if is_read is not None:
        q = q.filter_by(is_read=is_read)
    return q.order_by(Notification.created_at.desc())

def mark_notification_read(notification):
    notification.is_read = True
    db.session.commit()
    return notification

def mark_all_read_for_user(user_id):
    updated = Notification.query.filter_by(user_id=user_id, is_read=False).update({"is_read": True})
    db.session.commit()
    return updated

ROLE_MAP = {
    "clients": "client",
    "writers": "writer",
}


def send_notification_to_user(
    email: str,
    title: str,
    message: str,
    notif_type="info",
    details=None,
    sender_id=None
):
    user = User.query.filter_by(email=email).first()
    if not user:
        return None

    notif = Notification(
        sender_id=sender_id,
        user_email=email,
        target_type="individual",
        type=notif_type,
        title=title,
        message=message,
        details=details,
        created_at=datetime.utcnow(),
    )
    db.session.add(notif)
    db.session.commit()

    send_notification_email(user, title, message)
    return notif

def send_notification_to_group(group, title, message, notif_type="info", details=None, sender_id=None):
    role = ROLE_MAP.get(group)

    if not role:
        return 0

    users = User.query.filter_by(role=role).all()

    print(
        f"Sending group notification: group={group}, resolved_role={role}, users={len(users)}"
    )


    notif = Notification(
        sender_id=sender_id,
        target_type="group",
        target_group=role,
        type=notif_type,
        title=title,
        message=message,
        details=details,
        created_at=datetime.utcnow(),
    )
    db.session.add(notif)

    for u in users:
        send_notification_email(u, title, message)

    db.session.commit()
    return len(users)


def send_notification_to_all(title, message, notif_type="info", details=None, sender_id=None):
    notif = Notification(
        sender_id=sender_id,
        user_email=u.email,
        target_type="all",
        target_group="all",
        type=notif_type,
        title=title,
        message=message,
        details=details,
        created_at=datetime.utcnow(),
    )
    db.session.add(notif)

    users = User.query.all()
    
    for u in users:
        send_notification_email(u, title, message)

    db.session.commit()
    return len(users)
