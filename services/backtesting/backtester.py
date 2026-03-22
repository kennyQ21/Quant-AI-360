"""
Backtesting Engine
Simulates trading strategies on historical data
"""
import sys
from pathlib import Path
import logging
from typing import Dict, List, Optional, Callable

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.data_service.market_data import load_data
from services.feature_service.indicators import add_features_to_data
from .metrics import BacktestMetrics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BacktestResult:
    """Results from a backtest run"""
    
    def __init__(self, strategy_name: str, symbol: str, initial_capital: float):
        self.strategy_name = strategy_name
        self.symbol = symbol
        self.initial_capital = initial_capital
        self.final_capital = initial_capital
        self.equity_curve = [initial_capital]
        self.trades = []
        self.signals = []
        self.start_date = None
        self.end_date = None
        self.metrics = {}
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "strategy": self.strategy_name,
            "symbol": self.symbol,
            "initial_capital": self.initial_capital,
            "final_capital": self.final_capital,
            "total_return_pct": self.metrics.get("total_return_pct", 0),
            "sharpe_ratio": self.metrics.get("sharpe_ratio", 0),
            "max_drawdown": self.metrics.get("max_drawdown", 0),
            "win_rate": self.metrics.get("win_rate", 0),
            "profit_factor": self.metrics.get("profit_factor", 0),
            "total_trades": len(self.trades),
            "winning_trades": self.metrics.get("winning_trades", 0),
            "start_date": str(self.start_date),
            "end_date": str(self.end_date),
        }
    
    def __repr__(self):
        return f"<BacktestResult {self.strategy_name} {self.symbol} {self.metrics.get('total_return_pct', 0):.2f}%>"


class Backtester:
    """Main backtesting engine"""
    
    def __init__(self, initial_capital: float = 100000, transaction_cost: float = 0.001):
        """
        Initialize backtester
        
        Args:
            initial_capital: Starting capital in currency units
            transaction_cost: Cost per trade as fraction (0.001 = 0.1%)
        """
        self.initial_capital = initial_capital
        self.transaction_cost = transaction_cost
    
    def run(self, symbol: str, strategy_func: Callable, 
            start_date: Optional[str] = None, end_date: Optional[str] = None) -> BacktestResult:
        """
        Run backtest on a stock with given strategy
        
        Args:
            symbol: Stock symbol (e.g. 'RELIANCE.NS')
            strategy_func: Function that takes DataFrame and returns signals
                          Should return DataFrame with 'signal' column (BUY/SELL/HOLD)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        
        Returns:
            BacktestResult object
        """
        logger.info(f"Starting backtest: {strategy_func.__name__} on {symbol}")
        
        # Load data
        data = load_data(symbol)
        if data.empty:
            logger.error(f"No data available for {symbol}")
            return None
        
        # Add features
        data = add_features_to_data(data)
        
        # Filter by date range
        if start_date:
            data = data[data.index.get_level_values(0) >= start_date] if 'Date' in data.index.names else data[data['Date'] >= start_date]
        if end_date:
            data = data[data.index.get_level_values(0) <= end_date] if 'Date' in data.index.names else data[data['Date'] <= end_date]
        
        if data.empty:
            logger.error(f"No data in date range for {symbol}")
            return None
        
        # Reset index to ensure Date is a column
        if 'Date' in data.index.names:
            data = data.reset_index()
        
        # Generate signals
        signals = strategy_func(data)
        data['signal'] = signals
        
        # Initialize result
        result = BacktestResult(strategy_func.__name__, symbol, self.initial_capital)
        result.start_date = data['Date'].iloc[0] if 'Date' in data.columns else data.index[0]
        result.end_date = data['Date'].iloc[-1] if 'Date' in data.columns else data.index[-1]
        
        # Run backtest
        position = None  # None = no position, 'LONG' = holding
        entry_price = 0
        entry_date = None
        
        for idx, row in data.iterrows():
            signal = row['signal'] if 'signal' in row else 'HOLD'
            # Ensure signal is a scalar string
            if hasattr(signal, 'item'):
                signal = signal.item()
            elif isinstance(signal, (list, tuple)):
                signal = signal[0] if signal else 'HOLD'
            
            price = row['Close'] if 'Close' in row else (row['close'] if 'close' in row else 0)
            # Ensure price is numeric
            if hasattr(price, 'item'):
                price = price.item()
            price = float(price) if price else 0
            
            date = row['Date'] if 'Date' in row else idx
            
            # Close position on SELL or other signal
            if position == 'LONG' and signal in ['SELL', 'HOLD']:
                exit_price = price
                profit_loss = (exit_price - entry_price) * 100  # Simplified: 100 shares
                profit_loss -= abs(profit_loss * self.transaction_cost)  # Transaction cost
                
                trade = {
                    'entry_date': entry_date,
                    'exit_date': date,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'profit_loss': profit_loss,
                    'profit_loss_pct': ((exit_price - entry_price) / entry_price * 100) - self.transaction_cost * 100,
                    'strategy': strategy_func.__name__,
                }
                result.trades.append(trade)
                
                # Update capital
                result.final_capital += profit_loss
                position = None
                
                logger.debug(f"CLOSE: {symbol} at {exit_price} on {date}, P&L: {profit_loss:.2f}")
            
            # Open position on BUY
            if position is None and signal == 'BUY':
                entry_price = price
                entry_date = date
                position = 'LONG'
                logger.debug(f"OPEN: {symbol} at {entry_price} on {date}")
            
            # Record equity curve
            result.equity_curve.append(result.final_capital)
        
        # Close any open position at end
        if position == 'LONG':
            final_price = data.iloc[-1]['Close'] if 'Close' in data.columns else data.iloc[-1].get('close', 0)
            profit_loss = (final_price - entry_price) * 100
            profit_loss -= abs(profit_loss * self.transaction_cost)
            result.final_capital += profit_loss
            result.trades.append({
                'entry_date': entry_date,
                'exit_date': result.end_date,
                'entry_price': entry_price,
                'exit_price': final_price,
                'profit_loss': profit_loss,
                'profit_loss_pct': ((final_price - entry_price) / entry_price * 100) - self.transaction_cost * 100,
                'strategy': strategy_func.__name__,
                'status': 'CLOSED AT END',
            })
        
        # Calculate metrics
        days = len(data)
        result.metrics = BacktestMetrics.get_all_metrics(
            result.equity_curve, result.trades, days, self.initial_capital
        )
        
        logger.info(f"Backtest complete: {result}")
        logger.info(f"  Total Return: {result.metrics['total_return_pct']:.2f}%")
        logger.info(f"  Sharpe Ratio: {result.metrics['sharpe_ratio']:.2f}")
        logger.info(f"  Max Drawdown: {result.metrics['max_drawdown']:.2f}%")
        logger.info(f"  Win Rate: {result.metrics['win_rate']:.2f}%")
        logger.info(f"  Profit Factor: {result.metrics['profit_factor']:.2f}")
        logger.info(f"  Total Trades: {len(result.trades)}")
        
        return result
    
    def run_multiple(self, symbols: List[str], strategy_func: Callable) -> Dict[str, BacktestResult]:
        """Run backtest on multiple stocks"""
        results = {}
        for symbol in symbols:
            result = self.run(symbol, strategy_func)
            if result:
                results[symbol] = result
        return results
