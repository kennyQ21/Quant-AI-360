# Quick Start Guide - Phase 1 Setup

## 🚀 Initial Setup (5 minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run One-Time Setup
```bash
python setup_phase1.py
```

This script will:
- ✓ Create necessary directories
- ✓ Download 10 years of historical data for 15+ stocks
- ✓ Save data in optimized Parquet format
- ✓ Build combined market dataset
- ✓ Validate all data

**Note**: First run takes 10-15 minutes (downloading large datasets)

---

## 📊 Daily Operations

### Update Latest Data
```bash
python ingestion/update_market_data.py
```

Run this daily (or schedule with cron/scheduler) to fetch latest prices.

### Rebuild Dataset
```bash
python data/build_dataset.py
```

Rebuilds combined dataset after updates.

### Health Check
```bash
python validate_data.py
```

Validates all data is correct and complete.

---

## 🛠️ Development

### Test Phase 1 Components
```bash
python test_phase1.py
```

Runs 5 tests to verify everything works:
1. Data download
2. Parquet storage
3. Dataset building
4. MCP server initialization
5. LangGraph agent initialization

### Start MCP Server (for agents)
```bash
python mcp_server/server.py
```

Runs on `http://127.0.0.1:8000`

### Use with LangChain Agent
```python
from agents.langgraph_agent import MarketDataAgent

agent = MarketDataAgent()  # Requires OPENAI_API_KEY

# Analyze a stock
result = agent.analyze_stock("RELIANCE.NS")
print(result['analysis'])
```

---

## 📁 Project Structure

```
quant-ai-trading/
├── data/
│   ├── parquet/              ← Stock .parquet files
│   ├── market_dataset.parquet ← Combined dataset
│   └── build_dataset.py
├── ingestion/
│   ├── market_data.py        ← Data downloader
│   └── update_market_data.py ← Daily updates
├── mcp_server/
│   └── server.py             ← MCP tools server
├── agents/
│   └── langgraph_agent.py    ← AI agent
├── config.py                 ← Configuration
├── setup_phase1.py           ← Initial setup
├── validate_data.py          ← Data validation
├── test_phase1.py            ← Functionality tests
└── README.md                 ← Full documentation
```

---

## ⚙️ Configuration

Edit `config.py` to customize:

```python
# Stocks to track (add/remove as needed)
STOCKS = [
    "RELIANCE.NS",
    "TCS.NS",
    "HDFCBANK.NS",
    # ... 12+ more
]

# Data parameters
DATA_PERIOD = "10y"      # Historical period to fetch
DATA_INTERVAL = "1d"     # Daily candlesticks
LOOKBACK_PERIOD = 30     # Recent days for queries
```

---

## 🔍 Common Tasks

### Add a New Stock
```python
from config import STOCKS
from ingestion.market_data import download_and_save_stock

# Add to config.py first: STOCKS.append("SYMBOL.NS")

# Then download
download_and_save_stock("SYMBOL.NS")

# Rebuild dataset
python data/build_dataset.py
```

### Check Latest Price
```python
from ingestion.market_data import load_data

data = load_data("RELIANCE.NS")
print(data[["Close", "Volume"]].tail())
```

### Export Dataset for ML
```python
import pandas as pd

dataset = pd.read_parquet("data/market_dataset.parquet")

# Filter for specific stock
reliance = dataset[dataset["symbol"] == "RELIANCE.NS"]

# Save for training
reliance.to_csv("reliance_training_data.csv", index=False)
```

---

## 🐛 Troubleshooting

### Downloads are slow
- Normal for 10 years × 15+ stocks
- Takes 10-15 minutes on first run
- Later updates are faster (only last 30 days)

### No data files created
- Check internet connection
- Verify stock symbols are correct (e.g., "RELIANCE.NS" not "RELIANCE")
- Check Yahoo Finance isn't blocking requests

### MCP server won't start
- Install: `pip install mcp`
- Check port 8000 is available
- Run with: `python mcp_server/server.py`

### Agent needs API key
- Set: `export OPENAI_API_KEY="your-key"`
- Or: `echo "OPENAI_API_KEY=your-key" > .env`

---

## 📈 Next Phase

Phase 2 will add:
- Technical indicators (RSI, MACD, Bollinger Bands)
- Pattern recognition
- Risk metrics
- Portfolio optimization
- Real-time streaming
- Web dashboard

---

## ✅ Verification Checklist

After setup, verify:
- [ ] Dependencies installed: `pip show pandas`
- [ ] Data directory created: `ls -la data/parquet/`
- [ ] Parquet files exist: Check `data/parquet/*.parquet`
- [ ] Combined dataset: Check `data/market_dataset.parquet`
- [ ] Tests pass: `python test_phase1.py`
- [ ] MCP server starts: `python mcp_server/server.py`

---

## 📚 Resources

- [yfinance Documentation](https://github.com/ranaroussi/yfinance)
- [Pandas Parquet](https://pandas.pydata.org/docs/reference/io.html#parquet)
- [LangChain Docs](https://python.langchain.com/)
- [MCP Reference](https://modelcontextprotocol.io/)

---

Need help? See README.md for full documentation.
