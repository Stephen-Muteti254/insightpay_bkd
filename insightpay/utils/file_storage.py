import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app

def save_survey_attachment(file, survey_id):
    root = current_app.config["INSIGHTPAY_SURVEY_UPLOADS_FOLDER"]
    survey_root = os.path.join(root, str(survey_id))

    os.makedirs(survey_root, exist_ok=True)

    filename = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    full_path = os.path.join(survey_root, unique_name)

    file.save(full_path)

    # store RELATIVE path in DB (important)
    return f"surveys/{survey_id}/{unique_name}", file.content_type, os.path.getsize(full_path)
