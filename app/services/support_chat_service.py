from app.extensions import db
from app.models.support_chat import SupportChat
from app.models.support_message import SupportMessage
from app.services.chat_service import sanitize_message
from flask import current_app
import os
import uuid
from werkzeug.utils import secure_filename

def save_support_file(file, chat_id, message_id):
    # Root directory
    root_dir = current_app.config.get("SUPPORT_UPLOADS_FOLDER", "uploads/support_chats")
    
    # Ensure folder exists
    dest_dir = os.path.join(root_dir, chat_id, message_id)
    os.makedirs(dest_dir, exist_ok=True)
    
    # Generate unique file name
    filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
    file_path = os.path.join(dest_dir, filename)
    
    file.save(file_path)
    return filename, file_path

def get_or_create_support_chat(user_id):
    chat = SupportChat.query.filter_by(user_id=user_id).first()

    if not chat:
        chat = SupportChat(user_id=user_id)
        db.session.add(chat)
        db.session.commit()

    return chat


def add_support_message(chat_id, sender_id, content):
    # sanitized = sanitize_message(content)

    msg = SupportMessage(
        support_chat_id=chat_id,
        sender_id=sender_id,
        content=content
    )

    db.session.add(msg)
    db.session.commit()
    return msg
