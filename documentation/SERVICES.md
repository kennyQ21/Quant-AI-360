# Services Architecture Guide

## Overview

The Quant AI Trading System uses a **microservices architecture** to ensure scalability, maintainability, and independent service deployment.

---

## Services

### 1️⃣ Data Service (`services/data_service/`)

**Purpose**: Collect, store, and manage market data

**Files**:
- `market_data.py` - Download prices from yfinance
- `dataset_builder.py` - Combine stocks into unified dataset
- `update_service.py` - Daily price updates

**Key Functions**:
```python
# Download stock data
fetch_stock_data(symbol)

# Save to parquet
save_data(symbol, dataframe)

# Load from parquet
load_data(symbol)

# Build combined dataset
build_dataset()

# Update daily prices
update_all_stocks()
```

**Data Flow**:
```
Yahoo Finance API
    ↓
fetch_stock_data()
    ↓
save_data() → parquet files
    ↓
build_dataset() → market_dataset.parquet
```

---

### 2️⃣ Feature Service (`services/feature_service/`)

**Purpose**: Calculate technical indicators and engineer features

**Files**:
- `indicators.py` - Technical indicator calculations

**Key Functions**:
```python
# Individual indicators
calculate_sma(data, window)         # Simple Moving Average
calculate_ema(data, window)         # Exponential Moving Average
calculate_rsi(data, window=14)      # Relative Strength Index
calculate_macd(data, fast, slow)    # MACD Convergence Divergence
calculate_bollinger_bands(data)     # Bollinger Bands
calculate_atr(high, low, close)     # Average True Range

# Batch processing
add_features_to_data(dataframe)     # Add all indicators at once
```

**Indicators** (Phase 2+):
- Moving Averages: SMA, EMA
- Momentum: RSI, MACD
- Volatility: Bollinger Bands, ATR
- Price Changes: Returns, Log Returns

**Usage**:
```python
from services.feature_service.indicators import add_features_to_data

df = load_data("RELIANCE.NS")
df_with_features = add_features_to_data(df)

# Now has columns: RSI_14, MACD, BB_Upper, ATR_14, etc.
```

---

### 3️⃣ ML Service (`services/ml_service/`)

**Purpose**: Price prediction and pattern recognition (Phase 3+)

**Files**:
- `models.py` - ML model definitions

**Planned Models**:
- LSTM/GRU for price prediction
- Random Forest for classification
- XGBoost for feature importance
- Transformer models for time series

**Current Status**: Placeholder structure for Phase 3+

---

### 4️⃣ Decision Service (`services/decision_service/`)

**Purpose**: Generate trading signals and manage risk

**Files**:
- `trading_decisions.py` - Signal generation & risk management

**Key Classes**:
```python
SignalGeneratorService()       # Generate buy/sell signals
RiskManagementService()        # Calculate stops, position size
PortfolioDecisionService()     # Portfolio-level decisions
```

**Trading Signal**:
```python
@dataclass
class TradingSignal:
    symbol: str               # "RELIANCE.NS"
    signal_type: SignalType   # BUY, SELL, HOLD, UNKNOWN
    confidence: float         # 0.0 - 1.0
    entry_price: float
    exit_price: float
    stop_loss: float
    take_profit: float
    risk_level: RiskLevel     # LOW, MEDIUM, HIGH
    reason: str
    timestamp: str
```

**Risk Management**:
```python
risk_mgr = RiskManagementService()

# Position sizing
position_size = risk_mgr.calculate_position_size(100000)

# Stop loss
sl = risk_mgr.calculate_stop_loss(entry_price=2500)

# Take profit
tp = risk_mgr.calculate_take_profit(entry_price=2500, reward_risk_ratio=2.0)

# Check daily loss limit
allowed = risk_mgr.is_trade_allowed(current_loss, portfolio_value)
```

---

### 5️⃣ Storage (`storage/`)

**Purpose**: Abstract data persistence layer

**Files**:
- `parquet_store.py` - Parquet file operations

**Classes**:
```python
ParquetStore(base_path)        # Low-level parquet operations
DataStore(storage_type, path)  # High-level abstraction
```

**Usage**:
```python
from storage.parquet_store import DataStore

# Initialize
store = DataStore("parquet", Path("data"))

# Save any dataframe
store.save_dataset(df, "my_dataset")

# Load
loaded_df = store.load_dataset("my_dataset")

# Check existence
exists = store.has_dataset("my_dataset")

# List all
datasets = store.list_datasets()
```

---

