import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # MongoDB Configuration
    # MongoDB Configuration
    MONGO_USERNAME = os.getenv('MONGO_ROOT_USERNAME', 'admin')
    MONGO_PASSWORD = os.getenv('MONGO_ROOT_PASSWORD', 'adminpassword')
    MONGO_HOST = os.getenv('MONGO_HOST', 'mongodb')
    MONGO_PORT = os.getenv('MONGO_PORT', '27017')
    MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'infocal')
    
    MONGO_URI = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB_NAME}?authSource=admin"
    
    # Google OAuth Configuration
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
    GOOGLE_OAUTH_REDIRECT_URI = 'http://localhost:8080/api/oauth2callback'
    
    # Security Configuration
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')  # Remove .encode()
    JWT_SECRET = os.getenv('JWT_SECRET')
    JWT_EXPIRATION = int(os.getenv('JWT_EXPIRATION', '3600'))
    
    # Geosphere API Configuration
    GEOSPHERE_API_URL = os.getenv('GEOSPHERE_API_URL')
    GEOSPHERE_API_KEY = os.getenv('GEOSPHERE_API_KEY')
    
    # Warning Configuration
    WARNING_CHECK_INTERVAL = int(os.getenv('WARNING_CHECK_INTERVAL', '300'))
    WARNING_RADIUS_KM = float(os.getenv('WARNING_RADIUS_KM', '50.0'))
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Application Configuration
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    TESTING = os.getenv('TESTING', 'False').lower() == 'true'
    
    # CORS Configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
