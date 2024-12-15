import logging
import threading
import time
from datetime import datetime, timedelta, timezone
from google_auth_oauthlib.flow import Flow
from ..models.user import User
from ..models.warning import Warning
from ..utils.geo import check_location_relevance
from .geosphere_service import GeosphereService
from .calendar_service import GoogleCalendarService
from ..config import Config

logger = logging.getLogger(__name__)

class WarningService:
    def __init__(self):
        self.geosphere_service = GeosphereService()
        self.running = False
        self.check_interval = Config.WARNING_CHECK_INTERVAL

    def start_warning_processor(self):
        """Start the background warning processor"""
        if self.running:
            logger.warning("Warning processor already running")
            return

        self.running = True
        thread = threading.Thread(target=self._warning_processor_loop)
        thread.daemon = True
        thread.start()
        logger.info("Warning processor started")

    def stop_warning_processor(self):
        """Stop the background warning processor"""
        self.running = False
        logger.info("Warning processor stopped")

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
            warnings = self.geosphere_service.get_warnings()
            logger.info(f"Fetched {len(warnings)} warnings from Geosphere")
            
            # Add debug logging for each warning
            for w in warnings:
                logger.debug(f"Raw warning: {w}")
                logger.debug(f"Warning start_time: {w.get('start_time')}, "
                           f"type: {type(w.get('start_time'))}, "
                           f"timezone: {getattr(w.get('start_time'), 'tzinfo', None)}")
            
            current_time = datetime.now(timezone.utc)
            logger.debug(f"Current time (UTC): {current_time}")
            
            # Filter upcoming warnings
            upcoming_warnings = []
            for w in warnings:
                if not isinstance(w.get('start_time'), datetime):
                    logger.debug(f"Skipping warning - invalid start_time type: {type(w.get('start_time'))}")
                    continue
                
                warning_time = w['start_time'].astimezone(timezone.utc) if w['start_time'].tzinfo else w['start_time'].replace(tzinfo=timezone.utc)
                if warning_time > current_time and warning_time <= current_time + timedelta(days=7):
                    upcoming_warnings.append(w)
                    logger.debug(f"Added upcoming warning: type={w.get('type')}, time={warning_time}")
                else:
                    logger.debug(f"Skipped warning: type={w.get('type')}, time={warning_time}")

            logger.info(f"Found {len(upcoming_warnings)} upcoming warnings")
            
            users = User.get_all_active()
            logger.info(f"Processing warnings for {len(users)} active users")
            
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
            relevant_warnings = self._filter_relevant_warnings(warnings, user.locations, user.warning_preferences)
            
            logger.info(f"Found {len(relevant_warnings)} relevant warnings for user {user.email}")
            logger.debug(f"Relevant warnings: {relevant_warnings}")

            for warning in relevant_warnings:
                try:
                    # Debug log to see warning structure
                    logger.debug(f"Processing warning: {warning}")
                    
                    if not isinstance(warning, dict):
                        logger.error(f"Warning is not a dictionary: {type(warning)}")
                        continue
                        
                    # Check required fields
                    required_fields = ['type', 'severity', 'start_time', 'end_time', 'location', 'description', 'warning_id']
                    missing_fields = [field for field in required_fields if field not in warning]
                    if missing_fields:
                        logger.error(f"Warning missing required fields: {missing_fields}")
                        continue

                    if not Warning.is_processed(user.email, warning['warning_id']):
                        logger.debug(f"Creating calendar event for warning: {warning['warning_id']}")
                        event = calendar_service.create_warning_event(warning)
                        Warning.mark_processed(user.email, warning['warning_id'], event['id'])
                        logger.info(f"Created warning event for user {user.email}: {warning['type']}")
                    else:
                        logger.debug(f"Warning already processed: {warning['warning_id']}")

                except Exception as e:
                    logger.error(f"Error processing individual warning: {str(e)}", exc_info=True)
                    continue

        except Exception as e:
            logger.error(f"Error processing user warnings: {str(e)}", exc_info=True)
            raise

    def _filter_relevant_warnings(self, warnings, locations, preferences):
        """Filter warnings based on user locations and preferences"""
        try:
            relevant_warnings = []
            
            logger.info(f"Checking {len(warnings)} warnings against {len(locations)} locations")
            logger.debug(f"User locations: {locations}")
            
            for warning in warnings:
                try:
                    logger.debug(f"Checking warning: {warning}")
                    warning_type = warning.get('type')
                    warning_id = warning.get('warning_id', 'unknown')
                    
                    # Check if warning type is enabled in preferences
                    if not preferences.get(warning_type, True):
                        logger.debug(f"Warning {warning_id} type {warning_type} disabled")
                        continue

                    # Check relevance for each location
                    for location in locations:
                        logger.debug(f"Checking against location: {location}")
                        if check_location_relevance(location, warning['location']):
                            logger.info(
                                f"Warning {warning_id} relevant for location "
                                f"{location.get('name', 'unknown')}"
                            )
                            relevant_warnings.append(warning)
                            break

                except Exception as e:
                    logger.error(f"Error checking warning: {str(e)}", exc_info=True)
                    continue

            # Sort warnings by start time
            relevant_warnings.sort(key=lambda x: x['start_time'])
            
            logger.info(f"Found {len(relevant_warnings)} relevant warnings")
            return relevant_warnings

        except Exception as e:
            logger.error(f"Error filtering warnings: {str(e)}", exc_info=True)
            return []

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
