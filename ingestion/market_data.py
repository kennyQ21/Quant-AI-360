"""
Market Data Downloader
Fetches historical stock data from Yahoo Finance
"""
import sys
from pathlib import Path
import yfinance as yf
import pandas as pd
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import PARQUET_DIR, DATA_PERIOD, DATA_INTERVAL
from storage.data_loader import load_market_data, save_market_data

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_stock_data(symbol: str, period: str = DATA_PERIOD, interval: str = DATA_INTERVAL) -> pd.DataFrame:
    """
    Fetch historical stock data from Yahoo Finance
    
    Args:
        symbol: Stock symbol (e.g., "RELIANCE.NS")
        period: Period to fetch (default: 10y)
        interval: Interval (default: 1d for daily)
    
    Returns:
        DataFrame with OHLCV data
    """
    try:
        logger.info(f"Fetching data for {symbol}...")
        data = yf.download(symbol, period=period, interval=interval, progress=False)
        
        if data.empty:
            logger.warning(f"No data found for {symbol}")
            return pd.DataFrame()
        
        logger.info(f"Successfully fetched {len(data)} records for {symbol}")
        return data
    
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {str(e)}")
        return pd.DataFrame()


def save_data(symbol: str, data: pd.DataFrame) -> bool:
    """
    Save stock data to parquet format via Unified DataLoader
    
    Args:
        symbol: Stock symbol
        data: DataFrame to save
    
    Returns:
        True if successful, False otherwise
    """
    try:
        success = save_market_data(data, symbol)
        if success:
            logger.info(f"Saved {symbol} data via DataLoader")
        return success
    
    except Exception as e:
        logger.error(f"Error saving data for {symbol}: {str(e)}")
        return False


def load_data(symbol: str) -> pd.DataFrame:
    """
    Load stock data from parquet file via Unified DataLoader
    
    Args:
        symbol: Stock symbol
    
    Returns:
        DataFrame with stock data
    """
    try:
        data = load_market_data(symbol)
        
        if data is None or data.empty:
            logger.warning(f"No data found for {symbol} after fallback.")
            return pd.DataFrame()
        
        logger.info(f"Loaded {len(data)} records for {symbol}")
        return data
    
    except Exception as e:
        logger.error(f"Error loading data for {symbol}: {str(e)}")
        return pd.DataFrame()


def download_and_save_stock(symbol: str) -> bool:
    """
    Download and save stock data in one operation
    
    Args:
        symbol: Stock symbol
    
    Returns:
        True if successful, False otherwise
    """
    data = fetch_stock_data(symbol)
    if data.empty:
        return False
    return save_data(symbol, data)


if __name__ == "__main__":
    # Example usage
    symbol = "RELIANCE.NS"
    data = fetch_stock_data(symbol)
    print(f"\nLast 5 rows of {symbol}:")
    print(data.tail())
    
    # Save the data
    save_data(symbol, data)
    
    # Load and verify
    loaded_data = load_data(symbol)
    print(f"\nVerification - Loaded {len(loaded_data)} records")
