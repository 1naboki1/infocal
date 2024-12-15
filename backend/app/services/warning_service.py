import logging
import threading
import time
from datetime import datetime, timedelta, timezone
from threading import Lock
from google_auth_oauthlib.flow import Flow

from ..models.user import User
from ..models.warning import Warning
from .geosphere_service import GeosphereService
from .calendar_service import GoogleCalendarService
from ..config import Config

logger = logging.getLogger(__name__)

class WarningService:
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(WarningService, cls).__new__(cls)
                cls._instance.initialized = False
            return cls._instance
    
    def __init__(self):
        if self.initialized:
            return
            
        self.geosphere_service = GeosphereService()
        self.running = False
        self.check_interval = Config.WARNING_CHECK_INTERVAL
        self.processor_thread = None
        self.initialized = True

    def start_warning_processor(self):
        """Start the background warning processor"""
        with self._lock:
            if self.running:
                logger.warning("Warning processor already running")
                return
            
            if self.processor_thread and self.processor_thread.is_alive():
                logger.warning("Warning processor thread already exists")
                return

            self.running = True
            self.processor_thread = threading.Thread(target=self._warning_processor_loop)
            self.processor_thread.daemon = True
            self.processor_thread.start()
            logger.info("Warning processor started")

    def stop_warning_processor(self):
        """Stop the background warning processor"""
        with self._lock:
            self.running = False
            logger.info("Warning processor stopped")
            if self.processor_thread:
                self.processor_thread.join(timeout=30)
                self.processor_thread = None

    def _warning_processor_loop(self):
        """Background loop to process warnings"""
        logger.info("Warning processor loop started")
        while self.running:
            try:
                self.process_warnings()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in warning processor loop: {str(e)}")
                time.sleep(60)  # Wait before retrying

    def process_warnings(self):
        """Process all warnings for all users"""
        try:
            logger.info("Starting warning processing cycle")
            
            # Get all active users and their locations
            users = User.get_all_active()
            logger.info(f"Processing warnings for {len(users)} active users")

            # Collect all unique locations from all users
            all_locations = []
            for user in users:
                if user.locations:
                    all_locations.extend(user.locations)
            
            if not all_locations:
                logger.info("No locations to check for warnings")
                return

            # Get warnings for all locations
            warnings = self.geosphere_service.get_warnings(all_locations)
            logger.info(f"Fetched {len(warnings)} warnings from Geosphere")

            current_time = datetime.now(timezone.utc)
            logger.debug(f"Current time (UTC): {current_time}")
            
            # Filter for active and upcoming warnings
            upcoming_warnings = []
            for w in warnings:
                start_time = w.get('start_time')
                end_time = w.get('end_time')
                
                if not isinstance(start_time, datetime) or not isinstance(end_time, datetime):
                    logger.debug(f"Skipping warning - invalid time format: start={start_time}, end={end_time}")
                    continue
                
                # Ensure the times are UTC
                start_time_utc = start_time if start_time.tzinfo else start_time.replace(tzinfo=timezone.utc)
                end_time_utc = end_time if end_time.tzinfo else end_time.replace(tzinfo=timezone.utc)
                
                # Warning is valid if it ends in the future and starts within the next 7 days
                is_future_warning = end_time_utc > current_time
                is_within_window = start_time_utc <= current_time + timedelta(days=7)
                
                if is_future_warning and is_within_window:
                    logger.debug(f"Found valid warning: type={w.get('type')}, "
                               f"start={start_time_utc}, end={end_time_utc}")
                    upcoming_warnings.append(w)
                else:
                    logger.debug(f"Skipping warning: type={w.get('type')}, "
                               f"start={start_time_utc}, end={end_time_utc}, "
                               f"is_future={is_future_warning}, is_within_window={is_within_window}")

            logger.info(f"Found {len(upcoming_warnings)} upcoming warnings")
            
            # Process warnings for each user
            for user in users:
                try:
                    if not user.google_tokens or not user.google_tokens.get('access_token'):
                        logger.info(f"Skipping user {user.email} - no Google tokens")
                        continue

                    self._process_user_warnings(user, upcoming_warnings)
                except Exception as e:
                    logger.error(f"Error processing warnings for user {user.email}: {str(e)}")
                    continue
                    
            logger.info("Completed warning processing cycle")
        except Exception as e:
            logger.error(f"Error in warning processing: {str(e)}")

    def _process_user_warnings(self, user, warnings):
        """Process warnings for a specific user"""
        try:
            calendar_service = GoogleCalendarService(user.email)
            relevant_warnings = []
            
            # Filter warnings based on user preferences and check for duplicates
            for warning in warnings:
                warning_id = warning.get('warning_id')
                warning_type = warning.get('type')
                
                # Skip if warning type is disabled in preferences
                if not user.warning_preferences.get(warning_type, True):
                    continue
                    
                # Skip if warning is already processed
                if Warning.is_processed(user.email, warning_id):
                    logger.debug(f"Warning {warning_id} already processed for user {user.email}")
                    continue
                    
                # Check if warning location matches any user location
                for user_location in user.locations:
                    if (warning['location']['lat'] == user_location['lat'] and 
                        warning['location']['lon'] == user_location['lon']):
                        relevant_warnings.append(warning)
                        break
            
            logger.info(f"Found {len(relevant_warnings)} new relevant warnings for user {user.email}")
            logger.debug(f"Relevant warnings: {relevant_warnings}")

            for warning in relevant_warnings:
                try:
                    # Double-check for duplicate right before creation
                    if not Warning.is_processed(user.email, warning['warning_id']):
                        logger.debug(f"Creating calendar event for warning: {warning['warning_id']}")
                        event = calendar_service.create_warning_event(warning)
                        Warning.mark_processed(user.email, warning['warning_id'], event['id'])
                        logger.info(f"Created warning event for user {user.email}: {warning['type']}")
                except Exception as e:
                    logger.error(f"Error processing individual warning: {str(e)}", exc_info=True)
                    continue

        except Exception as e:
            logger.error(f"Error processing user warnings: {str(e)}", exc_info=True)
            raise

    def get_user_warning_history(self, user_email, limit=50):
        """Get warning history for user"""
        return Warning.get_user_history(user_email, limit)

    def update_user_preferences(self, user_email, preferences):
        """Update user warning preferences"""
        user = User.find_by_email(user_email)
        if not user:
            raise ValueError(f"User not found: {user_email}")
        
        user.update_preferences(preferences)
        logger.info(f"Updated preferences for user {user_email}")

    def create_oauth_flow(self, redirect_uri):
        """Create Google OAuth flow"""
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
