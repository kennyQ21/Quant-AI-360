"""
SMC FRAMEWORK - QUICK REFERENCE & CHEAT SHEET

Professional Smart Money Concepts Price Action System
All 7 detectors + Confluence scoring + Scanner ready to use
"""

# ============================================================================
# QUICK START - RUN ALL DETECTORS + SCORE
# ============================================================================

import pandas as pd
from services.price_action import (
    OrderFlowAnalyzer, LiquidityDetector, FVGDetector, IFVGMonitor,
    AMDDetector, VCPDetector, BreakoutDetector
)
from services.strategy_engine import ConfluenceEngine

# Load your OHLCV data
df = pd.read_csv('AAPL.csv', parse_dates=['Date'], index_col='Date')

# Initialize all detectors
of = OrderFlowAnalyzer()
liq = LiquidityDetector()
fvg = FVGDetector()
ifvg = IFVGMonitor()
amd = AMDDetector()
vcp = VCPDetector()
bo = BreakoutDetector()

# Run detectors
of_result = of.analyze(df)
liq_result = liq.analyze(df)
fvg_result = fvg.analyze(df)
ifvg_result = ifvg.analyze()  # Note: No df parameter
amd_result = amd.analyze(df)
vcp_result = vcp.analyze(df)
bo_result = bo.analyze(df)

# Score with confluence
engine = ConfluenceEngine()
setup = engine.score_setup(
    order_flow=of_result,
    liquidity=liq_result,
    fvg=fvg_result,
    ifvg=ifvg_result,
    amd=amd_result,
    vcp=vcp_result,
    breakout=bo_result,
    current_price=df['Close'].iloc[-1]
)

if setup:
    print(f"Signal: {setup.signal_name}")
    print(f"Score: {setup.score:.0f}/100 ({setup.confidence})")
    print(f"Entry: ${setup.entry_price:.2f}")
    print(f"Stop: ${setup.stop_loss:.2f}")
    print(f"Target 1: ${setup.target1:.2f}")
    print(f"Target 2: ${setup.target2:.2f}")


# ============================================================================
# SCAN MULTIPLE STOCKS
# ============================================================================

from services.strategy_engine import SMCScanner

def load_data(symbol: str) -> pd.DataFrame:
    """Your data loader"""
    return pd.read_csv(f"data/{symbol}.csv", parse_dates=['Date'], index_col='Date')

scanner = SMCScanner(
    symbols=['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA'],
    min_score=50.0,  # Skip setups below this score
    max_results=20   # Return top 20
)

results = scanner.scan_all(data_loader=load_data)
scanner.print_results(results)
scanner.export_results(results, 'smc_setups.csv')


# ============================================================================
# DETECTOR DETAILS & OUTPUT FORMATS
# ============================================================================

# 1. ORDER FLOW ANALYZER
# Returns: MarketStructure dataclass
# Key Fields:
#   - trend: 'UPTREND' | 'DOWNTREND' | 'RANGE'
#   - structure_quality: 0-5 (how many confirming structure points)
#   - last_bos: StructurePoint (last Break of Structure)
#   - last_choch: StructurePoint (Change of Character)
#   - is_fresh_choch: bool (just triggered)

# 2. LIQUIDITY DETECTOR
# Returns: Dict with 'liquidity_levels' list
# Each level:
#   - price: float
#   - type: 'EQUAL_HIGH' | 'EQUAL_LOW' | 'PREV_DAY_HIGH' | 'PREV_DAY_LOW' | 'RANGE_HIGH' | 'RANGE_LOW'
#   - touches: int (how many times price tested)
#   - strength: 0-100 (higher = more reliable)

# 3. FVG DETECTOR (Fair Value Gap)
# Returns: Dict with FVG statistics
# Key Fields:
#   - total_fvgs: int (all detected gaps)
#   - fresh_fvgs: int (untested, full potential)
#   - tested_fvgs: int (touched but not filled)
#   - filled_fvgs: int (price closed inside)
#   - violated_fvgs: int (price rejected the zone)
# Each FVG:
#   - top: float
#   - bottom: float
#   - direction: 'BULLISH' | 'BEARISH'
#   - state: FVGState.FRESH | TESTED | FILLED | VIOLATED
#   - gap_size_pct: float (0.2% - 3.0%)

# 4. IFVG MONITOR (Inverse FVG)
# Returns: Dict with violated FVGs acting as S/R
# Key Fields:
#   - ifvgs: list (violated zones)
#   - resistance_ifvgs: list (converted to resistance)
#   - support_ifvgs: list (converted to support)
# Note: IFVG maintains state - call analyze() with NO parameters

# 5. AMD DETECTOR (Accumulation-Manipulation-Distribution)
# Returns: Dict with 3-phase progression
# Key Fields:
#   - phase: 'ACCUMULATION' | 'MANIPULATION' | 'DISTRIBUTION' | 'NONE'
#   - setup_quality: 0-100
#   - accumulation_range: [start_idx, end_idx]
#   - manipulation_candle: idx
#   - distribution_direction: 'UP' | 'DOWN'

