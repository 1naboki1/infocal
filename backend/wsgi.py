import logging
from app.main import app
from app.services.warning_service import WarningService

# Setup logging
logger = logging.getLogger(__name__)

# Initialize warning service
warning_service = WarningService()
warning_service.start_warning_processor()

logger.info("Warning processor initialized in WSGI")

if __name__ == "__main__":
    app.run()
