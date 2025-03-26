
import os
import logging
import json
from app import db
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy import JSON

logger = logging.getLogger(__name__)

def get_db():
    from flask import current_app
    with current_app.app_context():
        return db.session

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, index=True)
    phone_number = db.Column(db.String(20), unique=True, index=True)
    name = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    preferences = db.Column(MutableDict.as_mutable(JSON), default=dict)
    
    requests = db.relationship("VideoRequest", back_populates="user")
    
    def get_preferred_message_type(self) -> str:
        if not self.preferences:
            return "whatsapp"
        return self.preferences.get("preferred_message_type", "whatsapp")
    
    def set_preferred_message_type(self, message_type: str) -> None:
        if not self.preferences:
            self.preferences = {}
        self.preferences["preferred_message_type"] = message_type

class VideoRequest(db.Model):
    __tablename__ = "video_requests"

    id = db.Column(db.Integer, primary_key=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    topic = db.Column(db.String(100))
    subject = db.Column(db.String(50))
    level = db.Column(db.String(20))
    query = db.Column(db.Text)
    status = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    request_metadata = db.Column(MutableDict.as_mutable(JSON), default=dict)
    
    user = db.relationship("User", back_populates="requests")
    video = db.relationship("Video", back_populates="request", uselist=False)
    
    def get_message_type(self) -> str:
        if not self.request_metadata:
            return self.user.get_preferred_message_type()
        return self.request_metadata.get("message_type", self.user.get_preferred_message_type())
    
    def is_enhanced(self) -> bool:
        if not self.request_metadata:
            return False
        return self.request_metadata.get("enhanced_features", False)

class Video(db.Model):
    __tablename__ = "videos"

    id = db.Column(db.Integer, primary_key=True, index=True)
    request_id = db.Column(db.Integer, db.ForeignKey("video_requests.id"))
    title = db.Column(db.String(200))
    description = db.Column(db.Text, nullable=True)
    firebase_url = db.Column(db.String(255))
    duration = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    video_metadata = db.Column(MutableDict.as_mutable(JSON), default=dict)
    
    request = db.relationship("VideoRequest", back_populates="video")
    
    def get_content_features(self) -> List[str]:
        if not self.video_metadata or "content_features" not in self.video_metadata:
            return []
        return self.video_metadata.get("content_features", [])
