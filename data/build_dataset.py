"""
Dataset Builder
Combines individual stock parquet files into a unified dataset
"""
import sys
from pathlib import Path
import pandas as pd
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import PARQUET_DIR, DATASET_FILE

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
        # Find all parquet files
        parquet_files = list(PARQUET_DIR.glob("*.parquet"))
        
        if not parquet_files:
            logger.warning(f"No parquet files found in {PARQUET_DIR}")
            return pd.DataFrame()
        
        logger.info(f"Found {len(parquet_files)} parquet files")
        
        dfs = []
        for file_path in parquet_files:
            try:
                df = pd.read_parquet(file_path)
                
                # Add symbol column
                symbol = file_path.stem  # filename without extension
                df["symbol"] = symbol
                
                # Reset index to have Date as a column
                df = df.reset_index()
                
                dfs.append(df)
                logger.info(f"Loaded {symbol}: {len(df)} records")
            
            except Exception as e:
                logger.error(f"Error reading {file_path}: {str(e)}")
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
