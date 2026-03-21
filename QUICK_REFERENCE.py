#!/usr/bin/env python3
"""
Quick Reference: Testing Your Trading Strategies
Copy-paste patterns for validating new strategies
"""

# ============================================================================
# PATTERN 1: Quick Single Backtest
# ============================================================================
from services.backtesting import Backtester

def test_simple():
    """Test: Single backtest on one stock"""
    backtester = Backtester(initial_capital=100000, transaction_cost=0.001)
    
    # Your strategy function
    def my_strategy(df):
        signals = []
        for idx, row in df.iterrows():
            if row['RSI_14'] < 30:
                signals.append('BUY')
            elif row['RSI_14'] > 70:
                signals.append('SELL')
            else:
                signals.append('HOLD')
        return signals
    
    # Run it
    result = backtester.run("RELIANCE.NS", my_strategy)
    
    # Check results
    print(f"Return: {result.metrics['total_return_pct']:.2f}%")
    print(f"Sharpe: {result.metrics['sharpe_ratio']:.2f}")
    print(f"Trades: {result.metrics['total_trades']:.0f}")
    
    return result


# ============================================================================
# PATTERN 2: Validate Quality (Enterprise Standards)
# ============================================================================
from services.backtesting import BacktestValidator

def test_with_validation():
    """Test: Single backtest + quality assessment"""
    
    backtester = Backtester(initial_capital=100000)
    validator = BacktestValidator()
    
    def my_strategy(df):
        # Your strategy here
        return ['BUY' if df['RSI_14'].iloc[i] < 30 else 'HOLD' for i in range(len(df))]
    
    # Run & validate
    result = backtester.run("RELIANCE.NS", my_strategy)
    
    if result:
        quality = validator.validate_backtest_quality(result.metrics)
        validator.print_validation_report("RELIANCE.NS", result.metrics, quality)
        
        # Make decision
        if quality in ['EXCELLENT', 'GOOD']:
            print("✅ Strategy looks promising!")
        else:
            print("❌ Strategy needs improvement")
    
    return result


# ============================================================================
# PATTERN 3: Multi-Stock Robustness Testing
# ============================================================================
def test_multi_stock():
    """Test: Does strategy work on multiple stocks?"""
    
    from services.backtesting.comprehensive_tester import StrategyTester
    
    def my_strategy(df):
        return ['BUY' if df['RSI_14'].iloc[i] < 30 else 'HOLD' for i in range(len(df))]
    
    tester = StrategyTester()
    results = tester.test_multi_stock(my_strategy, "My Strategy")
    
    # Check results
    print("Multi-Stock Results:")
    for stock_result in results['stocks']:
        print(f"  {stock_result['symbol']}: {stock_result['return']:.2f}% return")


# ============================================================================
# PATTERN 4: Market Period Testing (Bull/Crash/etc.)
# ============================================================================
def test_market_periods():
    """Test: How does strategy perform in different markets?"""
    
    from services.backtesting.comprehensive_tester import StrategyTester
    
    def my_strategy(df):
        return ['BUY' if df['RSI_14'].iloc[i] < 30 else 'HOLD' for i in range(len(df))]
    
    tester = StrategyTester()
    results = tester.test_market_periods(my_strategy, "My Strategy")
    
    # Check results
    print("Market Period Results:")
    for period_result in results['periods']:
        print(f"  {period_result['period']}: {period_result['return']:.2f}% return")


# ============================================================================
# PATTERN 5: Walk-Forward Testing (Most Realistic)
# ============================================================================
def test_walk_forward():
    """Test: Rolling window backtests (simulates real trading)"""
    
    from services.backtesting.walk_forward import WalkForwardTester
    
    def my_strategy(df):
        return ['BUY' if df['RSI_14'].iloc[i] < 30 else 'HOLD' for i in range(len(df))]
    
    tester = WalkForwardTester(initial_capital=100000)
    results = tester.run_walk_forward(
        "RELIANCE.NS",
        my_strategy,
        training_window_years=4,
        test_window_years=1
    )
    
    # Check results
    summary = results['summary']
    print(f"Average Return: {summary['avg_return']:.2f}%")
    print(f"Consistency: {summary['consistency']:.1f}%")
    print(f"Total Trades: {summary['total_trades']:.0f}")
    
    # Interpretation
    if summary['consistency'] >= 80:
        print("✅ STRONG: Strategy is consistent across time periods")
    elif summary['consistency'] >= 60:
        print("⚠️  MODERATE: Strategy works sometimes, needs improvement")
    else:
        print("❌ WEAK: Strategy is unreliable")


