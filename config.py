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

# Data configuration — Nifty 50 constituents
STOCKS = [
    # ── Financial Services ───────────────────────────────────────────
    "HDFCBANK.NS",      # HDFC Bank
    "ICICIBANK.NS",     # ICICI Bank
    "SBIN.NS",          # State Bank of India
    "KOTAKBANK.NS",     # Kotak Mahindra Bank
    "AXISBANK.NS",      # Axis Bank
    "INDUSINDBK.NS",    # IndusInd Bank
    "BAJFINANCE.NS",    # Bajaj Finance
    "BAJAJFINSV.NS",    # Bajaj Finserv
    "HDFCLIFE.NS",      # HDFC Life
    "SBILIFE.NS",       # SBI Life Insurance
    # ── IT ────────────────────────────────────────────────────────────
    "TCS.NS",           # Tata Consultancy Services
    "INFY.NS",          # Infosys
    "WIPRO.NS",         # Wipro
    "HCLTECH.NS",       # HCL Technologies
    "TECHM.NS",         # Tech Mahindra
    # ── Oil & Gas / Energy ────────────────────────────────────────────
    "RELIANCE.NS",      # Reliance Industries
    "ONGC.NS",          # ONGC
    "NTPC.NS",          # NTPC
    "POWERGRID.NS",     # Power Grid Corp
    "ADANIENT.NS",      # Adani Enterprises
    # ── Automobile ────────────────────────────────────────────────────
    "MARUTI.NS",        # Maruti Suzuki
    "TATAMOTORS.NS",    # Tata Motors
    "M&M.NS",           # Mahindra & Mahindra
    "BAJAJ-AUTO.NS",    # Bajaj Auto
    "HEROMOTOCO.NS",    # Hero MotoCorp
    "EICHERMOT.NS",     # Eicher Motors
    # ── FMCG ──────────────────────────────────────────────────────────
    "ITC.NS",           # ITC Limited
    "HINDUNILVR.NS",    # Hindustan Unilever
    "NESTLEIND.NS",     # Nestle India
    "TATACONSUM.NS",    # Tata Consumer Products
    "BRITANNIA.NS",     # Britannia Industries
    # ── Pharma & Healthcare ───────────────────────────────────────────
    "SUNPHARMA.NS",     # Sun Pharma
    "DRREDDY.NS",       # Dr. Reddy's
    "CIPLA.NS",         # Cipla
    "APOLLOHOSP.NS",    # Apollo Hospitals
    "DIVISLAB.NS",      # Divi's Labs
    # ── Metals & Mining ───────────────────────────────────────────────
    "TATASTEEL.NS",     # Tata Steel
    "JSWSTEEL.NS",      # JSW Steel
    "HINDALCO.NS",      # Hindalco
    "COALINDIA.NS",     # Coal India
    # ── Telecom ───────────────────────────────────────────────────────
    "BHARTIARTL.NS",    # Bharti Airtel
    # ── Infrastructure / Capital Goods ────────────────────────────────
    "LT.NS",            # Larsen & Toubro
    "ULTRACEMCO.NS",    # UltraTech Cement
    "GRASIM.NS",        # Grasim Industries
    # ── Consumer / Other ──────────────────────────────────────────────
    "ASIANPAINT.NS",    # Asian Paints
    "TITAN.NS",         # Titan Company
    "WIPRO.NS",         # (already listed above, de-duped at runtime)
]

# De-duplicate (WIPRO appears in the file twice for readability)
STOCKS = list(dict.fromkeys(STOCKS))

# ── Sector classification (for portfolio risk constraints) ────────────────
SECTOR_MAP = {
    # Financial Services
    "HDFCBANK.NS": "Financials", "ICICIBANK.NS": "Financials",
    "SBIN.NS": "Financials", "KOTAKBANK.NS": "Financials",
    "AXISBANK.NS": "Financials", "INDUSINDBK.NS": "Financials",
    "BAJFINANCE.NS": "Financials", "BAJAJFINSV.NS": "Financials",
    "HDFCLIFE.NS": "Financials", "SBILIFE.NS": "Financials",
    # IT
    "TCS.NS": "IT", "INFY.NS": "IT", "WIPRO.NS": "IT",
    "HCLTECH.NS": "IT", "TECHM.NS": "IT",
    # Energy
    "RELIANCE.NS": "Energy", "ONGC.NS": "Energy", "NTPC.NS": "Energy",
    "POWERGRID.NS": "Energy", "ADANIENT.NS": "Energy",
    # Automobile
    "MARUTI.NS": "Auto", "TATAMOTORS.NS": "Auto", "M&M.NS": "Auto",
    "BAJAJ-AUTO.NS": "Auto", "HEROMOTOCO.NS": "Auto", "EICHERMOT.NS": "Auto",
    # FMCG
    "ITC.NS": "FMCG", "HINDUNILVR.NS": "FMCG", "NESTLEIND.NS": "FMCG",
    "TATACONSUM.NS": "FMCG", "BRITANNIA.NS": "FMCG",
    # Pharma
    "SUNPHARMA.NS": "Pharma", "DRREDDY.NS": "Pharma", "CIPLA.NS": "Pharma",
    "APOLLOHOSP.NS": "Pharma", "DIVISLAB.NS": "Pharma",
    # Metals
    "TATASTEEL.NS": "Metals", "JSWSTEEL.NS": "Metals",
    "HINDALCO.NS": "Metals", "COALINDIA.NS": "Metals",
    # Telecom
    "BHARTIARTL.NS": "Telecom",
    # Infrastructure
    "LT.NS": "Infra", "ULTRACEMCO.NS": "Infra", "GRASIM.NS": "Infra",
    # Consumer
    "ASIANPAINT.NS": "Consumer", "TITAN.NS": "Consumer",
}

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
