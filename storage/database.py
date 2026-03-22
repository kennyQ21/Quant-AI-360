"""
PostgreSQL Database Connection and Session Management
Handles all database operations for the trading system
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Database URL (PostgreSQL on localhost)
DATABASE_URL = "postgresql://localhost/quant_trading"

# Create engine
try:
    engine = create_engine(
        DATABASE_URL,
        echo=False,  # Set to True for SQL debugging
        pool_size=10,
        max_overflow=20,
    )
except Exception as e:
    logger.warning(f"PostgreSQL connection failed: {e}")
    logger.info("Falling back to SQLite for development")
    # Fallback to SQLite for development
    db_path = Path(__file__).parent.parent / "data" / "quant_trading.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_session():
    """Get database session"""
    return SessionLocal()


def init_db():
    """Initialize all tables in database"""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized")


def drop_all():
    """Drop all tables (for testing)"""
    Base.metadata.drop_all(bind=engine)
    logger.warning("All tables dropped")
