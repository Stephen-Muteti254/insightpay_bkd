from insightpay.models.survey import Survey
from insightpay.models.survey_attempt import SurveyAttempt
from insightpay.models.survey_attachment import SurveyAttachment
from app.extensions import db
from datetime import datetime
from insightpay.utils.file_storage import save_survey_attachment
from sqlalchemy import not_

def parse_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).lower() in ("true", "1", "yes", "on")


class SurveyService:

    @staticmethod
    def list_surveys():
        return Survey.query.order_by(Survey.created_at.desc()).all()

    @staticmethod
    def list_active_surveys_for_users(user_id):
        now = datetime.utcnow()

        attempted_subquery = (
            db.session.query(SurveyAttempt.survey_id)
            .filter(SurveyAttempt.user_id == user_id)
            .subquery()
        )

        return (
            Survey.query
            .filter(Survey.is_active.is_(True))
            .filter(Survey.slots_remaining > 0)
            .filter(
                (Survey.expires_at.is_(None)) |
                (Survey.expires_at > now)
            )
            .filter(~Survey.id.in_(attempted_subquery))
            .order_by(Survey.created_at.desc())
            .all()
        )


    @staticmethod
    def start_survey_for_user(survey_id, user_id):
        survey = (
            Survey.query
            .filter_by(id=survey_id, is_active=True)
            .with_for_update()
            .first_or_404()
        )

        if survey.slots_remaining <= 0:
            abort(400, "No slots remaining")

        survey.slots_remaining -= 1
        db.session.commit()
        return survey


    @staticmethod
    def create_survey(data, files, admin_id):
        survey = Survey(
            title=data["title"],
            topic=data["topic"],
            description=data.get("description"),
            duration_minutes=int(data["durationMinutes"]),
            reward=data["reward"],
            total_slots=int(data["totalSlots"]),
            slots_remaining=int(data["totalSlots"]),
            external_url=data["externalUrl"],
            expires_at=(
                datetime.fromisoformat(data["expiresAt"])
                if data.get("expiresAt") else None
            ),
            is_active=parse_bool(data.get("isActive"), True),
            created_by=admin_id,
        )

        db.session.add(survey)
        db.session.flush()

        for f in files:
            relative_path, content_type, size = save_survey_attachment(f, survey.id)

            attachment = SurveyAttachment(
                survey_id=survey.id,
                name=f.filename,
                type=content_type,
                size=size,
                url=relative_path,  # exact stored path
            )
            db.session.add(attachment)

        db.session.commit()
        return survey

    @staticmethod
    def update_survey(survey, data):

        if "isActive" in data:
            survey.is_active = parse_bool(data["isActive"])

        if "totalSlots" in data:
            new_total = int(data["totalSlots"])
            diff = new_total - survey.total_slots
            survey.total_slots = new_total
            survey.slots_remaining = max(0, survey.slots_remaining + diff)

        for field, attr in [
            ("title", "title"),
            ("topic", "topic"),
            ("description", "description"),
            ("durationMinutes", "duration_minutes"),
            ("reward", "reward"),
            ("externalUrl", "external_url"),
        ]:
            if field in data:
                setattr(survey, attr, data[field])

        if "expiresAt" in data:
            survey.expires_at = (
                datetime.fromisoformat(data["expiresAt"])
                if data["expiresAt"] else None
            )

        db.session.commit()
        return survey

    @staticmethod
    def delete_survey(survey):
        db.session.delete(survey)
        db.session.commit()
