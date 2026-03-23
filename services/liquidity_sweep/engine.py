"""Liquidity Sweep Detection Engine"""
import pandas as pd
from typing import Dict, Any

def detect_liquidity_sweep(data: pd.DataFrame, lookback: int = 20) -> Dict[str, Any]:
    """
    Detects buy-side and sell-side liquidity sweeps.
    A sweep occurs when price wicks through a prior swing high/low
    and then reverses back inside the range, confirmed by next candle.
    """
    if data.empty or len(data) < lookback + 5:
        return {"detected": False, "type": "none", "level": 0, "interpretation": "Insufficient data"}

    recent = data.tail(lookback + 5)
    
    # Find the swing high/low of the lookback period (excluding last 5 candles)
    window = recent.iloc[:-5]
    swing_high = float(window["High"].max())
    swing_low = float(window["Low"].min())

    last_5 = recent.tail(5)

    # Check for strict sweep + confirmation logic
    for i in range(len(last_5) - 1):
        candle = last_5.iloc[i]
        next_candle = last_5.iloc[i + 1]

        # Bullish sweep: Wick breaches below swing_low, but closes above it. Next candle confirms.
        if candle["Low"] < swing_low and candle["Close"] > swing_low:
            if next_candle["Close"] > next_candle["Open"] and next_candle["Close"] > candle["Close"]:
                return {
                    "detected": True,
                    "type": "Bullish Sweep",
                    "level": round(swing_low, 2),
                    "swept_to": round(float(candle["Low"]), 2),
                    "interpretation": f"Price swept sell-side liquidity at \u20b9{swing_low:.1f}, closed back inside, and confirmed. Smart money absorption signal.",
                }

        # Bearish sweep: Wick breaches above swing_high, but closes below it. Next candle confirms.
        if candle["High"] > swing_high and candle["Close"] < swing_high:
            if next_candle["Close"] < next_candle["Open"] and next_candle["Close"] < candle["Close"]:
                return {
                    "detected": True,
                    "type": "Bearish Sweep",
                    "level": round(swing_high, 2),
                    "swept_to": round(float(candle["High"]), 2),
                    "interpretation": f"Price swept buy-side liquidity at \u20b9{swing_high:.1f}, closed back inside, and confirmed. Smart money distribution signal.",
                }

    return {
        "detected": False,
        "type": "none",
        "level": 0,
        "interpretation": "No strict liquidity sweep pattern detected in recent price action.",
    }
