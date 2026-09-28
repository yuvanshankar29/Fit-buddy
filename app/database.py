"""Database connection and session management module using SQLAlchemy."""

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

logger = logging.getLogger(__name__)

# SQLite connection args for multi-threaded FastAPI compatibility
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency for yielding request-scoped SQLAlchemy database sessions.
    
    Guarantees session cleanup upon completion or on failure.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initializes SQLite database tables on application startup."""
    import app.models  # noqa: F401 - Ensure all models are registered with Base
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully at %s", settings.DATABASE_URL)
