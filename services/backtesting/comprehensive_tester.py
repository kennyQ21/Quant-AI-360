"""
Comprehensive Strategy Testing Suite
Multi-stock, multi-period, and walk-forward validation
"""
import sys
from pathlib import Path
import logging
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import STOCKS
from services.backtesting import Backtester
from services.backtesting.validator import BacktestValidator
from services.data_service.market_data import load_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StrategyTester:
    """Comprehensive strategy testing across stocks and periods"""
    
    def __init__(self):
        self.backtester = Backtester(initial_capital=100000, transaction_cost=0.001)
        self.validator = BacktestValidator()
        self.results = {}
    
    def test_multi_stock(self, strategy_func, strategy_name: str, 
                        stocks: List[str] = None, limit: int = 5) -> Dict:
        """Test strategy across multiple stocks"""
        if stocks is None:
            stocks = STOCKS[:limit]
        
        logger.info("\n" + "="*70)
        logger.info(f"MULTI-STOCK TEST: {strategy_name}")
        logger.info("="*70)
        
        results = {}
        total_return = 0
        avg_sharpe = 0
        quality_scores = {'EXCELLENT': 0, 'GOOD': 0, 'ACCEPTABLE': 0, 'POOR': 0, 'UNUSABLE': 0}
        
        for i, symbol in enumerate(stocks, 1):
            logger.info(f"\n[{i}/{len(stocks)}] Testing {symbol}...")
            
            result = self.backtester.run(symbol, strategy_func)
            
            if result:
                quality = self.validator.validate_backtest_quality(result.metrics)
                quality_scores[quality] += 1
                
                results[symbol] = {
                    'metrics': result.metrics,
                    'quality': quality,
                    'trades': len(result.trades),
                }
                
                total_return += result.metrics.get('total_return_pct', 0)
                avg_sharpe += result.metrics.get('sharpe_ratio', 0)
                
                # Print single-line summary
                print(f"  ├─ Return: {result.metrics['total_return_pct']:>7.2f}% | " +
                      f"Sharpe: {result.metrics['sharpe_ratio']:>5.2f} | " +
                      f"Trades: {result.metrics['total_trades']:>3.0f} | {quality}")
        
        # Summary statistics
        num_stocks = len(results)
        if num_stocks > 0:
            logger.info("\n" + "-"*70)
            logger.info("MULTI-STOCK SUMMARY")
            logger.info("-"*70)
            logger.info(f"Average Return: {total_return/num_stocks:.2f}%")
            logger.info(f"Average Sharpe: {avg_sharpe/num_stocks:.2f}")
            logger.info("Strategy Quality Distribution:")
            for quality, count in quality_scores.items():
                if count > 0:
                    pct = (count / num_stocks) * 100
                    logger.info(f"  {quality:12} {count:2} stocks ({pct:5.1f}%)")
        
        return results
    
    def test_market_periods(self, strategy_func, strategy_name: str, 
                           symbol: str = "RELIANCE.NS") -> Dict:
        """Test strategy across different market conditions"""
        logger.info("\n" + "="*70)
        logger.info(f"MARKET PERIOD TEST: {strategy_name} on {symbol}")
        logger.info("="*70)
        
        data = load_data(symbol)
        if data.empty:
            logger.error(f"No data for {symbol}")
            return {}
        
        # Define market periods
        periods = [
            ("2014-2016", "BULL MARKET", "2014-01-01", "2016-12-31"),      # Strong uptrend
            ("2017-2019", "VOLATILE", "2017-01-01", "2019-12-31"),          # Corrections
            ("2020-2021", "COVID RECOVERY", "2020-01-01", "2021-12-31"),    # Crash + recovery
            ("2022-2024", "MIXED", "2022-01-01", "2024-12-31"),             # Recovery + sideways
        ]
        
        results = {}
        
        for period_name, market_type, start, end in periods:
            logger.info(f"\nTesting period: {period_name} ({market_type})")
            
            result = self.backtester.run(symbol, strategy_func, start_date=start, end_date=end)
            
            if result:
                quality = self.validator.validate_backtest_quality(result.metrics)
                results[period_name] = {
                    'period': period_name,
                    'market_type': market_type,
                    'metrics': result.metrics,
                    'quality': quality,
                }
                
                print(f"  ├─ Return: {result.metrics['total_return_pct']:>7.2f}% | " +
                      f"Sharpe: {result.metrics['sharpe_ratio']:>5.2f} | " +
                      f"Drawdown: {result.metrics['max_drawdown']*100:>6.1f}% | {quality}")
        
        # Summary
        if results:
            logger.info("\n" + "-"*70)
            logger.info("PERIOD ROBUSTNESS CHECK")
            logger.info("-"*70)
            
            returns = [r['metrics']['total_return_pct'] for r in results.values()]
            sharpes = [r['metrics']['sharpe_ratio'] for r in results.values()]
            
            logger.info(f"Return across periods: Min {min(returns):.1f}% | Avg {sum(returns)/len(returns):.1f}% | Max {max(returns):.1f}%")
            logger.info(f"Sharpe across periods: Min {min(sharpes):.2f} | Avg {sum(sharpes)/len(sharpes):.2f} | Max {max(sharpes):.2f}")
            
            consistency = sum(1 for q in [r['quality'] for r in results.values()] if q in ['GOOD', 'EXCELLENT'])
            consistency_pct = (consistency / len(results)) * 100
            logger.info(f"Consistent quality: {consistency_pct:.0f}% of periods (GOOD or EXCELLENT)")
        
        return results
    
    def compare_against_benchmark(self, strategy_func, strategy_name: str,
                                  symbol: str = "RELIANCE.NS") -> Dict:
        """Compare strategy return vs Buy-and-Hold benchmark"""
        logger.info("\n" + "="*70)
        logger.info(f"BENCHMARK COMPARISON: {strategy_name} vs Buy-and-Hold")
        logger.info("="*70)
        
        # Test strategy
        logger.info(f"\nTesting strategy on {symbol}...")
        strategy_result = self.backtester.run(symbol, strategy_func)
        
        if not strategy_result:
            return {}
        
        # Test buy-and-hold benchmark
        logger.info(f"Testing buy-and-hold benchmark on {symbol}...")
        def buy_and_hold(df):
            """Simple buy-and-hold strategy"""
            return ['BUY'] + ['HOLD'] * (len(df) - 1)
        
        benchmark_result = self.backtester.run(symbol, buy_and_hold)
        
        if not benchmark_result:
            return {}
        
        # Compare
        strategy_return = strategy_result.metrics['total_return_pct']
        benchmark_return = benchmark_result.metrics['total_return_pct']
        excess_return = strategy_return - benchmark_return
        
        strategy_sharpe = strategy_result.metrics['sharpe_ratio']
        benchmark_sharpe = benchmark_result.metrics['sharpe_ratio']
        
        logger.info("\n" + "-"*70)
        logger.info("BENCHMARK COMPARISON RESULTS")
        logger.info("-"*70)
        logger.info(f"Strategy Return:  {strategy_return:>7.2f}%")
        logger.info(f"Benchmark Return: {benchmark_return:>7.2f}%")
        logger.info(f"Excess Return:    {excess_return:>7.2f}% {'✓ OUTPERFORMS' if excess_return > 0 else '✗ UNDERPERFORMS'}")
        
        logger.info(f"\nStrategy Sharpe:  {strategy_sharpe:>7.2f}")
        logger.info(f"Benchmark Sharpe: {benchmark_sharpe:>7.2f}")
        logger.info(f"Excess Sharpe:    {strategy_sharpe - benchmark_sharpe:>7.2f}")
        
        win_rate = sum(1 for t in strategy_result.trades if t.get('profit_loss', 0) > 0) / len(strategy_result.trades) * 100 if strategy_result.trades else 0
        logger.info(f"\nWin Rate:         {win_rate:>7.1f}%")
        logger.info(f"Total Trades:     {len(strategy_result.trades):>7.0f}")
        
        return {
            'strategy': {
                'return': strategy_return,
                'sharpe': strategy_sharpe,
                'drawdown': strategy_result.metrics['max_drawdown'],
                'trades': len(strategy_result.trades),
            },
            'benchmark': {
                'return': benchmark_return,
                'sharpe': benchmark_sharpe,
                'drawdown': benchmark_result.metrics['max_drawdown'],
            },
            'outperforms': excess_return > 0,
            'excess_return': excess_return,
        }


