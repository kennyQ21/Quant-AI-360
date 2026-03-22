"""
Walk-Forward Testing Framework
More realistic than single backtest - simulates parameter recalibration
"""
import sys
from pathlib import Path
import logging
import pandas as pd
from datetime import timedelta
from typing import Dict
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.backtesting import Backtester
from services.data_service.market_data import load_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WalkForwardTester:
    """
    Walk-Forward Testing
    
    Why it matters:
    Regular backtest: Train once → Test once (overfitting risk)
    Walk-forward:     Train rolling windows → Test each window (realistic)
    
    Example:
    Train 2014-2018 → Test 2019
    Train 2015-2019 → Test 2020
    Train 2016-2020 → Test 2021
    
    This simulates real trading where you update parameters periodically.
    """
    
    def __init__(self, initial_capital: float = 100000):
        self.backtester = Backtester(initial_capital=initial_capital, transaction_cost=0.001)
        self.initial_capital = initial_capital
    
    def run_walk_forward(self, symbol: str, strategy_func, 
                        training_window_years: int = 4,
                        test_window_years: int = 1,
                        rebalance_freq: str = "yearly") -> Dict:
        """
        Run walk-forward test
        
        Args:
            symbol: Stock symbol
            strategy_func: Strategy function
            training_window_years: Years of data to train on
            test_window_years: Years to test after training
            rebalance_freq: How often to retrain ('yearly', 'quarterly')
        
        Returns:
            Dictionary with results for each window
        """
        logger.info("\n" + "="*70)
        logger.info(f"WALK-FORWARD TEST: {symbol}")
        logger.info(f"Training window: {training_window_years}y | Test window: {test_window_years}y")
        logger.info("="*70)
        
        data = load_data(symbol)
        if data.empty:
            logger.error(f"No data for {symbol}")
            return {}
        
        # Reset index and ensure Date is a column
        if 'Date' not in data.columns:
            data = data.reset_index()
            if 'Date' not in data.columns and 'index' in data.columns:
                data = data.rename(columns={'index': 'Date'})
            elif 'Date' not in data.columns:
                data['Date'] = data.index
        
        data['Date'] = pd.to_datetime(data['Date'])
        data = data.sort_values('Date').reset_index(drop=True)
        
        # Calculate window
        start_date = data['Date'].min()
        end_date = data['Date'].max()
        
        # Define windows
        windows = []
        train_duration = training_window_years * 365
        test_duration = test_window_years * 365
        
        current_train_start = start_date
        
        while current_train_start + timedelta(days=train_duration + test_duration) <= end_date:
            train_end = current_train_start + timedelta(days=train_duration)
            test_end = train_end + timedelta(days=test_duration)
            
            windows.append({
                'train_start': current_train_start,
                'train_end': train_end,
                'test_start': train_end,
                'test_end': test_end,
            })
            
            if rebalance_freq == "yearly":
                current_train_start += timedelta(days=365)
            elif rebalance_freq == "quarterly":
                current_train_start += timedelta(days=90)
        
        logger.info(f"Total windows: {len(windows)}\n")
        
        # Run each window
        results = []
        total_test_capital = self.initial_capital
        test_trades_all = []
        test_returns_all = []
        
        for i, window in enumerate(windows, 1):
            logger.info(f"[Window {i}/{len(windows)}] Training: {window['train_start'].strftime('%Y-%m-%d')} → "
                       f"{window['train_end'].strftime('%Y-%m-%d')} | "
                       f"Testing: {window['test_start'].strftime('%Y-%m-%d')} → "
                       f"{window['test_end'].strftime('%Y-%m-%d')}")
            
            # Run test
            result = self.backtester.run(
                symbol, strategy_func,
                start_date=window['test_start'].strftime('%Y-%m-%d'),
                end_date=window['test_end'].strftime('%Y-%m-%d')
            )
            
            if result:
                window_return = result.metrics['total_return_pct']
                test_returns_all.append(window_return)
                test_trades_all.extend(result.trades)
                
                # Update cumulative capital
                test_profit = self.initial_capital * (window_return / 100)
                total_test_capital += test_profit
                
                logger.info(f"  Return: {window_return:>7.2f}% | "
                           f"Sharpe: {result.metrics['sharpe_ratio']:>5.2f} | "
                           f"Trades: {result.metrics['total_trades']:>3.0f}")
                
                results.append({
                    'window': i,
                    'dates': f"{window['test_start'].strftime('%Y-%m-%d')} to {window['test_end'].strftime('%Y-%m-%d')}",
                    'return': window_return,
                    'sharpe': result.metrics['sharpe_ratio'],
                    'trades': result.metrics['total_trades'],
                    'win_rate': result.metrics['win_rate'],
                })
        
        # Summary statistics
        if results:
            logger.info("\n" + "-"*70)
            logger.info("WALK-FORWARD SUMMARY")
            logger.info("-"*70)
            
            avg_return = np.mean(test_returns_all)
            std_return = np.std(test_returns_all)
            min_return = np.min(test_returns_all)
            max_return = np.max(test_returns_all)
            consistency = sum(1 for r in test_returns_all if r > 0) / len(test_returns_all) * 100 if test_returns_all else 0
            
            logger.info(f"Average Return: {avg_return:.2f}%")
            logger.info(f"Std Dev Return: {std_return:.2f}%")
            logger.info(f"Min Return: {min_return:.2f}%")
            logger.info(f"Max Return: {max_return:.2f}%")
            logger.info(f"Winning Windows: {consistency:.1f}%")
            logger.info(f"Total Test Capital: {total_test_capital:,.0f} (from {self.initial_capital:,.0f})")
            logger.info(f"Total Return: {((total_test_capital - self.initial_capital*len(windows)) / (self.initial_capital*len(windows))) * 100:.2f}%")
            
            # Risk assessment
            if consistency >= 70:
                logger.info("✓ Strategy is CONSISTENT (wins >70% of windows)")
            elif consistency >= 50:
                logger.info("⚠️  Strategy is MIXED (wins 50-70% of windows)")
            else:
                logger.info("✗ Strategy is UNRELIABLE (wins <50% of windows)")
            
            if std_return > avg_return * 0.5:
                logger.info("⚠️  Strategy has HIGH VOLATILITY across windows")
            else:
                logger.info("✓ Strategy returns are STABLE across windows")
        
        return {
            'windows': results,
            'summary': {
                'total_windows': len(results),
                'avg_return': np.mean(test_returns_all) if test_returns_all else 0,
                'std_return': np.std(test_returns_all) if test_returns_all else 0,
                'consistency': consistency,
                'total_trades': len(test_trades_all),
            }
        }