### 6️⃣ MCP Server (`mcp_server/`)

**Purpose**: Expose all services via Model Context Protocol

**Running MCP Server**:
```bash
python mcp_server/server.py
```

**Exposed Tools**:
```
get_stock_prices(symbol, lookback_days=30)
get_stock_summary(symbol)
get_latest_price(symbol)
list_available_stocks()
get_combined_dataset()
```

**Integration with Agents**:
```python
from agents.langgraph_agent import MarketDataAgent

agent = MarketDataAgent()
result = agent.analyze_stock("RELIANCE.NS")
# Agent uses MCP tools internally
```

---

### 7️⃣ Agents (`agents/`)

**Purpose**: AI-powered analysis using LangChain

**Files**:
- `langgraph_agent.py` - LangChain integration

**Agent Tools**:
- `get_stock_data` - Fetch prices
- `analyze_trends` - Trend analysis
- `get_market_overview` - Portfolio overview

**Usage**:
```python
from agents.langgraph_agent import MarketDataAgent

agent = MarketDataAgent()  # Requires OPENAI_API_KEY

# Analyze single stock
result = agent.analyze_stock("RELIANCE.NS")
print(result['analysis'])

# Analyze portfolio
portfolio_result = agent.analyze_portfolio()
```

---

## Data Flow Diagram

```
┌─────────────────┐
│  Market APIs    │
│  (yfinance)     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  DATA SERVICE                           │
│  ├─ fetch_stock_data()                  │
│  ├─ save_data() → parquet               │
│  └─ build_dataset()                     │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  STORAGE                                │
│  ├─ Individual: RELIANCE.NS.parquet     │
│  ├─ Individual: TCS.NS.parquet          │
│  └─ Combined: market_dataset.parquet    │
└─────────────────────────────────────────┘
         │
         ├──────────────────┐
         │                  │
         ▼                  ▼
┌──────────────────┐   ┌──────────────────┐
│  FEATURE SERVICE │   │   MCP SERVER     │
│  ├─ RSI          │   │                  │
│  ├─ MACD         │   │ get_stock_...()  │
│  ├─ Bollinger    │   │ list_...()       │
│  └─ ATR, EMA     │   └────────┬─────────┘
└────────┬─────────┘            │
         │                      ▼
         ▼                ┌─────────────┐
┌──────────────────┐     │   AGENTS    │
│   ML SERVICE     │     │             │
│  (Phase 3+)      │     │ LangChain   │
│  ├─ Predictions  │     │ ChatGPT     │
│  └─ Patterns     │     └─────────────┘
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────────────┐
│  DECISION SERVICE                    │
│  ├─ Generate signals                 │
│  ├─ Risk management                  │
│  └─ Portfolio optimization           │
└──────────┬──────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  TRADING EXECUTION                   │
│  ├─ Create orders                    │
│  ├─ Monitor positions                │
│  └─ Send alerts                      │
└──────────────────────────────────────┘
```

---

## Service Dependencies

```
Feature Service
    ↓ depends on
Data Service

ML Service
    ↓ depends on
Feature Service

Decision Service
    ↓ depends on
ML Service
Feature Service
Data Service

MCP Server
    ↓ depends on
All Services

Agents
    ↓ depends on
MCP Server
```

---

## Common Operations

### Download and Setup
```bash
# One-time setup with all data download
python setup_phase1.py
```

### Daily Updates
```bash
# Update prices for all stocks
python -m services.data_service.update_service

# Rebuild combined dataset
python -m services.data_service.dataset_builder
```

### Data Validation
```bash
# Verify data integrity
python validate_data.py
```

### Service Testing
```bash
# Test all services
python test_services.py
```

### Start MCP Server
```bash
# Run for agent access
python mcp_server/server.py
```

---

## Docker Deployment

### Build Services
```bash
cd docker
chmod +x build.sh start.sh stop.sh
./build.sh
```

### Run Services
```bash
./start.sh
```

### Check Status
```bash
docker-compose -f docker/docker-compose.yml ps
```

### View Logs
```bash
docker-compose -f docker/docker-compose.yml logs -f
```

### Stop Services
```bash
./stop.sh
```

---

## Configuration

Edit `config.py` to customize:

```python
# Stocks to track
STOCKS = [
    "RELIANCE.NS",
    "TCS.NS",
    "HDFCBANK.NS",
    # ... add/remove as needed
]

# Data parameters
DATA_PERIOD = "10y"        # Historical period
DATA_INTERVAL = "1d"       # Daily candlesticks
LOOKBACK_PERIOD = 30       # Recent days for queries

# Service configuration
MCP_SERVER_HOST = "127.0.0.1"
MCP_SERVER_PORT = 8000
```

