import logging
import sys
from typing import Optional
from .config import get_settings

def setup_logging(name: Optional[str] = None) -> logging.Logger:
    """Configure logging with a consistent format."""
    settings = get_settings()
    
    logger = logging.getLogger(name or "nlsql")
    logger.setLevel(settings.LOG_LEVEL)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )
        logger.addHandler(handler)
    
    return logger