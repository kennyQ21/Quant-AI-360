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
        
        winning = 0
        for trade in trades:
            pl = trade.get('profit_loss', 0)
            if hasattr(pl, 'iloc'):
                pl = pl.iloc[0]
            if float(pl) > 0:
                winning += 1
        return (winning / len(trades)) * 100

    @staticmethod
    def calculate_profit_factor(trades: List[Dict]) -> float:
        """Profit factor = sum of profits / sum of losses
        
        >1.5 is good, >2.0 is excellent
        If all trades are winning: returns sum of profits
        """
        if len(trades) == 0:
            return 0.0
        
        gross_profit = 0.0
        gross_loss = 0.0
        
        for trade in trades:
            pl = trade.get('profit_loss', 0)
            if hasattr(pl, 'iloc'):
                pl = float(pl.iloc[0])
            else:
                pl = float(pl)
                
            if pl > 0:
                gross_profit += pl
            elif pl < 0:
                gross_loss += abs(pl)
        
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
        
        # Helper to extract pl safely
        def safe_pl(t):
            pl = t.get('profit_loss', 0)
            if hasattr(pl, 'iloc'):
                return float(pl.iloc[0])
            return float(pl)

        return {
            "total_return_pct": BacktestMetrics.calculate_returns(equity_curve),
            "cagr": BacktestMetrics.calculate_cagr(equity_curve, days),
            "sharpe_ratio": BacktestMetrics.calculate_sharpe_ratio(returns),
            "max_drawdown": BacktestMetrics.calculate_max_drawdown(equity_curve),
            "win_rate": BacktestMetrics.calculate_win_rate(trades),
            "profit_factor": BacktestMetrics.calculate_profit_factor(trades),
            "recovery_factor": BacktestMetrics.calculate_recovery_factor(equity_curve, trades),
            "total_trades": len(trades),
            "winning_trades": sum(1 for t in trades if safe_pl(t) > 0),
            "losing_trades": sum(1 for t in trades if safe_pl(t) < 0),
        }

    @staticmethod
    def calculate_process_metrics(trades: List[Dict]) -> Dict:
        """
        Calculates institutional-grade process metrics from the desk manifesto.
        Requires 'pnl' and 'r_multiple' to be populated in trades.
        """
        if len(trades) == 0:
            return {}

        def safe_float(val):
            if hasattr(val, 'iloc'):
                return float(val.iloc[0])
            return float(val) if val is not None else 0.0

        winners = [safe_float(t.get('pnl', t.get('profit_loss', 0))) for t in trades if safe_float(t.get('pnl', t.get('profit_loss', 0))) > 0]
        losers = [safe_float(t.get('pnl', t.get('profit_loss', 0))) for t in trades if safe_float(t.get('pnl', t.get('profit_loss', 0))) < 0]
        
        win_rate = len(winners) / len(trades)
        loss_rate = 1.0 - win_rate
        
        avg_winner = np.mean(winners) if winners else 0.0
        avg_loser = abs(np.mean(losers)) if losers else 0.0
        
        # Expectancy per trade: (Win rate * Avg winner) - (Loss rate * Avg loser)
        expectancy = (win_rate * avg_winner) - (loss_rate * avg_loser)
        
        # R-Multiple Analysis
        r_multiples = [safe_float(t.get('r_multiple', 0)) for t in trades]
        avg_r_multiple = np.mean(r_multiples) if r_multiples else 0.0
        
        # Setup Quality vs Outcome
        # groups trades by setup quality 'score' mapping 1-3
        quality_map = {1: [], 2: [], 3: []}
        for t in trades:
            score = int(float(t.get('score', 1)))
            if score in quality_map:
                quality_map[score].append(safe_float(t.get('pnl', t.get('profit_loss', 0))))
                
        metrics = {
            "expectancy_dollars": float(expectancy),
            "win_rate_pct": float(win_rate * 100),
            "avg_r_multiple_achieved": float(avg_r_multiple),
            "is_win_rate_broken": bool((win_rate * 100) < 38.0 and len(trades) >= 20),
            "quality_performance": {
                str(score): {
                    "avg_pnl": float(np.mean(pnls)) if pnls else 0.0,
                    "trade_count": len(pnls)
                }
                for score, pnls in quality_map.items()
            }
        }
        return metrics
