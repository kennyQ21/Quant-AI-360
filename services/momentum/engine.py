"""Momentum Engine — RSI, MACD, ROC analysis"""
import pandas as pd
from typing import Dict, Any

def get_momentum(data: pd.DataFrame) -> Dict[str, Any]:
    if data.empty or len(data) < 30:
        return {"rsi": 50, "rsi_signal": "Neutral", "macd": 0, "momentum_label": "Weak"}

    close = data["Close"].squeeze()

    # RSI
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    rsi = float(100 - (100 / (1 + rs.iloc[-1])))

    # MACD
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    macd_val = float(macd_line.iloc[-1])
    signal_val = float(signal_line.iloc[-1])
    macd_hist = macd_val - signal_val

    # ROC 10
    roc = float((close.iloc[-1] - close.iloc[-10]) / close.iloc[-10] * 100) if len(close) >= 10 else 0.0

    # RSI signal
    if rsi >= 70:
        rsi_signal = "Overbought"
    elif rsi <= 30:
        rsi_signal = "Oversold"
    elif rsi >= 55:
        rsi_signal = "Bullish"
    elif rsi <= 45:
        rsi_signal = "Bearish"
    else:
        rsi_signal = "Neutral"

    # Overall momentum label
    bullish_count = sum([rsi >= 55, macd_val > signal_val, roc > 0])
    if bullish_count >= 2:
        momentum_label = "Strong" if bullish_count == 3 else "Moderate"
    elif rsi <= 35 and macd_val < signal_val:
        momentum_label = "Weak"
    else:
        momentum_label = "Neutral"

    return {
        "rsi": round(rsi, 1),
        "rsi_signal": rsi_signal,
        "macd": round(macd_val, 4),
        "macd_signal": round(signal_val, 4),
        "macd_histogram": round(macd_hist, 4),
        "roc_10": round(roc, 2),
        "momentum_label": momentum_label,
    }
