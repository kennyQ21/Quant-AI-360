#!/usr/bin/env python3
"""
COMPLETE VALIDATION SUITE FOR TRADING STRATEGIES
Runs all 7 validation checks before Phase 3 ML

This is the professional-grade validation that quant shops run
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import sys
from pathlib import Path
import logging

sys.path.insert(0, str(Path(__file__).parent))

from services.backtesting.validator import BacktestValidator
from services.backtesting.walk_forward import validate_with_walk_forward
from services.backtesting.strategies import rsi_mean_reversion, ma_crossover

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


def print_header(title: str):
    """Print formatted header"""
    logger.info("\n" + "🔬 " * 30)
    logger.info(f"  {title}")
    logger.info("🔬 " * 30)


def run_full_validation(strategy_func, strategy_name: str, symbol: str = "RELIANCE.NS"):
    """
    Run complete validation suite (7 checks):
    
    1. ✓ Data Integrity (validator.py)
    2. ✓ Lookahead Bias Detection (validator.py)
    3. ✓ Transaction Costs Validation (validator.py)
    4. ✓ Metrics Evaluation (validator.py)
    5. ✓ Multi-Stock Robustness (comprehensive_tester.py)
    6. ✓ Market Period Stability (comprehensive_tester.py)
    7. ✓ Walk-Forward Consistency (walk_forward.py)
    """
    
    print_header(f"FULL VALIDATION: {strategy_name}")
    
    # First, ensure data is available
    logger.info("\n📥 Ensuring market data is loaded...")
    from services.data_service.market_data import download_and_save_stock
    try:
        download_and_save_stock(symbol)
        logger.info(f"✓ Data ready for {symbol}")
    except Exception as e:
        logger.error(f"Could not download data: {e}")
    
    logger.info("\nValidation checklist:")
    logger.info("  1. Data Integrity Check")
    logger.info("  2. Lookahead Bias Detection")
    logger.info("  3. Transaction Costs Validation")
    logger.info("  4. Metrics Evaluation")
    logger.info("  5. Multi-Stock Robustness")
    logger.info("  6. Market Period Stability")
    logger.info("  7. Walk-Forward Consistency Testing")
    logger.info("\nStarting validation...")
    
    # Check 1-4: Basic validation
    print_header("Step 1/3: Basic Validation Checks (Data, Bias, Costs, Metrics)")
    from services.backtesting import Backtester
    backtester = Backtester(initial_capital=100000, transaction_cost=0.001)
    
    # Run single backtest to get metrics
    result = backtester.run(symbol, strategy_func)
    if result:
        validator = BacktestValidator()
        quality = validator.validate_backtest_quality(result.metrics)
        validator.print_validation_report(symbol, result.metrics, quality)
    else:
        logger.error(f"Failed to run backtest for {symbol}")
    
    # Check 5-6: Multi-stock and market period testing
    print_header("Step 2/3: Robustness Testing (Multi-Stock & Market Periods)")
    from services.backtesting.comprehensive_tester import run_comprehensive_validation
    comprehensive_result = run_comprehensive_validation(strategy_func, strategy_name)
    logger.info(comprehensive_result)
    
    # Check 7: Walk-forward testing
    print_header("Step 3/3: Walk-Forward Testing (Consistency Over Time)")
    _ = validate_with_walk_forward(symbol, strategy_func, strategy_name)
    
    # Final recommendation
    print_header("FINAL VALIDATION REPORT")
    logger.info("\n✅ All 7 validation checks completed!\n")
    logger.info("Interpretation Guide:")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info("Check 1: Data Integrity")
    logger.info("  ✓ Missing values < 1%")
    logger.info("  ✓ No duplicate dates")
    logger.info("  ✓ Price movements reasonable (< 20% daily)")
    logger.info("")
    logger.info("Check 2: Lookahead Bias")
    logger.info("  ✓ Signals use only past data")
    logger.info("  ✓ No future price knowledge in strategy")
    logger.info("")
    logger.info("Check 3: Transaction Costs")
    logger.info("  ✓ Included 0.1% cost per trade (realistic)")
    logger.info("  ✓ Cost range 0.01%-1.0% acceptable")
    logger.info("")
    logger.info("Check 4: Metrics Evaluation")
    logger.info("  ✓ Sharpe Ratio > 1.0 (risk-adjusted returns)")
    logger.info("  ✓ Win Rate > 55% (more winners than losers)")
    logger.info("  ✓ Profit Factor > 1.5 (gross wins > 1.5x gross losses)")
    logger.info("  ✓ Max Drawdown < -25% (not too risky)")
    logger.info("")
    logger.info("Check 5: Multi-Stock Testing")
    logger.info("  ✓ Works on RELIANCE, TCS, HDFCBANK, INFY, SBIN")
    logger.info("  ✓ Not just one stock overfitting")
    logger.info("")
    logger.info("Check 6: Market Period Stability")
    logger.info("  ✓ Bull market (2014-2016): Strong returns")
    logger.info("  ✓ Volatile market (2017-2019): Moderate returns")
    logger.info("  ✓ Crash (2020-2021): Positive or small loss")
    logger.info("  ✓ Recovery (2022-2024): Positive returns")
    logger.info("")
    logger.info("Check 7: Walk-Forward Testing")
    logger.info("  ✓ Works in 80%+ of 1-year periods")
    logger.info("  ✓ Consistent performance over time")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info("\n✅ VALIDATION COMPLETE")
    logger.info("\nNext steps:")
    logger.info("  1. Review results above")
    logger.info("  2. If all checks pass → Ready for Phase 3: ML Models")
    logger.info("  3. If some checks fail → Refine strategy and retry")
    logger.info("  4. If most checks fail → Rethink strategy approach")


def run_multiple_strategies():
    """Validate multiple strategies"""
    print_header("BATCH VALIDATION: Multiple Strategies")
    
    strategies = [
        (rsi_mean_reversion, "RSI Mean Reversion"),
        (ma_crossover, "MA Crossover"),
    ]
    
    for strategy_func, strategy_name in strategies:
        logger.info(f"\n{'='*70}")
        logger.info(f"Validating: {strategy_name}")
        logger.info(f"{'='*70}")
        try:
            run_full_validation(strategy_func, strategy_name)
        except Exception as e:
            logger.error(f"Failed: {str(e)}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    # Run single strategy with full validation
    logger.info("Starting Trading Strategy Validation Suite\n")
    
    # Run one strategy completely
    run_full_validation(rsi_mean_reversion, "RSI Mean Reversion Strategy")
    
    # Optional: Run multiple strategies in batch
    # run_multiple_strategies()
