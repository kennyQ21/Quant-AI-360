"""
Moving Average Crossover Strategy
Simple strategy: BUY when MA20 > MA50, SELL when MA20 < MA50
"""
import pandas as pd
from typing import List


def ma_crossover(df: pd.DataFrame, fast_ma: str = 'SMA_20', slow_ma: str = 'SMA_50') -> List[str]:
    """
    Moving Average Crossover Strategy
    
    Rules:
    - BUY when fast MA crosses above slow MA (golden cross)
    - SELL when fast MA crosses below slow MA (death cross)
    - HOLD when fast MA > slow MA (uptrend)
    - HOLD when fast MA < slow MA (downtrend, but no active signal)
    
    Args:
        df: DataFrame with OHLCV data and moving averages
        fast_ma: Name of fast moving average column (default: SMA_20)
        slow_ma: Name of slow moving average column (default: SMA_50)
    
    Returns:
        List of signals ('BUY', 'SELL', 'HOLD')
    """
    signals = []
    prev_fast = None
    prev_slow = None
    
    for idx, row in df.iterrows():
        fast = row.get(fast_ma, 0)
        slow = row.get(slow_ma, 0)
        
        # Skip if missing data
        if pd.isna(fast) or pd.isna(slow):
            signals.append('HOLD')
            prev_fast = fast
            prev_slow = slow
            continue
        
        # Crossover logic
        if prev_fast is not None and prev_slow is not None:
            # Golden Cross: fast MA crosses above slow MA
            if prev_fast <= prev_slow and fast > slow:
                signals.append('BUY')
            
            # Death Cross: fast MA crosses below slow MA
            elif prev_fast >= prev_slow and fast < slow:
                signals.append('SELL')
            
            else:
                signals.append('HOLD')
        else:
            # First bar
            if fast > slow:
                signals.append('BUY')
            elif fast < slow:
                signals.append('SELL')
            else:
                signals.append('HOLD')
        
        prev_fast = fast
        prev_slow = slow
    
    return signals


def ma_trend(df: pd.DataFrame, fast_ma: str = 'SMA_20', slow_ma: str = 'SMA_200') -> List[str]:
    """
    Multi-MA Trend Strategy
    
    Rules:
    - BUY when price > SMA20 > SMA200 (strong uptrend)
    - SELL when price < SMA20 < SMA200 (strong downtrend)
    - HOLD otherwise
    
    Args:
        df: DataFrame with moving averages
    
    Returns:
        List of signals
    """
    signals = []
    
    for idx, row in df.iterrows():
        close = row.get('Close', row.get('close', 0))
        fast = row.get(fast_ma, close)
        slow = row.get(slow_ma, close)
        
        # Strong uptrend
        if close > fast > slow:
            signals.append('BUY')
        
        # Strong downtrend
        elif close < fast < slow:
            signals.append('SELL')
        
        else:
            signals.append('HOLD')
    
    return signals