# ============================================================================
# PATTERN 6: FULL VALIDATION (Everything)
# ============================================================================
def test_full_validation():
    """Test: Complete validation suite (what production uses)"""
    
    from run_full_validation import run_full_validation
    
    def my_strategy(df):
        return ['BUY' if df['RSI_14'].iloc[i] < 30 else 'HOLD' for i in range(len(df))]
    
    # This runs ALL 7 validation checks
    run_full_validation(my_strategy, "My Strategy Name")
    
    # Output:
    # 1. Basic validation (data, bias, costs, metrics)
    # 2. Multi-stock testing (5 stocks)
    # 3. Market period testing (4 regimes)
    # 4. Walk-forward testing (6 rolling windows)
    # 5. Benchmark comparison (vs buy-and-hold)
    # + Comprehensive recommendations


# ============================================================================
# PATTERN 7: Store Results in Database
# ============================================================================
def test_and_store():
    """Test: Run backtest and save results to PostgreSQL"""
    
    from services.backtesting import Backtester
    from storage.queries import BacktestQueries
    
    def my_strategy(df):
        return ['BUY' if df['RSI_14'].iloc[i] < 30 else 'HOLD' for i in range(len(df))]
    
    # Run backtest
    backtester = Backtester()
    result = backtester.run("RELIANCE.NS", my_strategy)
    
    # Save to database
    if result:
        BacktestQueries.save_backtest(
            strategy_name="My Strategy",
            symbol="RELIANCE.NS",
            metrics=result.metrics,
            trades=result.trades
        )
        print("✅ Results saved to PostgreSQL")
    
    # Retrieve later
    all_results = BacktestQueries.get_backtest_results("My Strategy")
    print(f"Found {len(all_results)} historical backtests")


# ============================================================================
# PATTERN 8: Compare Multiple Strategies
# ============================================================================
def test_strategy_comparison():
    """Test: Which strategy is best?"""
    
    from services.backtesting import Backtester
    from services.backtesting import BacktestValidator
    
    strategies = {
        "RSI Simple": lambda df: ['BUY' if df['RSI_14'].iloc[i] < 30 else 'HOLD' for i in range(len(df))],
        "MA Crossover": lambda df: ['BUY' if df['SMA_50'].iloc[i] > df['SMA_200'].iloc[i] else 'HOLD' for i in range(len(df))],
        "Hybrid": lambda df: ['BUY' if (df['RSI_14'].iloc[i] < 30) and (df['SMA_50'].iloc[i] > df['SMA_200'].iloc[i]) else 'HOLD' for i in range(len(df))],
    }
    
    backtester = Backtester()
    validator = BacktestValidator()
    
    results = {}
    for name, strategy in strategies.items():
        result = backtester.run("RELIANCE.NS", strategy)
        if result:
            quality = validator.validate_backtest_quality(result.metrics)
            results[name] = {
                'return': result.metrics['total_return_pct'],
                'sharpe': result.metrics['sharpe_ratio'],
                'quality': quality
            }
    
    # Ranking
    print("Strategy Comparison:")
    for name, metrics in sorted(results.items(), key=lambda x: x[1]['return'], reverse=True):
        print(f"  {name:20} | Return: {metrics['return']:7.2f}% | Sharpe: {metrics['sharpe']:5.2f} | Quality: {metrics['quality']}")


# ============================================================================
# DEFAULT: Create your own strategy
# ============================================================================
def my_custom_strategy(df):
    """
    Template for creating your own strategy
    
    Args:
        df: DataFrame with OHLCV data + 15 indicators
            Available columns: Open, High, Low, Close, Volume
            Indicators: SMA_20, SMA_50, SMA_200, RSI_14, MACD, BB_Upper, etc.
    
    Returns:
        List of signals: ['BUY', 'SELL', 'HOLD']
    
    Rules:
        - Use only PAST data (no lookahead)
        - Return exactly len(df) signals
        - Signals are: 'BUY', 'SELL', or 'HOLD'
    """
    signals = []
    
    for idx in range(len(df)):
        row = df.iloc[idx]
        
        # Your logic here
        rsi = row['RSI_14']
        price = row['Close']
        sma_20 = row['SMA_20']
        
        if rsi < 30 and price > sma_20:
            signals.append('BUY')
        elif rsi > 70:
            signals.append('SELL')
        else:
            signals.append('HOLD')
    
    return signals


# ============================================================================
# RUN EXAMPLES
# ============================================================================
if __name__ == "__main__":
    print("Choose which pattern to test:")
    print("  1. test_simple()")
    print("  2. test_with_validation()")
    print("  3. test_multi_stock()")
    print("  4. test_market_periods()")
    print("  5. test_walk_forward()")
    print("  6. test_full_validation()  # RECOMMENDED")
    print("  7. test_and_store()")
    print("  8. test_strategy_comparison()")
    print("\nRun: python QUICK_REFERENCE.py")