# 6. VCP DETECTOR (Volatility Contraction Pattern)
# Returns: Dict with consolidation + breakout
# Key Fields:
#   - phase: 'NONE' | 'PATTERN_FORMING' | 'BREAKOUT_TRIGGERED'
#   - corrections: list of correction details
#   - breakout_level: float
#   - volume_multiple: float (at breakout)

# 7. BREAKOUT DETECTOR
# Returns: Dict with consolidation breakout details
# Key Fields:
#   - phase: 'NONE' | 'CONSOLIDATION' | 'BREAKOUT_TRIGGERED'
#   - consolidation: {high, low, range_pct, duration, volume_ratio, quality}
#   - breakout: {direction, entry_price, stop_price, volume_multiple, score}
#   - retest: {retest_level, retest_type} (optional)


# ============================================================================
# CONFLUENCE SCORING LOGIC
# ============================================================================

# Scoring Breakdown (0-100 pts total):
score_matrix = {
    'Order Flow': {
        'Bullish UPTREND': 20,
        'Bearish DOWNTREND': 20,
        'RANGE (neutral)': 5,
        'NONE': 0,
    },
    'Liquidity': {
        'At Entry (swept)': 20,
        'Near Entry': 15,
        'Present': 5,
        'Absent': 0,
    },
    'FVG': {
        'Fresh (untested)': 15,
        'Tested': 12,
        'Filled/Violated': 5,
        'None': 0,
    },
    'AMD': {
        'Complete 3-Phase': 15,
        'Distribution Phase': 12,
        'Accumulation': 8,
        'None': 0,
    },
    'VCP/Breakout': {
        'VCP Triggered': 12,
        'Breakout Triggered': 12,
        'Pattern Forming': 5,
        'None': 0,
    },
    'IFVG': {
        '2+ Zones': 10,
        '1 Zone': 6,
        'None': 0,
    },
    'Volume': {
        'Multi-detector confirmation': 5,
        'None': 0,
    }
}

# Signal Confidence Levels:
# - 75+: HIGH PROBABILITY → Execute
# - 50-74: MEDIUM PROBABILITY → Wait for additional confluence
# - <50: SKIP → Insufficient setup quality


# ============================================================================
# PARAMETER TUNING
# ============================================================================

# OrderFlowAnalyzer
of = OrderFlowAnalyzer()
# Key threshold: lookback=5 for swing detection (default)
# Adjust for different timeframes:
#   - 5m: lookback=3-5
#   - 15m: lookback=5-7
#   - 1h: lookback=5-10
#   - 4h: lookback=8-12
#   - 1d: lookback=5-8

# LiquidityDetector
liq = LiquidityDetector()
# Key threshold: tolerance=0.3% for equal levels
# Adjust based on stock volatility:
#   - Penny stocks: 0.5-1.0%
#   - Blue chips: 0.2-0.3%
#   - Crypto: 0.5-1.0%

# FVGDetector
fvg = FVGDetector()
# Key thresholds:
#   - min_gap_pct: 0.2% (minimum imbalance size)
#   - max_gap_pct: 3.0% (maximum imbalance size)
# Adjust for different volatility regimes

# VCPDetector
vcp = VCPDetector(min_corrections=2, max_final_correction_pct=5.0)
# Key thresholds:
#   - min_corrections: 2 (minimum required)
#   - max_final_correction_pct: 5% (must be very tight)

# BreakoutDetector
bo = BreakoutDetector(min_bars=10, max_bars=40, max_range_pct=10.0)
# Key thresholds:
#   - min_bars: 10 (minimum consolidation)
#   - max_bars: 40 (maximum consolidation)
#   - max_range_pct: 10% (range tightness)

# ConfluenceEngine
engine = ConfluenceEngine(
    stop_loss_pct=2.0,    # 2% from entry
    target_ratio=2.0      # 1:2 risk:reward
)
# Adjust based on risk tolerance:
#   - Conservative: stop_loss_pct=1.0, target_ratio=3.0
#   - Aggressive: stop_loss_pct=3.0, target_ratio=1.5


# ============================================================================
# WORKING WITH STATE (IFVG)
# ============================================================================

# IFVG is stateful - it accumulates violations over time

ifvg = IFVGMonitor()

# On each new candle:
df_new = df.iloc[-10:]  # New 10 candles

# 1. Update FVG detector (creates new FVGs)
fvg.analyze(df_new)

# 2. Check for violations in new FVGs
for fvg_item in fvg.fvgs:  # Access FVG container
    if fvg_item.state == fvg_item.state.VIOLATED:
        ifvg.register_violation(fvg_item)

# 3. Check IFVG touches
ifvg.check_ifvg_touches(df_new['Close'].iloc[-1])

# 4. Get IFVG result
ifvg_result = ifvg.analyze()


# ============================================================================
# INTEGRATION WITH PHASE 2 BACKTESTER
# ============================================================================

