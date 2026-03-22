"""
RSI Mean Reversion Strategy
Simple strategy: BUY when RSI < 30, SELL when RSI > 70
"""
import pandas as pd
from typing import List


def rsi_mean_reversion(df: pd.DataFrame, rsi_column: str = 'RSI_14') -> List[str]:
    """
    RSI Mean Reversion Strategy
    
    Rules:
    - BUY when RSI < 30 (oversold)
    - SELL when RSI > 70 (overbought)
    - HOLD otherwise
    
    Args:
        df: DataFrame with OHLCV data and RSI indicator
        rsi_column: Name of RSI column
    
    Returns:
        List of signals ('BUY', 'SELL', 'HOLD')
    """
    signals = []
    
    # Vectorized approach is faster
    rsi_values = df.get(rsi_column)
    if rsi_values is None:
        rsi_values = pd.Series([50] * len(df), index=df.index)
    
    for idx, rsi in enumerate(rsi_values):
        # Handle NaN values
        if pd.isna(rsi):
            signals.append('HOLD')
        # Oversold → BUY
        elif float(rsi) < 30:
            signals.append('BUY')
        # Overbought → SELL
        elif float(rsi) > 70:
            signals.append('SELL')
        # Neutral zone → HOLD
        else:
            signals.append('HOLD')
    
    return signals


def rsi_mean_reversion_with_trend(df: pd.DataFrame, rsi_column: str = 'RSI_14', 
                                   sma_column: str = 'SMA_20') -> List[str]:
    """
    RSI Mean Reversion with Trend Filter
    Only trade in direction of trend
    
    Rules:
    - BUY when RSI < 30 AND price > SMA20 (uptrend)
    - SELL when RSI > 70 AND price < SMA20 (downtrend)
    
    Args:
        df: DataFrame with OHLCV and indicators
    
    Returns:
        List of signals
    """
    signals = []
    
    rsi_values = df.get(rsi_column)
    close_values = df.get('Close', df.get('close'))
    sma_values = df.get(sma_column)
    
    if rsi_values is None:
        rsi_values = pd.Series([50] * len(df), index=df.index)
    if close_values is None:
        close_values = pd.Series([0] * len(df), index=df.index)
    if sma_values is None:
        sma_values = close_values.copy()
    
    for idx in range(len(df)):
        rsi = float(rsi_values.iloc[idx]) if not pd.isna(rsi_values.iloc[idx]) else 50
        close = float(close_values.iloc[idx]) if not pd.isna(close_values.iloc[idx]) else 0
        sma = float(sma_values.iloc[idx]) if not pd.isna(sma_values.iloc[idx]) else close
        
        # Oversold in uptrend → BUY
        if rsi < 30 and close > sma:
            signals.append('BUY')
        
        # Overbought in downtrend → SELL
        elif rsi > 70 and close < sma:
            signals.append('SELL')
        
        else:
            signals.append('HOLD')
    
    return signals

