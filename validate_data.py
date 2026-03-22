"""
Data Validation & Health Check
Validates the data layer before proceeding
"""
import sys
from pathlib import Path
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
from config import PARQUET_DIR, DATASET_FILE

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_stock_data(symbol: str) -> dict:
    """
    Validate individual stock data
    
    Args:
        symbol: Stock symbol
    
    Returns:
        Validation report
    """
    file_path = PARQUET_DIR / f"{symbol}.parquet"
    
    report = {
        "symbol": symbol,
        "file_exists": file_path.exists(),
        "issues": [],
        "status": "ok"
    }
    
    if not file_path.exists():
        report["status"] = "missing"
        return report
    
    try:
        df = pd.read_parquet(file_path)
        
        # Check for required columns
        required_cols = ["Open", "High", "Low", "Close", "Volume"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            report["issues"].append(f"Missing columns: {missing_cols}")
        
        # Check for missing values
        null_counts = df.isnull().sum()
        if null_counts.any():
            null_info = {col: int(count) for col, count in null_counts[null_counts > 0].items()}
            report["issues"].append(f"Null values: {null_info}")
        
        # Check data range
        report["records"] = len(df)
        report["date_range"] = {
            "start": str(df.index.min()),
            "end": str(df.index.max())
        }
        
        # Check for duplicates
        if df.index.duplicated().any():
            report["issues"].append(f"Duplicate dates: {df.index.duplicated().sum()}")
        
        # Check price consistency (OHLC)
        if "High" in df.columns and "Low" in df.columns:
            if (df["High"] < df["Low"]).any():
                report["issues"].append("Invalid OHLC: High < Low")
        
        if "Close" in df.columns and "High" in df.columns:
            if (df["Close"] > df["High"]).any():
                report["issues"].append("Invalid OHLC: Close > High")
        
        # Determine status
        if report["issues"]:
            report["status"] = "warning"
        
        return report
    
    except Exception as e:
        report["issues"].append(str(e))
        report["status"] = "error"
        return report


def validate_combined_dataset() -> dict:
    """
    Validate combined dataset
    
    Returns:
        Validation report
    """
    report = {
        "file_exists": DATASET_FILE.exists(),
        "issues": [],
        "status": "ok"
    }
    
    if not DATASET_FILE.exists():
        report["status"] = "missing"
        report["issues"].append("Dataset file not found")
        return report
    
    try:
        df = pd.read_parquet(DATASET_FILE)
        
        # Basic stats
        report["total_records"] = len(df)
        report["unique_symbols"] = df["symbol"].nunique() if "symbol" in df.columns else 0
        report["columns"] = list(df.columns)
        
        # Check required columns
        if "symbol" not in df.columns:
            report["issues"].append("Missing 'symbol' column")
        
        # Check for nulls
        null_counts = df.isnull().sum()
        if null_counts.any():
            null_info = {col: int(count) for col, count in null_counts[null_counts > 0].items()}
            report["issues"].append(f"Null values: {null_info}")
        
        # Determine status
        if report["issues"]:
            report["status"] = "warning"
        
        return report
    
    except Exception as e:
        report["issues"].append(str(e))
        report["status"] = "error"
        return report


def run_health_check():
    """Run complete data layer health check"""
    logger.info("=" * 60)
    logger.info("DATA LAYER HEALTH CHECK")
    logger.info("=" * 60)
    
    # Check parquet directory
    logger.info(f"\n1. Parquet Directory: {PARQUET_DIR}")
    if PARQUET_DIR.exists():
        parquet_files = list(PARQUET_DIR.glob("*.parquet"))
        logger.info(f"   Found {len(parquet_files)} stock files")
    else:
        logger.warning("   Directory does not exist")
    
    # Validate individual stocks
    logger.info("\n2. Validating stock data...")
    stock_reports = {}
    issues_count = 0
    
    for file_path in PARQUET_DIR.glob("*.parquet"):
        symbol = file_path.stem
        report = validate_stock_data(symbol)
        stock_reports[symbol] = report
        
        status_icon = "✓" if report["status"] == "ok" else "⚠" if report["status"] == "warning" else "✗"
        logger.info(f"   {status_icon} {symbol}: {report.get('records', 'N/A')} records")
        
        if report["issues"]:
            issues_count += len(report["issues"])
            for issue in report["issues"]:
                logger.warning(f"      - {issue}")
    
    # Validate combined dataset
    logger.info("\n3. Validating combined dataset...")
    dataset_report = validate_combined_dataset()
    
    if dataset_report["status"] == "ok":
        logger.info(f"   ✓ Dataset: {dataset_report.get('total_records', 'N/A')} records")
    elif dataset_report["status"] == "warning":
        logger.warning("   ⚠ Dataset: Warning detected")
    else:
        logger.error("   ✗ Dataset: Issues found")
    
    if dataset_report["issues"]:
        for issue in dataset_report["issues"]:
            logger.warning(f"      - {issue}")
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("HEALTH CHECK SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total stocks: {len(stock_reports)}")
    logger.info(f"Total issues: {issues_count}")
    
    all_ok = all(r["status"] == "ok" for r in stock_reports.values()) and dataset_report["status"] == "ok"
    
    if all_ok:
        logger.info("\n✓ Data layer is healthy!")
    else:
        logger.warning("\n⚠ Some issues detected above. Please review.")
    
    return {
        "stocks": stock_reports,
        "dataset": dataset_report,
        "all_healthy": all_ok
    }


if __name__ == "__main__":
    results = run_health_check()
