import logging
import sys
import time
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from core.config import settings

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # test connections before using
    pool_recycle=1800,  # recycle every 30 minutes
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def test_database_connection() -> None:
    """Test database connection and exit if it fails."""
    delay = 6
    max_retries = 10
    for attempt in range(max_retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            return
        except Exception as exc:
            logger.error(f"Database connection failed: {exc}")
            logger.warning(f"Waiting for DB... ({attempt + 1}/{max_retries})")
            time.sleep(delay)
    logger.error("Failed to connect to DB after retries.")
    sys.exit(1)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get the database session

    Use `db.begin_nested()` inside endpoints, this will ensure that the session is committed or rolled back properly.
    """

    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