# Use backtester to validate SMC setups historically

from services.backtesting import SimpleBacktester

def smc_strategy(df):
    """Using SMC signals for entry/exit"""
    positions = []
    
    for i in range(200, len(df)):
        current_df = df.iloc[:i+1]
        
        # Run all detectors
        of = OrderFlowAnalyzer().analyze(current_df)
        liq = LiquidityDetector().analyze(current_df)
        fvg = FVGDetector().analyze(current_df)
        amd = AMDDetector().analyze(current_df)
        vcp = VCPDetector().analyze(current_df)
        bo = BreakoutDetector().analyze(current_df)
        
        # Score
        engine = ConfluenceEngine()
        setup = engine.score_setup(
            order_flow=of, liquidity=liq, fvg=fvg, ifvg=None,
            amd=amd, vcp=vcp, breakout=bo,
            current_price=df['Close'].iloc[i]
        )
        
        # Generate signals
        if setup and setup.score >= 75:
            signal = {
                'entry': setup.entry_price,
                'stop': setup.stop_loss,
                'target': setup.target1,
                'direction': 'BUY' if setup.direction == 'LONG' else 'SELL'
            }
            positions.append(signal)
    
    return positions

# Backtest the strategy
backtester = SimpleBacktester()
results = backtester.backtest(smc_strategy, df)
print(results)


# ============================================================================
# DEBUGGING & ANALYSIS
# ============================================================================

# Print detailed detector output
print("\n=== ORDER FLOW ===")
print(f"Trend: {of_result.trend}")
print(f"Quality: {of_result.structure_quality}/5")
if of_result.last_bos:
    print(f"Recent BOS: ${of_result.last_bos.price} at candle #{of_result.last_bos.index}")

print("\n=== LIQUIDITY LEVELS ===")
for level in liq_result.get('liquidity_levels', []):
    print(f"{level.type}: ${level.price:.2f} (touches: {level.touches}, strength: {level.strength})")

print("\n=== FVG STATES ===")
print(f"Fresh: {fvg_result.get('fresh_fvgs', 0)}")
print(f"Tested: {fvg_result.get('tested_fvgs', 0)}")
print(f"Filled: {fvg_result.get('filled_fvgs', 0)}")
print(f"Violated: {fvg_result.get('violated_fvgs', 0)}")

# Check for specific patterns
if amd_result['phase'] == 'DISTRIBUTION':
    print("\n⚠️ AMD DISTRIBUTION DETECTED - Potential directional move")

if bo_result['phase'] == 'BREAKOUT_TRIGGERED':
    print(f"\n✓ BREAKOUT TRIGGERED: {bo_result['breakout']['direction']}")
    print(f"  Entry: ${bo_result['breakout']['entry_price']:.2f}")
    print(f"  Volume Multiple: {bo_result['breakout']['volume_multiple']:.2f}x")


# ============================================================================
# USEFUL SNIPPETS
# ============================================================================

# Convert results to DataFrame for analysis
import json

# Save setup details to JSON
if setup:
    setup_dict = {
        'signal': setup.signal_name,
        'score': setup.score,
        'components': setup.components,
        'entry': setup.entry_price,
        'stop': setup.stop_loss,
        'target1': setup.target1,
    }
    with open('last_setup.json', 'w') as f:
        json.dump(setup_dict, f, indent=2)

# Track detector evolution over time
detector_history = []

for i in range(100, len(df)):
    current_df = df.iloc[:i+1]
    
    of = OrderFlowAnalyzer().analyze(current_df)
    fvg = FVGDetector().analyze(current_df)
    
    detector_history.append({
        'candle': i,
        'price': df['Close'].iloc[i],
        'trend': of.trend,
        'fvg_count': fvg.get('total_fvgs', 0),
    })

history_df = pd.DataFrame(detector_history)
history_df.to_csv('detector_evolution.csv', index=False)


# ============================================================================
# COMMON ISSUES & SOLUTIONS
# ============================================================================

# Issue: No setups found
# Solution:
#   1. Check if min_score is too high (try 50)
#   2. Verify order flow is directional (not RANGE)
#   3. Ensure data has 200+ candles
#   4. Check data quality (no gaps, proper OHLCV)

# Issue: Too many false signals
# Solution:
#   1. Increase min_score threshold (75+)
#   2. Require more confluence components
#   3. Tighten liquidity tolerance (0.2%)
#   4. Increase FVG gap thresholds (0.5%-2.0%)

# Issue: IFVG showing no violations
# Solution:
#   1. Ensure FVGs are being created first
#   2. Check price action against FVG zones
#   3. IFVG only tracks completed violations
#   4. May need more historical data

# Issue: AMD not detecting 3-phase
# Solution:
#   1. AMD requires very specific sequencing
#   2. Check if accumulation exists (tight range, vol decline)
#   3. Look for false breakout (manipulation)
#   4. Ensure distribution move is strong enough

print("✅ SMC Framework loaded and ready to use")
