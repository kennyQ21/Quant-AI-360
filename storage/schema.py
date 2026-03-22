#!/usr/bin/env python
"""
Initialize Database Schema
Creates all tables and indexes in PostgreSQL
Run this once to set up the database
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from storage.database import init_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Initialize database"""
    logger.info("Initializing database schema...")
    
    try:
        # Create all tables
        init_db()
        
        logger.info("✓ Database schema initialized successfully")
        logger.info("✓ Tables created:")
        logger.info("  - market_prices")
        logger.info("  - technical_indicators")
        logger.info("  - trade_signals")
        logger.info("  - trades")
        logger.info("  - news")
        logger.info("  - backtests")
        
        return 0
    
    except Exception as e:
        logger.error(f"✗ Failed to initialize database: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
