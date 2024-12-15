from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
from datetime import datetime, timedelta
import jwt
import logging
from functools import wraps
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os

from .config import Config
from .services.calendar_service import GoogleCalendarService
from .services.geosphere_service import GeosphereService
from .services.warning_service import WarningService
from .services.oauth_service import GoogleOAuthService
from .models.user import User
from .utils.encryption import encrypt_token, decrypt_token
from .utils.logging_setup import setup_logging
from .utils.geo import geocode_location

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize services
warning_service = WarningService()
geosphere_service = GeosphereService()
oauth_service = GoogleOAuthService()

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'No authorization header'}), 401

        try:
            token = auth_header.split(' ')[1]
            payload = jwt.decode(token, Config.JWT_SECRET, algorithms=['HS256'])
            return f(payload['email'], *args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return jsonify({'error': 'Authentication failed'}), 401

    return decorated

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/auth/google', methods=['POST'])
def google_auth():
    """Initialize Google OAuth flow"""
    try:
        flow = oauth_service.create_flow(f"{request.host_url}api/oauth2callback")
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        return jsonify({'auth_url': authorization_url})
    except Exception as e:
        logger.error(f"OAuth initialization error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/oauth2callback')
def oauth2callback():
    """Handle OAuth callback from Google"""
    try:
        code = request.args.get('code')
        if not code:
            logger.error("No authorization code received")
            return redirect(f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}?error=no_code")

        flow = oauth_service.create_flow(f"{request.host_url}api/oauth2callback")
        flow.fetch_token(code=code)
        credentials = flow.credentials

        # Get user info from Google
        service = build('oauth2', 'v2', credentials=credentials)
        user_info = service.userinfo().get().execute()
        email = user_info.get('email')

        if not email:
            logger.error("No email received from Google")
            return redirect(f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}?error=no_email")

        logger.info(f"Processing OAuth callback for user: {email}")

        # Create or update user with Google tokens
        user = User.create_or_update(
            email=email,
            google_tokens={
                'access_token': encrypt_token(credentials.token),
                'refresh_token': encrypt_token(credentials.refresh_token) if credentials.refresh_token else None,
                'token_expiry': credentials.expiry.timestamp() if credentials.expiry else None,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes
            }
        )

        # Verify tokens were saved
        if not user.google_tokens or 'access_token' not in user.google_tokens:
            logger.error(f"Failed to save Google tokens for user: {email}")
            return redirect(f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}?error=token_save_failed")

        # Generate JWT
        token = jwt.encode(
            {
                'email': email,
                'exp': datetime.utcnow() + timedelta(days=7)
            },
            Config.JWT_SECRET
        )

        logger.info(f"Successfully processed OAuth callback for: {email}")
        
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        return redirect(f"{frontend_url}?token={token}&email={email}")

    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}", exc_info=True)
        return redirect(f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}?error=auth_failed")

@app.route('/api/auth/status')
@require_auth
def auth_status(email):
    """Check authentication status"""
    try:
        user = User.find_by_email(email)
        if not user:
            return jsonify({'authenticated': False}), 401
        return jsonify({
            'authenticated': True,
            'user': user.to_dict()
        })
    except Exception as e:
        logger.error(f"Auth status check error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/locations', methods=['GET'])
@require_auth
def get_locations(email):
    """Get user's locations"""
    try:
        user = User.find_by_email(email)
        if not user:
            user = User.create_or_update(email=email)
        return jsonify({'locations': user.locations})
    except Exception as e:
        logger.error(f"Error getting locations: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/locations', methods=['POST'])
@require_auth
def add_location(email):
    """Add a new location"""
    try:
        location_name = request.json.get('location')
        if not location_name:
            return jsonify({'error': 'Location name required'}), 400

        # Get or create user
        user = User.find_by_email(email)
        if not user:
            user = User.create_or_update(email=email)

        try:
            location_data = geocode_location(location_name)
            if not location_data:
                return jsonify({'error': 'Location not found'}), 404
        except Exception as e:
            logger.error(f"Geocoding error for {location_name}: {str(e)}")
            return jsonify({'error': 'Failed to geocode location'}), 400

        location = user.add_location(location_data)
        return jsonify({'location': location})
    except Exception as e:
        logger.error(f"Error adding location: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/locations', methods=['DELETE'])
@require_auth
def remove_location(email):
    """Remove a location"""
    try:
        location = request.json.get('location')
        if not location:
            return jsonify({'error': 'Location required'}), 400

        user = User.find_by_email(email)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        user.remove_location(location)
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Error removing location: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/preferences', methods=['GET'])
@require_auth
def get_preferences(email):
    """Get user's warning preferences"""
    try:
        user = User.find_by_email(email)
        if not user:
            user = User.create_or_update(email=email)
        return jsonify({'preferences': user.warning_preferences})
    except Exception as e:
        logger.error(f"Error getting preferences: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/preferences', methods=['PUT'])
@require_auth
def update_preferences(email):
    """Update user's warning preferences"""
    try:
        preferences = request.json.get('preferences')
        if not preferences:
            return jsonify({'error': 'Preferences required'}), 400

        user = User.find_by_email(email)
        if not user:
            user = User.create_or_update(email=email)
            
        user.update_preferences(preferences)
        return jsonify({
            'status': 'success',
            'preferences': user.warning_preferences
        })
    except Exception as e:
        logger.error(f"Error updating preferences: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/warnings/history', methods=['GET'])
@require_auth
def get_warning_history(email):
    """Get warning history for user"""
    try:
        limit = request.args.get('limit', default=50, type=int)
        user = User.find_by_email(email)
        if not user:
            user = User.create_or_update(email=email)
        history = warning_service.get_user_warning_history(email, limit)
        return jsonify({'history': history})
    except Exception as e:
        logger.error(f"Error getting warning history: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/warnings/active', methods=['GET'])
@require_auth
def get_active_warnings(email):
    """Get active warnings for user"""
    try:
        user = User.find_by_email(email)
        if not user:
            user = User.create_or_update(email=email)
            
        warnings = warning_service.get_active_warnings(user)
        return jsonify({'warnings': warnings})
    except Exception as e:
        logger.error(f"Error getting active warnings: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Start the warning processor
    warning_service.start_warning_processor()
    # Run the application
    app.run(host='0.0.0.0', port=8080)
