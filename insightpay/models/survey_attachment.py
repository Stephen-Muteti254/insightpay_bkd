from app.extensions import db
import uuid


def gen_uuid(prefix="att"):
    return f"{prefix}_{uuid.uuid4()}"


class SurveyAttachment(db.Model):
    __tablename__ = "insightpay_survey_attachments"

    id = db.Column(db.String(50), primary_key=True, default=gen_uuid)
    survey_id = db.Column(
        db.String(50),
        db.ForeignKey("insightpay_surveys.id"),
        nullable=False
    )

    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(100))
    size = db.Column(db.Integer)
    url = db.Column(db.Text, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "size": self.size,
            "url": self.url,
        }
