"""
Dataset Builder
Combines individual stock parquet files into a unified dataset
"""
import sys
from pathlib import Path
import pandas as pd
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import PARQUET_DIR, DATASET_FILE
from storage.data_loader import store, load_market_data

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def build_dataset() -> pd.DataFrame:
    """
    Build unified dataset from all parquet files
    
    Returns:
        Combined DataFrame with data from all stocks
    """
    try:
        # Get raw data symbols from local store layout as an index helper
        stems = store.list_files()
        raw_symbols = [s.replace("raw_", "") for s in stems if s.startswith("raw_")]
        
        # Also include legacy format items for transition
        legacy_symbols = [s for s in stems if not s.startswith("raw_") and not s.startswith("features_")]
        
        all_symbols = list(set(raw_symbols + legacy_symbols))
        
        if not all_symbols:
            logger.warning(f"No symbols found in data store.")
            return pd.DataFrame()
        
        logger.info(f"Found {len(all_symbols)} symbols to process")
        
        dfs = []
        for symbol in all_symbols:
            try:
                # Try generic load via the data_loader
                df = load_market_data(symbol)
                
                # Fallback to legacy structure if the data_loader (which looks for 'raw_') fails
                if df is None or df.empty:
                    legacy_path = PARQUET_DIR / f"{symbol}.parquet"
                    if legacy_path.exists():
                        df = pd.read_parquet(legacy_path)
                    
                if df is None or df.empty:
                    continue
                
                # Add symbol column
                df["symbol"] = symbol
                
                # Reset index to have Date as a column
                if "Date" not in df.columns and "date" not in df.columns:
                    df = df.reset_index()
                
                dfs.append(df)
                logger.info(f"Loaded {symbol}: {len(df)} records")
            
            except Exception as e:
                logger.error(f"Error reading dataset for {symbol}: {str(e)}")
                continue
        
        if not dfs:
            logger.error("No data could be loaded")
            return pd.DataFrame()
        
        # Combine all dataframes
        dataset = pd.concat(dfs, ignore_index=True)
        logger.info(f"Combined dataset shape: {dataset.shape}")
        
        return dataset
    
    except Exception as e:
        logger.error(f"Error building dataset: {str(e)}")
        return pd.DataFrame()


def save_dataset(dataset: pd.DataFrame) -> bool:
    """
    Save combined dataset to parquet
    
    Args:
        dataset: DataFrame to save
    
    Returns:
        True if successful, False otherwise
    """
    try:
        dataset.to_parquet(DATASET_FILE, index=False)
        logger.info(f"Saved combined dataset to {DATASET_FILE}")
        logger.info(f"Dataset shape: {dataset.shape}")
        return True
    
    except Exception as e:
        logger.error(f"Error saving dataset: {str(e)}")
        return False


def validate_dataset(dataset: pd.DataFrame) -> dict:
    """
    Validate the combined dataset
    
    Args:
        dataset: DataFrame to validate
    
    Returns:
        Dictionary with validation results
    """
    validation = {
        "total_records": len(dataset),
        "unique_symbols": dataset["symbol"].nunique() if "symbol" in dataset.columns else 0,
        "missing_values": dataset.isnull().sum().to_dict(),
        "date_range": None,
        "columns": list(dataset.columns)
    }
    
    if "Date" in dataset.columns:
        validation["date_range"] = {
            "start": str(dataset["Date"].min()),
            "end": str(dataset["Date"].max())
        }
    
    return validation


if __name__ == "__main__":
    # Build dataset
    logger.info("Starting dataset build...")
    dataset = build_dataset()
    
    if dataset.empty:
        logger.error("Failed to build dataset")
        sys.exit(1)
    
    # Save dataset
    if save_dataset(dataset):
        # Validate
        validation = validate_dataset(dataset)
        logger.info("\n=== Dataset Validation ===")
        for key, value in validation.items():
            logger.info(f"{key}: {value}")
        logger.info("✓ Dataset built successfully!")
    else:
        logger.error("Failed to save dataset")
        sys.exit(1)
