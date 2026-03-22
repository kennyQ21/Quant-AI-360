"""
Phase 1 Setup Script - Updated for services architecture
Downloads initial data and builds dataset
Run this once to set up the data layer
"""
import sys
from pathlib import Path
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import STOCKS, PARQUET_DIR
from services.data_service.market_data import download_and_save_stock

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_phase_1():
    """
    Complete Phase 1 setup
    1. Create directories
    2. Download stock data
    3. Build combined dataset
    """
    logger.info("=" * 60)
    logger.info("PHASE 1 SETUP - DATA LAYER")
    logger.info("=" * 60)
    
    # Step 1: Create parquet directory
    logger.info("\n[1/3] Creating parquet directory...")
    PARQUET_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"✓ Directory ready: {PARQUET_DIR}")
    
    # Step 2: Download stock data
    logger.info(f"\n[2/3] Downloading data for {len(STOCKS)} stocks...")
    logger.info("This may take several minutes (15-20 stocks × ~10 years of data)...\n")
    
    successful = []
    failed = []
    
    for idx, symbol in enumerate(STOCKS, 1):
        logger.info(f"[{idx}/{len(STOCKS)}] {symbol}...", end=" ")
        try:
            if download_and_save_stock(symbol):
                successful.append(symbol)
                logger.info("✓")
            else:
                failed.append(symbol)
                logger.info("✗ FAILED")
        except Exception as e:
            failed.append(symbol)
            logger.error(f"✗ ERROR: {str(e)}")
    
    logger.info("\n" + "-" * 60)
    logger.info("Download Summary:")
    logger.info(f"  Successful: {len(successful)}/{len(STOCKS)}")
    logger.info(f"  Failed: {len(failed)}/{len(STOCKS)}")
    
    if failed:
        logger.warning(f"  Failed symbols: {', '.join(failed)}")
    
    # Step 3: Build dataset
    if successful:
        logger.info("\n[3/3] Building combined dataset...")
        try:
            from services.data_service.dataset_builder import build_dataset, save_dataset, validate_dataset
            
            dataset = build_dataset()
            if not dataset.empty:
                if save_dataset(dataset):
                    validation = validate_dataset(dataset)
                    logger.info("✓ Dataset built successfully!")
                    logger.info("\nDataset Statistics:")
                    logger.info(f"  Total records: {validation['total_records']}")
                    logger.info(f"  Unique symbols: {validation['unique_symbols']}")
                    logger.info(f"  Columns: {validation['columns']}")
                else:
                    logger.error("✗ Failed to save dataset")
            else:
                logger.error("✗ Failed to build dataset")
        except Exception as e:
            logger.error(f"✗ Error building dataset: {str(e)}")
    else:
        logger.warning("\nSkipping dataset build (no data downloaded)")
    
    # Final summary
    logger.info("\n" + "=" * 60)
    logger.info("PHASE 1 SETUP COMPLETE")
    logger.info("=" * 60)
    logger.info("\nNext steps:")
    logger.info("  1. Start MCP server: python mcp_server/server.py")
    logger.info("  2. Test with agent: python agents/langgraph_agent.py")
    logger.info("  3. Schedule daily updates for latest data")
    logger.info("\nFor documentation: See README.md")


if __name__ == "__main__":
    try:
        setup_phase_1()
    except KeyboardInterrupt:
        logger.warning("\n\nSetup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n\nSetup failed: {str(e)}")
        sys.exit(1)
