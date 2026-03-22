"""
SQLAlchemy ORM Models for Trading Data
Defines database schema using Python classes
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Text
from datetime import datetime

from .database import Base


class MarketPrice(Base):
    """Market price data (OHLCV)"""
    __tablename__ = "market_prices"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True, nullable=False)
    date = Column(Date, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<MarketPrice {self.symbol} {self.date} {self.close}>"


class TechnicalIndicator(Base):
    """Computed technical indicators"""
    __tablename__ = "technical_indicators"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True, nullable=False)
    date = Column(Date, nullable=False, index=True)
    
    # Trend indicators
    sma_20 = Column(Float, nullable=True)
    sma_50 = Column(Float, nullable=True)
    sma_200 = Column(Float, nullable=True)
    ema_12 = Column(Float, nullable=True)
    ema_26 = Column(Float, nullable=True)
    
    # Momentum indicators
    rsi_14 = Column(Float, nullable=True)
    macd = Column(Float, nullable=True)
    macd_signal = Column(Float, nullable=True)
    macd_hist = Column(Float, nullable=True)
    
    # Volatility indicators
    bollinger_upper = Column(Float, nullable=True)
    bollinger_mid = Column(Float, nullable=True)
    bollinger_lower = Column(Float, nullable=True)
    atr_14 = Column(Float, nullable=True)
    
    # Volume indicators
    volume_ma = Column(Float, nullable=True)
    
    # Returns
    returns = Column(Float, nullable=True)
    log_returns = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<TechnicalIndicator {self.symbol} {self.date}>"


class TradeSignal(Base):
    """Trading signals (BUY/SELL/HOLD)"""
    __tablename__ = "trade_signals"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True, nullable=False)
    date = Column(Date, nullable=False, index=True)
    
    signal_type = Column(String(10), nullable=False)  # BUY, SELL, HOLD
    strength = Column(Float, nullable=False)  # 0-100
    
    # Price levels
    entry_price = Column(Float, nullable=True)
    target_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    
    # Strategy info
    strategy = Column(String(50), nullable=True)
    reason = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<TradeSignal {self.symbol} {self.signal_type} {self.strength}%>"


class Trade(Base):
    """Executed trades (for backtesting and live trading)"""
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True, nullable=False)
    
    # Entry details
    entry_time = Column(DateTime, nullable=False, index=True)
    entry_price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    
    # Exit details
    exit_time = Column(DateTime, nullable=True, index=True)
    exit_price = Column(Float, nullable=True)
    
    # Trade metrics
    profit_loss = Column(Float, nullable=True)
    profit_loss_pct = Column(Float, nullable=True)
    
    # Strategy info
    strategy = Column(String(50), nullable=True)
    trade_type = Column(String(10), nullable=False)  # LONG, SHORT
    status = Column(String(20), nullable=False, default="OPEN")  # OPEN, CLOSED
    
    # Risk management
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Trade {self.symbol} {self.trade_type} {self.status}>"


class NewsItem(Base):
    """News and events for sentiment analysis"""
    __tablename__ = "news"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True, nullable=False)
    
    headline = Column(Text, nullable=False)
    source = Column(String(100), nullable=True)
    url = Column(Text, nullable=True)
    
    # Sentiment analysis
    sentiment_score = Column(Float, nullable=True)  # -1.0 to 1.0
    sentiment_label = Column(String(20), nullable=True)  # NEGATIVE, NEUTRAL, POSITIVE
    
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<NewsItem {self.symbol} {self.sentiment_label}>"


class Backtest(Base):
    """Backtest results and metadata"""
    __tablename__ = "backtests"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_name = Column(String(100), nullable=False)
    symbol = Column(String(20), nullable=False)
    
    # Date range
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    
    # Capital
    initial_capital = Column(Float, nullable=False)
    final_capital = Column(Float, nullable=False)
    
    # Metrics
    total_return = Column(Float, nullable=False)
    total_return_pct = Column(Float, nullable=False)
    sharpe_ratio = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    win_rate = Column(Float, nullable=True)
    profit_factor = Column(Float, nullable=True)
    
    # Trades
    total_trades = Column(Integer, nullable=False)
    winning_trades = Column(Integer, nullable=False)
    losing_trades = Column(Integer, nullable=False)
    
    # Cost
    transaction_cost = Column(Float, nullable=False, default=0.001)  # 0.1%
    
    # Results
    results_json = Column(Text, nullable=True)  # Store full results as JSON
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Backtest {self.strategy_name} {self.total_return_pct}%>"
