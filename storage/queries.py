"""
Common Database Queries and Operations
Provides high-level database interface for the trading system
"""
from sqlalchemy import desc, and_
from datetime import datetime, date, timedelta
from typing import List, Optional

from .models import MarketPrice, TechnicalIndicator, Trade, TradeSignal, Backtest
from .database import get_session


class PriceQueries:
    """Queries for market price data"""
    
    @staticmethod
    def save_price(symbol: str, date: date, open_: float, high: float, low: float, close: float, volume: int):
        """Save or update market price"""
        session = get_session()
        try:
            price = session.query(MarketPrice).filter_by(symbol=symbol, date=date).first()
            if price:
                price.open = open_
                price.high = high
                price.low = low
                price.close = close
                price.volume = volume
                price.updated_at = datetime.utcnow()
            else:
                price = MarketPrice(
                    symbol=symbol, date=date,
                    open=open_, high=high, low=low, close=close, volume=volume
                )
                session.add(price)
            session.commit()
            return price
        finally:
            session.close()
    
    @staticmethod
    def get_prices(symbol: str, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[MarketPrice]:
        """Get price data for a symbol"""
        session = get_session()
        try:
            query = session.query(MarketPrice).filter_by(symbol=symbol)
            if start_date:
                query = query.filter(MarketPrice.date >= start_date)
            if end_date:
                query = query.filter(MarketPrice.date <= end_date)
            return query.order_by(MarketPrice.date).all()
        finally:
            session.close()
    
    @staticmethod
    def get_latest_price(symbol: str) -> Optional[MarketPrice]:
        """Get most recent price"""
        session = get_session()
        try:
            return session.query(MarketPrice).filter_by(symbol=symbol).order_by(desc(MarketPrice.date)).first()
        finally:
            session.close()


class IndicatorQueries:
    """Queries for technical indicators"""
    
    @staticmethod
    def save_indicator(symbol: str, date: date, **kwargs):
        """Save technical indicator"""
        session = get_session()
        try:
            indicator = session.query(TechnicalIndicator).filter_by(symbol=symbol, date=date).first()
            if indicator:
                for key, value in kwargs.items():
                    if hasattr(indicator, key):
                        setattr(indicator, key, value)
                indicator.updated_at = datetime.utcnow()
            else:
                indicator = TechnicalIndicator(symbol=symbol, date=date, **kwargs)
                session.add(indicator)
            session.commit()
            return indicator
        finally:
            session.close()
    
    @staticmethod
    def get_indicators(symbol: str, days: int = 100) -> List[TechnicalIndicator]:
        """Get recent indicators"""
        session = get_session()
        try:
            start_date = date.today() - timedelta(days=days)
            return session.query(TechnicalIndicator).filter(
                and_(
                    TechnicalIndicator.symbol == symbol,
                    TechnicalIndicator.date >= start_date
                )
            ).order_by(TechnicalIndicator.date).all()
        finally:
            session.close()


class TradeQueries:
    """Queries for trade history"""
    
    @staticmethod
    def open_trade(symbol: str, entry_price: float, quantity: float, strategy: str, 
                   stop_loss: Optional[float] = None, take_profit: Optional[float] = None):
        """Open a new trade"""
        session = get_session()
        try:
            trade = Trade(
                symbol=symbol,
                entry_time=datetime.utcnow(),
                entry_price=entry_price,
                quantity=quantity,
                strategy=strategy,
                trade_type="LONG",
                status="OPEN",
                stop_loss=stop_loss,
                take_profit=take_profit
            )
            session.add(trade)
            session.commit()
            return trade
        finally:
            session.close()
    
    @staticmethod
    def close_trade(trade_id: int, exit_price: float):
        """Close an open trade"""
        session = get_session()
        try:
            trade = session.query(Trade).filter_by(id=trade_id).first()
            if trade and trade.status == "OPEN":
                trade.exit_time = datetime.utcnow()
                trade.exit_price = exit_price
                trade.profit_loss = (exit_price - trade.entry_price) * trade.quantity
                trade.profit_loss_pct = ((exit_price - trade.entry_price) / trade.entry_price) * 100
                trade.status = "CLOSED"
                session.commit()
            return trade
        finally:
            session.close()
    
    @staticmethod
    def get_open_trades(symbol: Optional[str] = None) -> List[Trade]:
        """Get all open trades"""
        session = get_session()
        try:
            query = session.query(Trade).filter_by(status="OPEN")
            if symbol:
                query = query.filter_by(symbol=symbol)
            return query.all()
        finally:
            session.close()
    
    @staticmethod
    def get_trade_history(symbol: str, days: int = 30) -> List[Trade]:
        """Get closed trades in date range"""
        session = get_session()
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            return session.query(Trade).filter(
                and_(
                    Trade.symbol == symbol,
                    Trade.status == "CLOSED",
                    Trade.exit_time >= start_date
                )
            ).order_by(desc(Trade.exit_time)).all()
        finally:
            session.close()


class SignalQueries:
    """Queries for trading signals"""
    
    @staticmethod
    def save_signal(symbol: str, date: date, signal_type: str, strength: float, 
                    strategy: str, **kwargs):
        """Save trading signal"""
        session = get_session()
        try:
            signal = TradeSignal(
                symbol=symbol,
                date=date,
                signal_type=signal_type,
                strength=strength,
                strategy=strategy,
                **kwargs
            )
            session.add(signal)
            session.commit()
            return signal
        finally:
            session.close()
    
    @staticmethod
    def get_signals(symbol: str, signal_type: Optional[str] = None, days: int = 30) -> List[TradeSignal]:
        """Get recent signals"""
        session = get_session()
        try:
            start_date = date.today() - timedelta(days=days)
            query = session.query(TradeSignal).filter(
                and_(
                    TradeSignal.symbol == symbol,
                    TradeSignal.date >= start_date
                )
            )
            if signal_type:
                query = query.filter_by(signal_type=signal_type)
            return query.order_by(desc(TradeSignal.date)).all()
        finally:
            session.close()


class BacktestQueries:
    """Queries for backtest results"""
    
    @staticmethod
    def save_backtest(strategy_name: str, symbol: str, start_date: date, end_date: date,
                      initial_capital: float, final_capital: float, **kwargs):
        """Save backtest results"""
        session = get_session()
        try:
            backtest = Backtest(
                strategy_name=strategy_name,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                final_capital=final_capital,
                total_return=final_capital - initial_capital,
                total_return_pct=((final_capital - initial_capital) / initial_capital) * 100,
                **kwargs
            )
            session.add(backtest)
            session.commit()
            return backtest
        finally:
            session.close()
    
    @staticmethod
    def get_backtest_results(strategy_name: str, symbol: str = None) -> List[Backtest]:
        """Get backtest history"""
        session = get_session()
        try:
            query = session.query(Backtest).filter_by(strategy_name=strategy_name)
            if symbol:
                query = query.filter_by(symbol=symbol)
            return query.order_by(desc(Backtest.created_at)).all()
        finally:
            session.close()
