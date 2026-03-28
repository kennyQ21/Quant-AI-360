"""
Parquet Storage Handler
High-performance data storage using Apache Parquet format
with Supabase Storage cloud syncing and Local Disk fallback.
"""
import pandas as pd
from pathlib import Path
import logging
import io
import time
from typing import Optional

# Import the existing global supabase client
from .database import supabase_client

logger = logging.getLogger(__name__)

BUCKET_NAME = "market-data"


class ParquetStore:
    """Parquet format data storage (Cloud primary, Local fallback)"""
    
    def __init__(self, base_path: Path):
        """
        Initialize Parquet store
        
        Args:
            base_path: Base directory for parquet files (Local fallback path)
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        # Verify Cloud Bucket exactly once
        if supabase_client:
            try:
                # Basic check; mostly relies on the bucket existing already
                pass
            except Exception:
                pass
    
    def save(self, data: pd.DataFrame, name: str, compression: str = "snappy") -> bool:
        """
        Save DataFrame to parquet (Tries Cloud, falls back to Local)
        
        Args:
            data: DataFrame to save
            name: File name (without .parquet extension)
            compression: Compression algorithm ('snappy', 'gzip', 'brotli')
        
        Returns:
            True if successful anywhere
        """
        success = False
        
        # 1. Try Cloud Storage First
        if supabase_client:
            cloud_path = f"processed/{name}.parquet"
            if name.startswith("raw_"):
                cloud_path = f"raw/{name.replace('raw_', '')}.parquet"
            
            # Retry loop for network operations
            for attempt in range(3):
                try:
                    buffer = io.BytesIO()
                    data.to_parquet(buffer, compression=compression)
                    buffer.seek(0)
                    
                    # Check if file exists so we can update/upsert
                    opts = {"content-type": "application/octet-stream", "upsert": "true"}
                    supabase_client.storage.from_(BUCKET_NAME).upload(
                        cloud_path,
                        buffer.getvalue(),
                        opts
                    )
                    print(f"[ParquetStore] Saved to SUPABASE: {cloud_path}")
                    logger.info(f"Saved {name} to Supabase bucket: {cloud_path}")
                    success = True
                    break  # Success, exit retry loop
                except Exception as e:
                    logger.warning(f"Cloud upload failed for {name} (Attempt {attempt+1}/3): {str(e)}")
                    if attempt < 2:
                        time.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s
        
        # 2. Local Fallback (or Dual-write if preferred)
        try:
            file_path = self.base_path / f"{name}.parquet"
            data.to_parquet(file_path, compression=compression)
            if not success:
                print(f"[ParquetStore] Fallback to LOCAL for save: {file_path}")
                logger.info(f"Saved {name} to local fallback: {file_path}")
            success = True
        except Exception as e:
            logger.error(f"Local save failed for {name}: {str(e)}")
        
        return success
    
    def load(self, name: str) -> Optional[pd.DataFrame]:
        """
        Load DataFrame from parquet (Tries Cloud, falls back to Local)
        
        Args:
            name: File name (without .parquet extension)
        
        Returns:
            DataFrame or None if error
        """
        # 1. Try Cloud First
        if supabase_client:
            cloud_path = f"processed/{name}.parquet"
            if name.startswith("raw_"):
                cloud_path = f"raw/{name.replace('raw_', '')}.parquet"
                
            for attempt in range(3):
                try:
                    # Timeout handled indirectly via retries/Supabase client config
                    res = supabase_client.storage.from_(BUCKET_NAME).download(cloud_path)
                    buffer = io.BytesIO(res)
                    df = pd.read_parquet(buffer)
                    print(f"[ParquetStore] Loading from SUPABASE: {cloud_path}")
                    logger.info(f"Loaded {name} from Supabase: {cloud_path}")
                    return df
                except Exception as e:
                    logger.warning(f"Cloud fetch failed for {name} (Attempt {attempt+1}/3): {str(e)}")
                    if attempt < 2:
                        time.sleep(2 ** attempt)
            
            print(f"[ParquetStore] Cloud load failed after 3 attempts, attempting local fallback.")
        
        # 2. Local Fallback
        try:
            file_path = self.base_path / f"{name}.parquet"
            if not file_path.exists():
                logger.warning(f"File not found locally either: {file_path}")
                return None
            
            data = pd.read_parquet(file_path)
            print(f"[ParquetStore] Fallback to LOCAL: {file_path}")
            logger.info(f"Loaded {name} from local fallback: {file_path}")
            return data
        except Exception as e:
            logger.error(f"Local load failed for {name}: {str(e)}")
            return None
    
    def exists(self, name: str) -> bool:
        """Check if file exists (Local fast check, doesn't wait for cloud lookup)"""
        return (self.base_path / f"{name}.parquet").exists()
    
    def list_files(self) -> list:
        """List all parquet files locally."""
        return [f.stem for f in self.base_path.glob("*.parquet")]


class DataStore:
    """
    Main data store interface
    Abstracts different storage backends
    """
    
    def __init__(self, storage_type: str = "parquet", base_path: Path = None):
        """
        Initialize data store
        
        Args:
            storage_type: Type of storage ('parquet', 'csv', 'database')
            base_path: Base path for storage
        """
        self.storage_type = storage_type
        
        if storage_type == "parquet":
            self.store = ParquetStore(base_path)
        else:
            raise ValueError(f"Unknown storage type: {storage_type}")
    
    def save_dataset(self, data: pd.DataFrame, dataset_name: str) -> bool:
        """Save dataset"""
        return self.store.save(data, dataset_name)
    
    def load_dataset(self, dataset_name: str) -> Optional[pd.DataFrame]:
        """Load dataset"""
        return self.store.load(dataset_name)
    
    def has_dataset(self, dataset_name: str) -> bool:
        """Check if dataset exists"""
        return self.store.exists(dataset_name)
    
    def list_datasets(self) -> list:
        """List all datasets"""
        return self.store.list_files()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test storage
    store = ParquetStore(Path("data/storage"))
    
    # Create test data
    import numpy as np
    test_data = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=100),
        "value": np.random.randn(100).cumsum()
    })
    
    # Save and load
    store.save(test_data, "test_data")
    loaded = store.load("test_data")
    print(f"\nSaved and loaded {len(loaded)} records")
