from insightpay.models.survey import Survey
from insightpay.models.survey_attempt import SurveyAttempt
from insightpay.models.survey_attachment import SurveyAttachment
from app.extensions import db
from datetime import datetime
from insightpay.utils.file_storage import save_survey_attachment
from sqlalchemy import not_
from flask import current_app

import json
from insightpay.models.survey_question import SurveyQuestion
from insightpay.models.survey_question_option import SurveyQuestionOption
import os
import uuid


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

        questions_payload = data.get("questions")

        survey = Survey(
            title=data["title"],
            topic=data["topic"],
            description=data.get("description"),
            duration_minutes=int(data["durationMinutes"]),
            reward=data["reward"],
            total_slots=int(data["totalSlots"]),
            slots_remaining=int(data["totalSlots"]),
            is_active=data.get("isActive", "true") == "true",
            created_by=admin_id,
            expires_at=datetime.fromisoformat(data["expiresAt"]) if data.get("expiresAt") else None
        )

        db.session.add(survey)
        db.session.flush()  # get survey.id

        # -------------------------
        # QUESTIONS
        # -------------------------
        if questions_payload:
            questions = json.loads(questions_payload)

            for idx, q in enumerate(questions):

                if not q.get("question"):
                    raise ValueError("Question text required")

                if q["type"] in ["single_choice", "multiple_choice", "checkbox"] and not q.get("options"):
                    raise ValueError("Choice questions require options")

                question = SurveyQuestion(
                    survey_id=survey.id,
                    question_text=q["question"],
                    question_type=q["type"],
                    required=q.get("required", True),
                    position=idx
                )

                db.session.add(question)
                db.session.flush()

                # options
                if q["type"] in ["single_choice", "multiple_choice", "checkbox", "rating"]:
                    for opt in q.get("options", []):
                        option = SurveyQuestionOption(
                            question_id=question.id,
                            label=opt,
                            value=opt
                        )
                        db.session.add(option)

        # -------------------------
        # ATTACHMENTS
        # -------------------------
        upload_root = current_app.config["INSIGHTPAY_SURVEY_UPLOADS_FOLDER"]

        survey_dir = os.path.join(upload_root, survey.id)
        os.makedirs(survey_dir, exist_ok=True)

        for file in files:

            filename = f"{uuid.uuid4().hex}_{file.filename}"
            relative_path = os.path.join(survey.id, filename)
            file_path = os.path.join(upload_root, relative_path)

            file.save(file_path)

            attachment = SurveyAttachment(
                survey_id=survey.id,
                name=file.filename,
                type=file.mimetype,
                size=os.path.getsize(file_path),
                url=relative_path
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

        if "questions" in data:
            SurveyQuestion.query.filter_by(survey_id=survey.id).delete()

            for idx, q in enumerate(data["questions"]):

                question = SurveyQuestion(
                    survey_id=survey.id,
                    question_text=q["question"],
                    question_type=q["type"],
                    position=idx
                )

                db.session.add(question)
                db.session.flush()

                if q["type"] in ["single_choice", "multiple_choice", "checkbox"]:
                    for opt in q.get("options", []):
                        option = SurveyQuestionOption(
                            question_id=question.id,
                            label=opt,
                            value=opt
                        )
                        db.session.add(option)

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

        upload_root = current_app.config["INSIGHTPAY_SURVEY_UPLOADS_FOLDER"]

        survey_dir = os.path.join(upload_root, survey.id)

        # delete files
        if os.path.exists(survey_dir):
            for root, dirs, files in os.walk(survey_dir, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(survey_dir)

        db.session.delete(survey)
        db.session.commit()
