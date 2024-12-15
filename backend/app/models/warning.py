from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId
from ..config import Config

client = MongoClient(Config.MONGO_URI)
db = client[Config.MONGO_DB_NAME]

class Warning:
    collection = db.warnings
    history_collection = db.warning_history
    
    def __init__(self, type, severity, start_time, end_time, location, description, warning_id=None, _id=None):
        self._id = _id
        self.type = type
        self.severity = severity
        self.start_time = start_time
        self.end_time = end_time
        self.location = location  # Now includes geometry data
        self.description = description
        self.warning_id = warning_id  # External ID from Geosphere
        self.created_at = datetime.utcnow()
    
    @classmethod
    def find_active(cls):
        current_time = datetime.utcnow()
        return [
            cls(**data) for data in cls.collection.find({
                'start_time': {'$lte': current_time},
                'end_time': {'$gte': current_time}
            })
        ]
    
    def save(self):
        data = {
            'type': self.type,
            'severity': self.severity,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'location': self.location,
            'description': self.description,
            'warning_id': self.warning_id,
            'created_at': self.created_at
        }
        
        result = self.collection.insert_one(data)
        self._id = result.inserted_id
        return self

    @classmethod
    def is_processed(cls, user_email, warning_id):
        """Check if warning has been processed for user"""
        return cls.history_collection.find_one({
            'user_email': user_email,
            'warning_id': warning_id
        }) is not None
    
    @classmethod
    def mark_processed(cls, user_email, warning_id, calendar_event_id):
        """Mark warning as processed for user"""
        cls.history_collection.insert_one({
            'user_email': user_email,
            'warning_id': warning_id,
            'calendar_event_id': calendar_event_id,
            'processed_at': datetime.utcnow()
        })

    @classmethod
    def get_user_history(cls, user_email, limit=50):
        """Get warning history for user"""
        return list(cls.history_collection.find(
            {'user_email': user_email},
            {'_id': 0}
        ).sort('processed_at', -1).limit(limit))
