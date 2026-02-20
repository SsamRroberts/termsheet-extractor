import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from core.config import settings


def setup_logging() -> None:
    """
    Setup global logging configuration.

    Call this once on app instantiation in main.py.

    Usage anywhere in the project:
        import logging
        logger = logging.getLogger(__name__)
    """

    # Root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Capture all logs; handlers can filter levels

    handlers: list[logging.Handler] = []
    file_handler = None

    # File logging (rotating)
    if settings.LOG_PATH and settings.LOG_FILE:
        try:
            os.makedirs(settings.LOG_PATH, exist_ok=True)
            logger.info(f"Creating log directory {settings.LOG_PATH}")
        except Exception as e:
            logger.error(f"Error creating log directory {settings.LOG_PATH}: {e}")
            raise

        file_handler = RotatingFileHandler(
            settings.LOG_FILE,
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=5,
        )
        file_handler.setLevel(logging.DEBUG)
        handlers.append(file_handler)

    # Console logging
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)
    handlers.append(stream_handler)

    # Formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    for h in handlers:
        h.setFormatter(formatter)
        logger.addHandler(h)

    # Attach file handler to uvicorn loggers if present
    if file_handler:
        for uvicorn_logger in ("uvicorn", "uvicorn.access"):
            logging.getLogger(uvicorn_logger).addHandler(file_handler)
            logging.getLogger(uvicorn_logger).setLevel(logging.DEBUG)

    # Silence noisy loggers
    logging.getLogger("multipart.multipart").setLevel(logging.WARNING)

    logger.info("Logging configured successfully")
