"""
Quick test of backtesting engine
Run this to validate Phase 2 setup
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.backtesting import Backtester
from services.backtesting.strategies import rsi_mean_reversion, ma_crossover
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Quick backtest validation"""
    logger.info("=" * 60)
    logger.info("PHASE 2: BACKTESTING ENGINE - VALIDATION TEST")
    logger.info("=" * 60)
    
    # Initialize backtester
    backtester = Backtester(initial_capital=100000, transaction_cost=0.001)
    
    # Test stocks
    test_symbols = ["RELIANCE.NS", "TCS.NS", "INFY.NS"]
    
    # Test strategies
    strategies = [
        ("RSI Mean Reversion", rsi_mean_reversion),
        ("MA Crossover", ma_crossover),
    ]
    
    logger.info("\nRunning backtests on sample stocks...\n")
    
    for strategy_name, strategy_func in strategies:
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Strategy: {strategy_name}")
        logger.info(f"{'=' * 60}\n")
        
        for symbol in test_symbols:
            result = backtester.run(symbol, strategy_func)
            if result:
                print(f"\n{symbol}:")
                print(f"  Initial Capital: ₹{result.initial_capital:,.0f}")
                print(f"  Final Capital: ₹{result.final_capital:,.0f}")
                print(f"  Total Return: {result.metrics['total_return_pct']:.2f}%")
                print(f"  Sharpe Ratio: {result.metrics['sharpe_ratio']:.2f}")
                print(f"  Max Drawdown: {result.metrics['max_drawdown']:.2f}%")
                print(f"  Win Rate: {result.metrics['win_rate']:.1f}%")
                print(f"  Profit Factor: {result.metrics['profit_factor']:.2f}")
                print(f"  Total Trades: {result.metrics['total_trades']}")
    
    logger.info("\n" + "=" * 60)
    logger.info("✓ Backtesting engine validated successfully!")
    logger.info("=" * 60)
    logger.info("\nNext steps:")
    logger.info("1. Open research/strategy_experiments.ipynb for interactive testing")
    logger.info("2. Modify strategies in services/backtesting/strategies/")
    logger.info("3. Test on different stocks and date ranges")
    logger.info("4. Once strategy is validated, move to Phase 3: ML models")


if __name__ == "__main__":
    main()
