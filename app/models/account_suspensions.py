from app.extensions import db
from datetime import datetime
import uuid

def gen_uuid(prefix=None):
    uid = str(uuid.uuid4())
    return f"{prefix}-{uid}" if prefix else uid

class AccountSuspension(db.Model):
    __tablename__ = "account_suspensions"

    id = db.Column(db.String(50), primary_key=True, default=lambda: gen_uuid("sus"))
    user_id = db.Column(db.String(50), db.ForeignKey("users.id"), nullable=False)

    suspension_type = db.Column(db.String(20))  
    # temporary | permanent

    reasons = db.Column(db.JSON, nullable=False)
    notes = db.Column(db.Text, nullable=True)

    suspended_at = db.Column(db.DateTime, default=datetime.utcnow)
    suspended_until = db.Column(db.DateTime, nullable=True)

    is_active = db.Column(db.Boolean, default=True)

    admin_id = db.Column(db.String(50), nullable=False)
