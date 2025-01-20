# app/models/event.py
from app import db
from datetime import datetime

class Event(db.Model):
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(200))
    theme = db.Column(db.String(50))
    is_public = db.Column(db.Boolean, default=False)
    share_code = db.Column(db.String(10), unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    custom_fields = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'date': self.date.strftime('%Y-%m-%d %H:%M'),
            'location': self.location,
            'theme': self.theme,
            'is_public': self.is_public,
            'share_code': self.share_code,
            'custom_fields': self.custom_fields
        }