---

## Phase Rollout

### ✅ Phase 1 (COMPLETE)
- Data Service - Collection & Storage
- Storage - Parquet persistence
- MCP Server - Basic API

### 🔄 Phase 2 (NEXT)
- Feature Service - Technical indicators
- Decision Service - Signal generation
- Dashboard - Real-time monitoring

### 📋 Phase 3
- ML Service - Price predictions
- Advanced ML - Pattern recognition
- Backtesting engine

### 🚀 Phase 4
- Real-time streaming
- Live trading
- Production deployment

---

## Scaling Strategies

### Independent Scaling
Each service can be deployed and scaled independently:

```bash
# Scale data service for faster downloads
docker-compose scale data_service=3

# Scale feature service for more calculations
docker-compose scale feature_service=5

# Scale decision service for complex portfolio analysis
docker-compose scale decision_service=2
```

### Load Balancing
Use nginx or HAProxy to load balance duplicate services

### Async Processing
Use message queues (RabbitMQ, Kafka) for async communication

### Microservices Framework
Consider using FastAPI + Celery for production:

```python
# Example: Async feature calculation
from celery import Celery

app = Celery('feature_service')

@app.task
def calculate_indicators(symbol):
    data = load_data(symbol)
    return add_features_to_data(data)
```

---

## Error Handling

Each service includes logging and error handling:

```python
import logging

logger = logging.getLogger(__name__)

try:
    data = fetch_stock_data(symbol)
except Exception as e:
    logger.error(f"Error fetching {symbol}: {str(e)}")
    return None
```

---

## Testing

### Unit Tests
Test individual functions in isolation

```python
def test_rsi_calculation():
    prices = pd.Series(range(100, 120))
    rsi = calculate_rsi(prices)
    assert rsi.notna().sum() > 0
```

### Integration Tests
Test service interactions

```python
# test_services.py - Run full integration test
python test_services.py
```

### End-to-End Tests
Test complete workflows

```python
# Example: E2E test
data = fetch_stock_data("RELIANCE.NS")
features = add_features_to_data(data)
signal = generate_signal("RELIANCE.NS", features)
```

---

## Production Monitoring

### Service Health Checks
```python
# Health endpoint for each service
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "data_service"}
```

### Metrics & Logging
```python
# Log important events
logger.info(f"Downloaded {len(data)} records for {symbol}")

# Track metrics
metrics["data_points_processed"] += len(data)
metrics["download_time_seconds"] = elapsed_time
```

### Alerts
```python
# Alert on failures
if len(failed_stocks) > 0:
    send_alert(f"Download failed for {failed_stocks}")
```

---

## Best Practices

✅ **DO**:
- Keep services focused on one responsibility
- Use proper logging throughout
- Handle errors gracefully
- Test before deploying
- Document service interfaces
- Follow naming conventions
- Use type hints in Python

❌ **DON'T**:
- Create circular dependencies between services
- Hardcode configuration values
- Ignore error conditions
- Deploy without testing
- Mix business logic with infrastructure code
- Skip logging

---

## Troubleshooting

### Service Won't Start
```bash
# Check logs
docker logs quant-data-service

# Check configuration
python -c "from config import *; print(PARQUET_DIR)"

# Check dependencies
pip list | grep pandas
```

### Data Not Updating
```bash
# Run service directly
python -m services.data_service.update_service

# Check network
curl -I https://query1.finance.yahoo.com
```

### Feature Calculation Slow
```python
# Profile the code
python -m cProfile -s cumtime services/feature_service/indicators.py

# Optimize data loading
df = pd.read_parquet(file, columns=['Close', 'High', 'Low'])  # Load only needed columns
```

---

## Resources

- [Service-Oriented Architecture](https://en.wikipedia.org/wiki/Service-oriented_architecture)
- [Microservices Patterns](https://microservices.io/patterns/index.html)
- [12 Factor App](https://12factor.net/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Python Logging](https://docs.python.org/3/library/logging.html)

---

## Summary

The services architecture provides:
- ✓ **Scalability**: Scale services independently
- ✓ **Maintainability**: Clear responsibilities
- ✓ **Testability**: Test services in isolation
- ✓ **Flexibility**: Add new services easily
- ✓ **Reliability**: Isolated failures
- ✓ **Deployability**: Ship services independently

This design supports the system through all phases of development and provides a solid foundation for production deployment.