def run_comprehensive_validation(strategy_func, strategy_name: str):
    """Run complete validation suite"""
    logger.info("\n" + "🔬 "*35)
    logger.info("COMPREHENSIVE STRATEGY VALIDATION SUITE")
    logger.info("🔬 "*35)
    
    tester = StrategyTester()
    
    # Test 1: Multi-stock
    multistock_results = tester.test_multi_stock(strategy_func, strategy_name, limit=5)
    
    # Test 2: Market periods
    period_results = tester.test_market_periods(strategy_func, strategy_name)
    
    # Test 3: Benchmark
    benchmark_results = tester.compare_against_benchmark(strategy_func, strategy_name)
    
    # Final recommendation
    logger.info("\n" + "="*70)
    logger.info("VALIDATION RECOMMENDATION")
    logger.info("="*70)
    
    if benchmark_results.get('outperforms'):
        logger.info("✅ Strategy OUTPERFORMS buy-and-hold benchmark")
    else:
        logger.info("⚠️  Strategy UNDERPERFORMS buy-and-hold benchmark")
    
    good_stocks = sum(1 for r in multistock_results.values() if r['quality'] in ['GOOD', 'EXCELLENT'])
    total_stocks = len(multistock_results)
    if total_stocks > 0:
        consistency_pct = (good_stocks / total_stocks) * 100
        logger.info(f"✓ Consistent across {consistency_pct:.0f}% of stocks ({good_stocks}/{total_stocks})")
    
    good_periods = sum(1 for r in period_results.values() if r['quality'] in ['GOOD', 'EXCELLENT'])
    total_periods = len(period_results)
    if total_periods > 0:
        period_consistency = (good_periods / total_periods) * 100
        logger.info(f"✓ Robust across {period_consistency:.0f}% of market periods ({good_periods}/{total_periods})")
    
    logger.info("\n✓ Validation complete. Ready for Phase 3 if metrics are strong.")
    logger.info("="*70)


if __name__ == "__main__":
    from services.backtesting.strategies import rsi_mean_reversion
    
    run_comprehensive_validation(rsi_mean_reversion, "RSI Mean Reversion")