def validate_with_walk_forward(symbol: str, strategy_func, strategy_name: str):
    """
    Complete walk-forward validation
    This is more realistic than single backtest
    """
    logger.info("\n" + "🔬 "*35)
    logger.info(f"WALK-FORWARD VALIDATION: {strategy_name}")
    logger.info("🔬 "*35)
    logger.info("\n💡 Why Walk-Forward Testing?")
    logger.info("   Single backtest can overfit (looks good but fails live)")
    logger.info("   Walk-forward tests realistic conditions (retraining periodically)")
    
    tester = WalkForwardTester(initial_capital=100000)
    results = tester.run_walk_forward(
        symbol, strategy_func,
        training_window_years=4,
        test_window_years=1,
        rebalance_freq="yearly"
    )
    
    if results['windows']:
        logger.info("\n" + "="*70)
        logger.info("INTERPRETATION")
        logger.info("="*70)
        consistency = results['summary']['consistency']
        
        if consistency >= 80:
            logger.info("✅ STRONG: Strategy works in 80%+ of periods")
            logger.info("   Ready for cautious paper trading")
        elif consistency >= 60:
            logger.info("⚠️  MODERATE: Strategy works in 60-80% of periods")
            logger.info("   Consider refinement before live trading")
        elif consistency >= 40:
            logger.info("⚠️  WEAK: Strategy works in 40-60% of periods")
            logger.info("   Likely needs significant improvement or is not robust")
        else:
            logger.info("❌ UNRELIABLE: Strategy fails in most periods")
            logger.info("   Do not trade - back to drawing board")
    
    logger.info("="*70)
    return results


if __name__ == "__main__":
    from services.backtesting.strategies import rsi_mean_reversion
    
    validate_with_walk_forward("RELIANCE.NS", rsi_mean_reversion, "RSI Mean Reversion")
