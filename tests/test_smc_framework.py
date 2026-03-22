"""
SMC FRAMEWORK INTEGRATION TEST
Demonstrates all 7 detectors + confluence engine in action

Test approach:
1. Load sample OHLCV data
2. Run each detector individually
3. Show detector outputs
4. Run confluence scoring
5. Generate final setup
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict

from services.price_action import (
    OrderFlowAnalyzer,
    LiquidityDetector,
    FVGDetector,
    IFVGMonitor,
    AMDDetector,
    VCPDetector,
    BreakoutDetector
)
from services.strategy_engine import ConfluenceEngine

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_sample_data(rows: int = 200, trend: str = 'UP') -> pd.DataFrame:
    """
    Generate synthetic OHLCV data for testing
    
    trend: 'UP', 'DOWN', or 'RANGE'
    """
    dates = [datetime.now() - timedelta(days=x) for x in range(rows, 0, -1)]
    
    closes = [100]
    
    for i in range(1, rows):
        if trend == 'UP':
            change = np.random.normal(0.3, 1.5)
        elif trend == 'DOWN':
            change = np.random.normal(-0.3, 1.5)
        else:  # RANGE
            change = np.random.normal(0, 1.0) if i < rows * 0.7 else np.random.normal(0.2, 1.5)
        
        new_close = closes[-1] + change
        closes.append(max(50, new_close))
    
    data = []
    for i, close in enumerate(closes):
        high = close + np.random.uniform(0, 2)
        low = close - np.random.uniform(0, 2)
        open_price = (closes[i-1] if i > 0 else close) + np.random.uniform(-0.5, 0.5)
        volume = np.random.uniform(1000000, 5000000)
        
        data.append({
            'Open': open_price,
            'High': max(high, close, open_price),
            'Low': min(low, close, open_price),
            'Close': close,
            'Volume': volume,
        })
    
    df = pd.DataFrame(data, index=pd.DatetimeIndex(dates))
    return df


def test_single_detector(detector_name: str, df: pd.DataFrame) -> None:
    """Test individual detector"""
    print(f"\n{'='*80}")
    print(f"TESTING: {detector_name.upper()}")
    print('='*80)
    
    try:
        if detector_name == 'order_flow':
            detector = OrderFlowAnalyzer()
        elif detector_name == 'liquidity':
            detector = LiquidityDetector()
        elif detector_name == 'fvg':
            detector = FVGDetector()
        elif detector_name == 'ifvg':
            detector = IFVGMonitor()
        elif detector_name == 'amd':
            detector = AMDDetector()
        elif detector_name == 'vcp':
            detector = VCPDetector()
        elif detector_name == 'breakout':
            detector = BreakoutDetector()
        else:
            print(f"Unknown detector: {detector_name}")
            return
        
        result = detector.analyze(df)
        
        # Print result
        if isinstance(result, dict):
            for key, value in result.items():
                if isinstance(value, (str, int, float)):
                    print(f"  {key}: {value}")
                elif isinstance(value, list) and len(value) > 0:
                    print(f"  {key}: {len(value)} items")
                    for item in value[:2]:  # Print first 2 items
                        print(f"    - {item}")
        
        print(f"✓ {detector_name.upper()} completed successfully")
        
    except Exception as e:
        print(f"✗ {detector_name.upper()} failed: {str(e)}")
        import traceback
        traceback.print_exc()


def test_all_detectors(df: pd.DataFrame) -> Dict:
    """Run all 7 detectors and return outputs"""
    print(f"\n{'='*80}")
    print("RUNNING ALL 7 DETECTORS")
    print('='*80)
    
    order_flow = OrderFlowAnalyzer()
    liquidity = LiquidityDetector()
    fvg = FVGDetector()
    ifvg = IFVGMonitor()
    amd = AMDDetector()
    vcp = VCPDetector()
    breakout = BreakoutDetector()
    
    results = {}
    
    try:
        results['order_flow'] = order_flow.analyze(df)
        print("✓ ORDER_FLOW")
    except Exception as e:
        print(f"✗ ORDER_FLOW: {str(e)}")
        results['order_flow'] = None
    
    try:
        results['liquidity'] = liquidity.analyze(df)
        print("✓ LIQUIDITY")
    except Exception as e:
        print(f"✗ LIQUIDITY: {str(e)}")
        results['liquidity'] = None
    
    try:
        results['fvg'] = fvg.analyze(df)
        print("✓ FVG")
    except Exception as e:
        print(f"✗ FVG: {str(e)}")
        results['fvg'] = None
    
    try:
        # IFVG doesn't take df - it maintains state
        results['ifvg'] = ifvg.analyze()
        print("✓ IFVG")
    except Exception as e:
        print(f"✗ IFVG: {str(e)}")
        results['ifvg'] = None
    
    try:
        results['amd'] = amd.analyze(df)
        print("✓ AMD")
    except Exception as e:
        print(f"✗ AMD: {str(e)}")
        results['amd'] = None
    
    try:
        results['vcp'] = vcp.analyze(df)
        print("✓ VCP")
    except Exception as e:
        print(f"✗ VCP: {str(e)}")
        results['vcp'] = None
    
    try:
        results['breakout'] = breakout.analyze(df)
        print("✓ BREAKOUT")
    except Exception as e:
        print(f"✗ BREAKOUT: {str(e)}")
        results['breakout'] = None
    
    return results


def test_confluence_scoring(detector_results: Dict, current_price: float) -> None:
    """Test confluence engine scoring"""
    print(f"\n{'='*80}")
    print("CONFLUENCE SCORING")
    print('='*80)
    
    engine = ConfluenceEngine(stop_loss_pct=2.0, target_ratio=2.0)
    
    setup = engine.score_setup(
        order_flow=detector_results.get('order_flow'),
        liquidity=detector_results.get('liquidity'),
        fvg=detector_results.get('fvg'),
        ifvg=detector_results.get('ifvg'),
        amd=detector_results.get('amd'),
        vcp=detector_results.get('vcp'),
        breakout=detector_results.get('breakout'),
        current_price=current_price
    )
    
    if setup:
        print("✓ SETUP FOUND")
        print(f"  Signal: {setup.signal_name}")
        print(f"  Score: {setup.score:.1f}/100 ({setup.confidence} confidence)")
        print(f"  Direction: {setup.direction}")
        print(f"  Entry: ${setup.entry_price:.2f}")
        print(f"  Stop Loss: ${setup.stop_loss:.2f}")
        print(f"  Target 1: ${setup.target1:.2f}")
        print(f"  Target 2: ${setup.target2:.2f}")
        print(f"  Components: {', '.join(setup.components)}")
        print("  Score breakdown:")
        print(f"    - Order Flow: {setup.order_flow_score} pts")
        print(f"    - Liquidity: {setup.liquidity_score} pts")
        print(f"    - FVG: {setup.fvg_score} pts")
        print(f"    - AMD: {setup.amd_score} pts")
        print(f"    - VCP/Breakout: {setup.vcp_score} pts")
        print(f"    - IFVG: {setup.ifvg_score} pts")
        print(f"    - Volume: {setup.volume_score} pts")
        print(f"  Notes: {setup.notes}")
    else:
        print("✗ NO SETUP (score too low or order flow not bullish/bearish)")


def run_full_integration_test():
    """Complete integration test"""
    print("\n" + "="*80)
    print("SMC FRAMEWORK - COMPLETE INTEGRATION TEST")
    print("="*80)
    
    # Generate test data
    print("\n[1] Generating synthetic OHLCV data...")
    df_uptrend = generate_sample_data(rows=200, trend='UP')
    print(f"✓ Generated {len(df_uptrend)} candles")
    print(f"  Price range: ${df_uptrend['Low'].min():.2f} - ${df_uptrend['High'].max():.2f}")
    
    # Test individual detectors (detailed)
    print("\n[2] Testing individual detectors...")
    for detector_name in ['order_flow', 'liquidity', 'fvg', 'amd', 'vcp', 'breakout']:
        test_single_detector(detector_name, df_uptrend)
    
    # Test all detectors together
    print("\n[3] Running all 7 detectors...")
    detector_results = test_all_detectors(df_uptrend)
    
    # Test confluence scoring
    print("\n[4] Testing confluence engine...")
    current_price = df_uptrend['Close'].iloc[-1]
    test_confluence_scoring(detector_results, current_price)
    
    # Test on different market conditions
    print("\n[5] Testing on DOWNTREND market...")
    df_downtrend = generate_sample_data(rows=200, trend='DOWN')
    detector_results_down = test_all_detectors(df_downtrend)
    test_confluence_scoring(detector_results_down, df_downtrend['Close'].iloc[-1])
    
    # Test on RANGE market
    print("\n[6] Testing on RANGE market...")
    df_range = generate_sample_data(rows=200, trend='RANGE')
    detector_results_range = test_all_detectors(df_range)
    test_confluence_scoring(detector_results_range, df_range['Close'].iloc[-1])
    
    print("\n" + "="*80)
    print("INTEGRATION TEST COMPLETE")
    print("="*80)


if __name__ == '__main__':
    run_full_integration_test()
