# Quant AI Trading System - Phase 1

## Phase 1: Data Layer Architecture

```
Market APIs
     ↓
Data Collectors
     ↓
MCP Tools
     ↓
LangChain / LangGraph Agents
     ↓
Data Storage
```

## Project Structure

```
quant-ai-trading/
├── data/                    # Data storage and processing
│   ├── build_dataset.py    # Combines individual stocks into unified dataset
│   └── parquet/            # Stored .parquet files (created on first run)
├── ingestion/              # Data collection pipeline
│   ├── market_data.py      # Market data downloader (yfinance)
│   └── update_market_data.py # Daily updates script
├── mcp_server/             # MCP server for agent access
│   └── server.py           # FastMCP server with market data tools
├── agents/                 # AI agents for analysis
│   └── langgraph_agent.py  # LangChain agent integration
├── graph/                  # LangGraph state management
├── models/                 # ML models (Phase 2+)
├── dashboard/              # Web dashboard (Phase 2+)
├── config.py               # Central configuration
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Download Historical Data

```bash
# Download and save data for all configured stocks
python ingestion/market_data.py
```

Or download specific stock:
```python
from ingestion.market_data import download_and_save_stock
download_and_save_stock("RELIANCE.NS")
```

### 3. Build Combined Dataset

```bash
python data/build_dataset.py
```

This combines all individual stock parquet files into `data/market_dataset.parquet`.

### 4. Start MCP Server

```bash
python mcp_server/server.py
```

The server will start and expose these tools:
- `get_stock_prices(symbol)` - Get recent price data
- `get_stock_summary(symbol)` - Get summary statistics
- `get_latest_price(symbol)` - Get latest price info
- `list_available_stocks()` - List all available stocks
- `get_combined_dataset()` - Get dataset metadata

### 5. Use with LangChain Agent

```python
from agents.langgraph_agent import MarketDataAgent

agent = MarketDataAgent()  # Requires OPENAI_API_KEY

# Analyze a stock
result = agent.analyze_stock("RELIANCE.NS")
print(result['analysis'])

# Analyze portfolio
result = agent.analyze_portfolio()
print(result['analysis'])
```

## Features

### Market Data Collection
- **Historical Data**: 10 years of daily OHLCV data
- **Format**: Parquet (optimized for ML workflows)
- **Storage**: Individual stock files + combined dataset
- **Update**: Daily update script for latest prices

### Tracked Stocks (15+)
Default configuration tracks Indian large-cap stocks:
- RELIANCE.NS (Reliance Industries)
- TCS.NS (Tata Consultancy Services)
- HDFCBANK.NS (HDFC Bank)
- INFY.NS (Infosys)
- WIPRO.NS (Wipro)
- And 10+ more...

Edit `config.py` to add/remove stocks.

### MCP Server Tools
The server exposes 6 tools for agent access:

1. **get_stock_prices(symbol, lookback_days=30)**
   - Returns recent price data in dictionary format
   - Default: Last 30 days

2. **get_stock_summary(symbol)**
   - Price statistics (min, max, avg, current)
   - Volume statistics
   - Date range

3. **get_latest_price(symbol)**
   - Current OHLCV data
   - Adj Close price

4. **list_available_stocks()**
   - Returns all available symbols
   - Total count

5. **get_combined_dataset()**
   - Dataset metadata
   - Unique symbols count
   - Total records

### Data Validation

The system validates data for:
- ✓ No missing values
- ✓ Correct timestamps
- ✓ Correct symbol labels
- ✓ Consistent format

Run validation after building dataset:
```python
from data.build_dataset import validate_dataset
import pandas as pd

dataset = pd.read_parquet("data/market_dataset.parquet")
validation = validate_dataset(dataset)
print(validation)
```

## Daily Updates

Automate daily updates with cron or task scheduler:

```bash
# Run daily at 7 PM
0 19 * * * cd /path/to/quant-ai-trading && python ingestion/update_market_data.py
```

Or use Airflow/Prefect for more advanced scheduling (Phase 2+).

## Data Storage

### Individual Stocks
```
data/parquet/
├── RELIANCE.NS.parquet
├── TCS.NS.parquet
├── HDFCBANK.NS.parquet
└── ... (14+ more)
```

Each file contains: `Date, Open, High, Low, Close, Adj Close, Volume`

### Combined Dataset
```
data/market_dataset.parquet

Columns:
- Date
- Open, High, Low, Close
- Adj Close, Volume
- symbol (stock ticker)
```

## Next Steps (Phase 2+)

- [ ] Technical indicators (RSI, MACD, Bollinger Bands, etc.)
- [ ] Pattern recognition (patterns learning)
- [ ] Risk metrics (Beta, Sharpe ratio, correlation)
- [ ] Portfolio optimization (Modern Portfolio Theory)
- [ ] Backtesting engine
- [ ] Real-time data streams
- [ ] Web dashboard
- [ ] ML models for prediction
- [ ] Trading signals generation

## Configuration

Edit `config.py` to customize:

```python
# Add/remove stocks
STOCKS = [
    "RELIANCE.NS",
    "TCS.NS",
    # ...
]

# Data parameters
DATA_PERIOD = "10y"      # Historical period
DATA_INTERVAL = "1d"     # Daily data
LOOKBACK_PERIOD = 30     # Recent days for queries

# API configuration
MCP_SERVER_HOST = "127.0.0.1"
MCP_SERVER_PORT = 8000
```

## Troubleshooting

### No data downloading
- Check internet connection
- Verify stock symbols are correct (e.g., "RELIANCE.NS" for NSE)
- Check Yahoo Finance availability for the symbols

### Parquet files not created
- Ensure `data/parquet/` directory is created
- Check write permissions

### MCP server won't start
- Install FastMCP: `pip install mcp`
- Check port 8000 is available
- Check logs for specific errors

### Dataset building fails
- Ensure at least one stock data is downloaded
- Check for corrupted parquet files
- Verify disk space available

## Resources

- **yfinance**: [Documentation](https://github.com/ranaroussi/yfinance)
- **LangChain**: [Documentation](https://python.langchain.com/)
- **LangGraph**: [Documentation](https://github.com/langchain-ai/langgraph)
- **MCP**: [Reference](https://modelcontextprotocol.io/)
- **Pandas**: [Parquet Guide](https://pandas.pydata.org/docs/reference/io.html#parquet)

## Status

✅ **Phase 1 Complete**
- [x] Project structure
- [x] Data downloader
- [x] Parquet storage
- [x] Dataset builder
- [x] MCP server
- [x] LangChain agent skeleton
- [x] Configuration system
- [x] Daily update script
- [x] Data validation

🔄 **Next Phase**: Technical Indicators & Analysis
