"""Basic Price Action Engine — Trend and Structure"""
import pandas as pd
from typing import Dict, Any

def analyze_trend(data: pd.DataFrame) -> Dict[str, Any]:
    if data.empty or len(data) < 50:
        return {"trend": "Unknown", "sma50": 0, "sma200": 0}

    close = data["Close"].squeeze()
    current = float(close.iloc[-1])
    sma50 = close.rolling(50).mean().iloc[-1]
    sma200 = close.rolling(200).mean().iloc[-1] if len(data) >= 200 else sma50

    if current > sma50 and sma50 > sma200:
        trend = "Bullish"
    elif current < sma50 and sma50 < sma200:
        trend = "Bearish"
    else:
        trend = "Sideways"

    return {
        "trend": trend,
        "current_price": round(current, 2),
        "sma50": round(float(sma50), 2),
        "sma200": round(float(sma200), 2),
    }
