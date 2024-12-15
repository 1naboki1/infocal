from datetime import datetime
import logging
from pymongo import MongoClient
from bson import ObjectId
from ..config import Config

logger = logging.getLogger(__name__)

client = MongoClient(Config.MONGO_URI)
db = client[Config.MONGO_DB_NAME]

class User:
    collection = db.users
    
    def __init__(self, email, google_tokens=None, locations=None, warning_preferences=None, _id=None, **kwargs):
        self._id = _id
        self.email = email
        self.google_tokens = google_tokens or {}
        self.locations = locations or []
        self.warning_preferences = warning_preferences or {
            'rain': True,
            'snow': True,
            'wind': True,
            'storm': True,
            'heat': True,
            'frost': True
        }
        # Allow for any additional fields from MongoDB
        for key, value in kwargs.items():
            setattr(self, key, value)
        
        if not hasattr(self, 'created_at'):
            self.created_at = datetime.utcnow()
        if not hasattr(self, 'updated_at'):
            self.updated_at = datetime.utcnow()

    @classmethod
    def find_by_email(cls, email):
        try:
            data = cls.collection.find_one({'email': email})
            if data:
                # Convert ObjectId to string for JSON serialization
                if '_id' in data:
                    data['_id'] = str(data['_id'])
                return cls(**data)
            return None
        except Exception as e:
            logger.error(f"Error finding user by email {email}: {str(e)}")
            raise

    @classmethod
    def create_or_update(cls, email, **kwargs):
        """Create or update a user"""
        try:
            user = cls.find_by_email(email)
            if not user:
                logger.info(f"Creating new user with email: {email}")
                user = cls(email=email)
            else:
                logger.info(f"Updating existing user: {email}")

            # Update user with any provided kwargs
            for key, value in kwargs.items():
                if value is not None:  # Only update if value is not None
                    setattr(user, key, value)
                    logger.info(f"Updated {key} for user {email}")

            user.save()
            return user
        except Exception as e:
            logger.error(f"Error creating/updating user {email}: {str(e)}", exc_info=True)
            raise

    def save(self):
        try:
            # Prepare data for MongoDB
            data = {
                'email': self.email,
                'google_tokens': self.google_tokens,
                'locations': self.locations,
                'warning_preferences': self.warning_preferences,
                'created_at': getattr(self, 'created_at', datetime.utcnow()),
                'updated_at': datetime.utcnow()
            }
            
            if hasattr(self, '_id'):
                result = self.collection.update_one(
                    {'_id': ObjectId(self._id) if isinstance(self._id, str) else self._id},
                    {'$set': data}
                )
                if result.modified_count == 0 and result.matched_count == 0:
                    # Document wasn't found, insert it
                    result = self.collection.insert_one(data)
                    self._id = str(result.inserted_id)
            else:
                result = self.collection.insert_one(data)
                self._id = str(result.inserted_id)
            
            logger.info(f"Successfully saved user {self.email}")
            return self
        except Exception as e:
            logger.error(f"Error saving user {self.email}: {str(e)}")
            raise

    def update_tokens(self, tokens):
        try:
            self.google_tokens.update(tokens)
            self.updated_at = datetime.utcnow()
            self.save()
            logger.info(f"Updated tokens for user {self.email}")
        except Exception as e:
            logger.error(f"Error updating tokens for user {self.email}: {str(e)}")
            raise
    
    def add_location(self, location):
        try:
            # Check if location with same name already exists
            existing_locations = [loc.get('name') for loc in self.locations]
            if location.get('name') not in existing_locations:
                self.locations.append(location)
                self.save()
                logger.info(f"Added location {location.get('name')} for user {self.email}")
            return location
        except Exception as e:
            logger.error(f"Error adding location for user {self.email}: {str(e)}")
            raise
    
    def remove_location(self, location):
        try:
            self.locations = [loc for loc in self.locations if loc.get('name') != location.get('name')]
            self.save()
            logger.info(f"Removed location {location.get('name')} for user {self.email}")
        except Exception as e:
            logger.error(f"Error removing location for user {self.email}: {str(e)}")
            raise
    
    def update_preferences(self, preferences):
        try:
            self.warning_preferences.update(preferences)
            self.save()
            logger.info(f"Updated preferences for user {self.email}")
        except Exception as e:
            logger.error(f"Error updating preferences for user {self.email}: {str(e)}")
            raise

    @classmethod
    def get_all_active(cls):
        try:
            users = []
            for data in cls.collection.find():
                if '_id' in data:
                    data['_id'] = str(data['_id'])
                users.append(cls(**data))
            return users
        except Exception as e:
            logger.error(f"Error getting all active users: {str(e)}")
            raise

    def to_dict(self):
        return {
            'email': self.email,
            'locations': self.locations,
            'warning_preferences': self.warning_preferences,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at
        }
