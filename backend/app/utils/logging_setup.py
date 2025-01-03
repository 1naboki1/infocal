import logging
import sys
from logging.handlers import RotatingFileHandler
from ..config import Config

def setup_logging():
    """
    Configure application-wide logging settings.
    
    Sets up logging to both file and console with proper formatting
    and log rotation.
    """
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Set root logger to DEBUG
    
    # Create formatters
    verbose_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s'
    )
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s'  # Added name to see source
    )
    
    # Console Handler - Now showing DEBUG messages
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(simple_formatter)
    console_handler.setLevel(logging.DEBUG)  # Changed from INFO to DEBUG
    
    # File Handler
    file_handler = RotatingFileHandler(
        'infocal.log',
        maxBytes=10000000,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(verbose_formatter)
    file_handler.setLevel(logging.DEBUG)
    
    # Remove existing handlers if any
    logger.handlers = []
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # Set logging levels for specific modules
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('google').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.INFO)
    
    # Set specific loggers to DEBUG
    logging.getLogger('app.services.geosphere_service').setLevel(logging.DEBUG)
    logging.getLogger('app.services.warning_service').setLevel(logging.DEBUG)
    
    logger.info('Logging setup completed')

def get_logger(name):
    """
    Get a logger instance with the given name.
    
    Args:
        name (str): Name for the logger
        
    Returns:
        Logger: Configured logger instance
    """
    return logging.getLogger(name)
