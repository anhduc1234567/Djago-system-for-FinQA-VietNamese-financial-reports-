# chatbot/models.py
from mongoengine import Document, EmbeddedDocument, StringField, DateTimeField, ListField, EmbeddedDocumentField, IntField,  EmailField
from datetime import datetime

# Message trong conversation
class Message(EmbeddedDocument):
    role = StringField(required=True, choices=['user', 'assistant'])
    content = StringField(required=True)
    timestamp = DateTimeField(required=True)

# Conversation model
class Conversation(Document):
    conversation_id = StringField(required=True, unique=True)  # UUID
    user_id = StringField(required=True)
    messages = ListField(EmbeddedDocumentField(Message))      # danh sách messages
    file_id = ListField(StringField())                         # list of file IDs
    created_at = DateTimeField()
    updated_at = DateTimeField()

    meta = {
        'collection': 'Conversations'  # tên collection trong MongoDB
    }
# File đã upload
class UploadedFile(Document):
    user_id = StringField(required=True, default="user_ducanh")  # mặc định user
    file_name = StringField(required=True)
    file_path = StringField(required=True)
    upload_date = DateTimeField(default=datetime.utcnow)
    
    meta = {'collection': 'Files'}

class Users(Document):
    user_id = StringField(required=True, unique=True)  # username
    email = EmailField(required=True, unique=True)
    password = StringField(required=True)

    meta = {'collection': 'Users'}