"""
Parquet Storage Handler
High-performance data storage using Apache Parquet format
"""
import pandas as pd
from pathlib import Path
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ParquetStore:
    """Parquet format data storage"""
    
    def __init__(self, base_path: Path):
        """
        Initialize Parquet store
        
        Args:
            base_path: Base directory for parquet files
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def save(self, data: pd.DataFrame, name: str, compression: str = "snappy") -> bool:
        """
        Save DataFrame to parquet
        
        Args:
            data: DataFrame to save
            name: File name (without .parquet extension)
            compression: Compression algorithm ('snappy', 'gzip', 'brotli')
        
        Returns:
            True if successful
        """
        try:
            file_path = self.base_path / f"{name}.parquet"
            data.to_parquet(file_path, compression=compression)
            logger.info(f"Saved {name} to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving {name}: {str(e)}")
            return False
    
    def load(self, name: str) -> Optional[pd.DataFrame]:
        """
        Load DataFrame from parquet
        
        Args:
            name: File name (without .parquet extension)
        
        Returns:
            DataFrame or None if error
        """
        try:
            file_path = self.base_path / f"{name}.parquet"
            if not file_path.exists():
                logger.warning(f"File not found: {file_path}")
                return None
            
            data = pd.read_parquet(file_path)
            logger.info(f"Loaded {name} from {file_path}")
            return data
        except Exception as e:
            logger.error(f"Error loading {name}: {str(e)}")
            return None
    
    def exists(self, name: str) -> bool:
        """Check if file exists"""
        return (self.base_path / f"{name}.parquet").exists()
    
    def list_files(self) -> list:
        """List all parquet files"""
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
