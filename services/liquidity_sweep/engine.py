"""Liquidity Sweep Detection Engine"""
import pandas as pd
from typing import Dict, Any

def detect_liquidity_sweep(data: pd.DataFrame, lookback: int = 20) -> Dict[str, Any]:
    """
    Detects buy-side and sell-side liquidity sweeps.
    A sweep occurs when price wicks through a prior swing high/low
    and then reverses back inside the range.
    """
    if data.empty or len(data) < lookback + 5:
        return {"detected": False, "type": "none", "level": 0, "interpretation": "Insufficient data"}

    recent = data.tail(lookback + 5)
    
    # Find the swing high/low of the lookback period (excluding last 5 candles)
    window = recent.iloc[:-5]
    swing_high = float(window["High"].max())
    swing_low = float(window["Low"].min())

    last_5 = recent.tail(5)
    swept_high = float(last_5["High"].max())
    swept_low = float(last_5["Low"].min())
    close = float(data["Close"].iloc[-1])

    # Bullish sweep: price dipped below swing low then closed above it
    if swept_low < swing_low and close > swing_low:
        return {
            "detected": True,
            "type": "Bullish Sweep",
            "level": round(swing_low, 2),
            "swept_to": round(swept_low, 2),
            "interpretation": f"Price swept sell-side liquidity at \u20b9{swing_low:.1f} and recovered. Smart money absorption signal.",
        }

    # Bearish sweep: price pushed above swing high then closed below it
    if swept_high > swing_high and close < swing_high:
        return {
            "detected": True,
            "type": "Bearish Sweep",
            "level": round(swing_high, 2),
            "swept_to": round(swept_high, 2),
            "interpretation": f"Price swept buy-side liquidity at \u20b9{swing_high:.1f} and rejected. Smart money distribution signal.",
        }

    return {
        "detected": False,
        "type": "none",
        "level": 0,
        "interpretation": "No liquidity sweep pattern detected in recent price action.",
    }
