"""
Backtest Performance Metrics
Calculates risk, return, and performance metrics for strategy evaluation
"""
import numpy as np
from typing import Dict, List


class BacktestMetrics:
    """Calculate comprehensive backtest metrics"""
    
    @staticmethod
    def calculate_returns(equity_curve: List[float]) -> float:
        """Total return percentage"""
        if len(equity_curve) < 2:
            return 0.0
        initial = equity_curve[0]
        final = equity_curve[-1]
        return ((final - initial) / initial) * 100
    
    @staticmethod
    def calculate_sharpe_ratio(returns: np.ndarray, risk_free_rate: float = 0.0, periods_per_year: int = 252) -> float:
        """Sharpe ratio (risk-adjusted return)
        
        Higher is better. >1 is good, >2 is excellent
        """
        if len(returns) < 2:
            return 0.0
        
        excess_returns = returns - (risk_free_rate / periods_per_year)
        if excess_returns.std() == 0:
            return 0.0
        
        sharpe = (excess_returns.mean() * periods_per_year) / (excess_returns.std() * np.sqrt(periods_per_year))
        return float(sharpe)
    
    @staticmethod
    def calculate_max_drawdown(equity_curve: List[float]) -> float:
        """Maximum drawdown percentage
        
        Worst peak-to-trough decline during trading period
        """
        if len(equity_curve) < 2:
            return 0.0
        
        arr = np.array(equity_curve)
        running_max = np.maximum.accumulate(arr)
        drawdowns = (arr - running_max) / running_max
        max_dd = np.min(drawdowns)
        return float(max_dd * 100)
    
    @staticmethod
    def calculate_win_rate(trades: List[Dict]) -> float:
        """Percentage of winning trades"""
        if len(trades) == 0:
            return 0.0
        
        winning = sum(1 for trade in trades if float(trade.get('profit_loss', 0)) > 0)
        return (winning / len(trades)) * 100
    
    @staticmethod
    def calculate_profit_factor(trades: List[Dict]) -> float:
        """Profit factor = sum of profits / sum of losses
        
        >1.5 is good, >2.0 is excellent
        If all trades are winning: returns sum of profits
        """
        if len(trades) == 0:
            return 0.0
        
        gross_profit = sum(float(trade.get('profit_loss', 0)) for trade in trades if float(trade.get('profit_loss', 0)) > 0)
        gross_loss = abs(sum(float(trade.get('profit_loss', 0)) for trade in trades if float(trade.get('profit_loss', 0)) < 0))
        
        if gross_loss == 0:
            return gross_profit if gross_profit > 0 else 0.0
        
        return gross_profit / gross_loss
    
    @staticmethod
    def calculate_cagr(equity_curve: List[float], days: int) -> float:
        """Compound Annual Growth Rate
        
        Annualized return metric
        """
        if len(equity_curve) < 2 or days == 0:
            return 0.0
        
        initial = equity_curve[0]
        final = equity_curve[-1]
        years = days / 252  # Trading days per year
        
        if years == 0 or initial == 0:
            return 0.0
        
        cagr = (final / initial) ** (1 / years) - 1
        return float(cagr * 100)
    
    @staticmethod
    def calculate_recovery_factor(equity_curve: List[float], trades: List[Dict]) -> float:
        """Recovery Factor = Total Profit / Max Drawdown
        
        How much profit generated per unit of drawdown
        Higher is better
        """
        if len(equity_curve) < 2:
            return 0.0
        
        total_profit = equity_curve[-1] - equity_curve[0]
        max_dd_abs = abs(BacktestMetrics.calculate_max_drawdown(equity_curve) * equity_curve[0] / 100)
        
        if max_dd_abs == 0:
            return 0.0
        
        return total_profit / max_dd_abs
    
    @staticmethod
    def get_all_metrics(equity_curve: List[float], trades: List[Dict], days: int, 
                       initial_capital: float) -> Dict:
        """Calculate all metrics at once"""
        returns = np.array([
            (equity_curve[i+1] - equity_curve[i]) / equity_curve[i]
            for i in range(len(equity_curve)-1)
        ]) if len(equity_curve) > 1 else np.array([])
        
        return {
            "total_return_pct": BacktestMetrics.calculate_returns(equity_curve),
            "cagr": BacktestMetrics.calculate_cagr(equity_curve, days),
            "sharpe_ratio": BacktestMetrics.calculate_sharpe_ratio(returns),
            "max_drawdown": BacktestMetrics.calculate_max_drawdown(equity_curve),
            "win_rate": BacktestMetrics.calculate_win_rate(trades),
            "profit_factor": BacktestMetrics.calculate_profit_factor(trades),
            "recovery_factor": BacktestMetrics.calculate_recovery_factor(equity_curve, trades),
            "total_trades": len(trades),
            "winning_trades": sum(1 for t in trades if float(t.get('profit_loss', 0)) > 0),
            "losing_trades": sum(1 for t in trades if float(t.get('profit_loss', 0)) < 0),
        }
