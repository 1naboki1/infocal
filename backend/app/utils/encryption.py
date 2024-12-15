import base64
import logging
from cryptography.fernet import Fernet
from ..config import Config

logger = logging.getLogger(__name__)

def generate_fernet_key():
    """Generate a valid Fernet key"""
    return Fernet.generate_key()

def initialize_cipher_suite():
    """Initialize the Fernet cipher suite with proper error handling"""
    key = Config.ENCRYPTION_KEY
    if not key:
        logger.warning("No encryption key found, generating new key")
        key = generate_fernet_key()
        logger.info("Generated new Fernet key")
        return Fernet(key)
    
    try:
        # If key is already bytes, use it directly; otherwise encode it
        key_bytes = key if isinstance(key, bytes) else key.encode()
        return Fernet(key_bytes)
    except (ValueError, AttributeError):
        logger.warning("Invalid encryption key, generating new key")
        key = generate_fernet_key()
        logger.info("Generated new Fernet key")
        return Fernet(key)

# Initialize cipher suite
cipher_suite = initialize_cipher_suite()

def encrypt_token(token: str) -> str:
    """Encrypt a token string using Fernet symmetric encryption."""
    try:
        if not isinstance(token, str):
            raise ValueError("Token must be a string")
            
        token_bytes = token.encode()
        encrypted_bytes = cipher_suite.encrypt(token_bytes)
        
        return base64.b64encode(encrypted_bytes).decode()
        
    except Exception as e:
        logger.error(f"Token encryption failed: {str(e)}")
        raise ValueError(f"Token encryption failed: {str(e)}")

def decrypt_token(encrypted_token: str) -> str:
    """Decrypt an encrypted token string."""
    try:
        if not isinstance(encrypted_token, str):
            raise ValueError("Encrypted token must be a string")
            
        encrypted_bytes = base64.b64decode(encrypted_token)
        decrypted_bytes = cipher_suite.decrypt(encrypted_bytes)
        
        return decrypted_bytes.decode()
        
    except Exception as e:
        logger.error(f"Token decryption failed: {str(e)}")
        raise ValueError(f"Token decryption failed: {str(e)}")
