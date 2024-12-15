import logging
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from ..config import Config

logger = logging.getLogger(__name__)

class GoogleOAuthService:
    @staticmethod
    def create_flow(redirect_uri):
        return Flow.from_client_config(
            {
                'web': {
                    'client_id': Config.GOOGLE_CLIENT_ID,
                    'client_secret': Config.GOOGLE_CLIENT_SECRET,
                    'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                    'token_uri': 'https://oauth2.googleapis.com/token',
                }
            },
            scopes=[
                'openid',
                'https://www.googleapis.com/auth/userinfo.email',
                'https://www.googleapis.com/auth/userinfo.profile',
                'https://www.googleapis.com/auth/calendar.events'
            ],
            redirect_uri=redirect_uri
        )

    @staticmethod
    def get_user_info(credentials):
        try:
            service = build('oauth2', 'v2', credentials=credentials)
            return service.userinfo().get().execute()
        except Exception as e:
            logger.error(f"Error getting user info: {str(e)}")
            raise
