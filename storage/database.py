"""
PostgreSQL Database Connection and Session Management
Handles all database operations for the trading system
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import Pool, QueuePool, StaticPool
import logging
from pathlib import Path
from config.settings import settings
from supabase import create_client, Client

logger = logging.getLogger(__name__)

# Supabase Client for Blob Storage & Auth
supabase_client: Client | None = None
try:
    if settings.db.supabase_url and settings.db.supabase_key:
        supabase_client = create_client(settings.db.supabase_url, settings.db.supabase_key)
        logger.info("Supabase API client initialized successfully.")
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {e}")

# Database URL from configured settings
DATABASE_URL = settings.db.database_url

engine_kwargs = {"echo": False}
if DATABASE_URL and DATABASE_URL.startswith("postgresql"):
    engine_kwargs["poolclass"] = QueuePool
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20
else:
    # Fallback to SQLite for local development only if no DB is given
    db_path = Path(__file__).parent.parent / "data" / "quant_trading.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    DATABASE_URL = f"sqlite:///{db_path}"
    engine_kwargs["connect_args"] = {"check_same_thread": False}
    engine_kwargs["poolclass"] = StaticPool
    logger.info(f"Using SQLite fallback at {db_path}")

try:
    engine = create_engine(DATABASE_URL, **engine_kwargs)
    logger.info("Database engine initialized successfully.")
except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
    raise e

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_session():
    """Get database session"""
    return SessionLocal()

def init_db():
    """Initialize all tables in database"""
    # Import models here to ensure they are registered with Base
    import storage.models
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized")

def drop_all():
    """Drop all tables (for testing)"""
    Base.metadata.drop_all(bind=engine)
    logger.warning("All tables dropped")

