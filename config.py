"""
Configuration file for Quant AI Trading System
"""
import os
from pathlib import Path

# Base paths
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
INGESTION_DIR = PROJECT_ROOT / "ingestion"
MCP_SERVER_DIR = PROJECT_ROOT / "mcp_server"
AGENTS_DIR = PROJECT_ROOT / "agents"

# Data configuration
STOCKS = [
    "RELIANCE.NS",      # Reliance Industries
    "TCS.NS",           # Tata Consultancy Services
    "HDFCBANK.NS",      # HDFC Bank
    "INFY.NS",          # Infosys
    "WIPRO.NS",         # Wipro
    "BAJAJFINSV.NS",    # Bajaj Finserv
    "SBIN.NS",          # State Bank of India
    "ICICIBANK.NS",     # ICICI Bank
    "KOTAKBANK.NS",     # Kotak Mahindra Bank
    "ASIANPAINT.NS",    # Asian Paints
    "MARUTI.NS",        # Maruti Suzuki
    "BHARTIARTL.NS",    # Bharti Airtel
    "ITC.NS",           # ITC Limited
    "SUNPHARMA.NS",     # Sun Pharma
    "LT.NS",            # Larsen & Toubro
]

# Data parameters
DATA_PERIOD = "10y"      # Historical period to fetch
DATA_INTERVAL = "1d"     # Daily data
LOOKBACK_PERIOD = 30     # Last 30 days for recent data

# File paths
PARQUET_DIR = DATA_DIR / "parquet"
DATASET_FILE = DATA_DIR / "market_dataset.parquet"

# API configuration
MCP_SERVER_HOST = "127.0.0.1"
MCP_SERVER_PORT = 8000

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
