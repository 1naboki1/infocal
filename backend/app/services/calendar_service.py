import logging
from datetime import datetime
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from ..models.user import User
from ..utils.encryption import decrypt_token, encrypt_token
from ..config import Config

logger = logging.getLogger(__name__)

class GoogleCalendarService:
    def __init__(self, user_email):
        self.logger = logging.getLogger(__name__)
        self.user = User.find_by_email(user_email)
        if not self.user:
            raise ValueError(f"User not found: {user_email}")
        
        self.credentials = self._get_credentials()
        self.service = build('calendar', 'v3', credentials=self.credentials)

    def _get_credentials(self):
        """Get and refresh Google credentials if needed"""
        try:
            tokens = self.user.google_tokens
            if not tokens:
                raise ValueError("No Google tokens found for user")

            credentials = Credentials(
                token=decrypt_token(tokens['access_token']),
                refresh_token=decrypt_token(tokens['refresh_token']) if tokens.get('refresh_token') else None,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=Config.GOOGLE_CLIENT_ID,
                client_secret=Config.GOOGLE_CLIENT_SECRET,
                scopes=['https://www.googleapis.com/auth/calendar.events']
            )

            if credentials.expired:
                credentials.refresh(Request())
                self.user.update_tokens({
                    'access_token': encrypt_token(credentials.token),
                    'token_expiry': credentials.expiry.timestamp()
                })

            return credentials
        except Exception as e:
            logger.error(f"Error getting credentials: {str(e)}")
            raise

    def create_warning_event(self, warning):
        """Create a calendar event for a warning"""
        try:
            if not isinstance(warning, dict):
                raise ValueError("Warning must be a dictionary")

            event = {
                'summary': f"Weather Warning: {warning['type'].capitalize()}",
                'description': warning['description'],
                'start': {
                    'dateTime': warning['start_time'].isoformat(),
                    'timeZone': 'Europe/Vienna',
                },
                'end': {
                    'dateTime': warning['end_time'].isoformat(),
                    'timeZone': 'Europe/Vienna',
                },
                'colorId': self._get_severity_color(warning['severity']),
                'location': warning['location'].get('area', ''),
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 60},
                        {'method': 'email', 'minutes': 120}
                    ]
                }
            }
            
            logger.debug(f"Creating calendar event: {event}")
            created_event = self.service.events().insert(calendarId='primary', body=event).execute()
            logger.info(f"Created calendar event: {created_event['id']}")
            
            return created_event

        except HttpError as e:
            logger.error(f"Google Calendar API error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error creating calendar event: {str(e)}")
            raise

    def _get_severity_color(self, severity):
        """Map severity to Google Calendar color IDs"""
        color_map = {
            'low': '7',     # Pale Green
            'medium': '5',  # Yellow
            'high': '11',   # Red
            'extreme': '4'  # Dark Red
        }
        return color_map.get(severity.lower(), '1')  # Default to blue

    def delete_event(self, event_id):
        """Delete a calendar event"""
        try:
            self.service.events().delete(calendarId='primary', eventId=event_id).execute()
            logger.info(f"Deleted calendar event: {event_id}")
            return True
        except HttpError as e:
            logger.error(f"Error deleting calendar event: {str(e)}")
            return False
