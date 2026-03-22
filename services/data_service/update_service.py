"""
Daily Market Data Update Service
Fetches latest data and updates the parquet files
"""
import sys
from pathlib import Path
import logging
from datetime import datetime

import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import STOCKS
from services.data_service.market_data import download_and_save_stock, load_data, save_data

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def update_all_stocks() -> dict:
    """
    Update data for all configured stocks
    
    Returns:
        Dictionary with update results
    """
    results = {
        "timestamp": datetime.now().isoformat(),
        "successful": [],
        "failed": [],
        "total": len(STOCKS)
    }
    
    logger.info(f"Starting daily update for {len(STOCKS)} stocks...")
    
    for symbol in STOCKS:
        try:
            if download_and_save_stock(symbol):
                results["successful"].append(symbol)
                logger.info(f"✓ Updated {symbol}")
            else:
                results["failed"].append(symbol)
                logger.error(f"✗ Failed to update {symbol}")
        
        except Exception as e:
            results["failed"].append(symbol)
            logger.error(f"✗ Error updating {symbol}: {str(e)}")
    
    # Log summary
    logger.info("\n=== Update Summary ===")
    logger.info(f"Total: {results['total']}")
    logger.info(f"Successful: {len(results['successful'])}")
    logger.info(f"Failed: {len(results['failed'])}")
    logger.info(f"Success Rate: {len(results['successful'])/results['total']*100:.1f}%")
    
    if results["failed"]:
        logger.warning(f"Failed symbols: {results['failed']}")
    
    return results


def append_new_data(symbol: str) -> bool:
    """
    Append newly fetched data to existing parquet file
    Useful for incremental updates without re-downloading full history
    
    Args:
        symbol: Stock symbol
    
    Returns:
        True if successful, False otherwise
    """
    try:
        from services.data_service.market_data import fetch_stock_data
        
        # Load existing data
        existing_data = load_data(symbol)
        
        if existing_data.empty:
            logger.warning(f"No existing data for {symbol}, downloading full history...")
            return download_and_save_stock(symbol)
        
        # Get last date in existing data
        if "Date" in existing_data.columns:
            last_date = existing_data["Date"].max()
        else:
            last_date = existing_data.index.max()
        
        logger.info(f"Last recorded date for {symbol}: {last_date}")
        
        # Fetch recent data (last 30 days)
        new_data = fetch_stock_data(symbol, period="30d")
        
        if new_data.empty:
            logger.warning(f"No new data available for {symbol}")
            return False
        
        # Remove duplicates and append
        new_data_reset = new_data.reset_index()
        existing_data_reset = existing_data.reset_index() if not isinstance(existing_data.index, pd.RangeIndex) else existing_data
        
        # Combine and remove duplicates based on Date
        combined = pd.concat([existing_data_reset, new_data_reset]).drop_duplicates(
            subset=["Date"] if "Date" in existing_data_reset.columns else [0]
        ).sort_index()
        
        # Save updated data
        save_data(symbol, combined)
        logger.info(f"Updated {symbol} with {len(combined)} records")
        return True
    
    except Exception as e:
        logger.error(f"Error appending data for {symbol}: {str(e)}")
        return False


if __name__ == "__main__":
    # Run full update
    results = update_all_stocks()
    
    # Check if we should rebuild the dataset
    if results["successful"]:
        logger.info("\nRebuild dataset after updates? Run: python services/data_service/dataset_builder.py")
