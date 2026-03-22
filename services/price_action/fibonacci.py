"""Fibonacci Retracement and Zone Engine"""
import pandas as pd
from typing import Dict, Any

def detect_swing_high_low(data: pd.DataFrame, window: int = 60) -> tuple:
    """Detect the most recent swing high and low within the given window."""
    if data.empty or len(data) < window:
        return 0.0, 0.0
    
    recent = data.tail(window)
    swing_high = float(recent["High"].max())
    swing_low = float(recent["Low"].min())
    return swing_high, swing_low

def compute_fib_levels(swing_high: float, swing_low: float) -> dict:
    """Compute Fibonacci retracement levels for a given swing high/low."""
    diff = swing_high - swing_low
    if diff == 0:
        return {}
        
    return {
        "0.0": swing_high,
        "0.236": swing_high - 0.236 * diff,
        "0.382": swing_high - 0.382 * diff,
        "0.5": swing_high - 0.5 * diff,
        "0.618": swing_high - 0.618 * diff,
        "0.786": swing_high - 0.786 * diff,
        "1.0": swing_low,
    }

def classify_zone(current_price: float, levels: dict) -> str:
    """Classify the current price into a Fibonacci zone."""
    if not levels:
        return "unknown"
        
    if current_price > levels["0.236"]:
        return "premium"
    elif levels["0.382"] >= current_price >= levels["0.5"]:
        return "discount"
    elif levels["0.5"] > current_price >= levels["0.618"]:
        return "golden_pocket"
    elif current_price < levels["0.786"]:
        return "failed_retracement"
    else:
        return "equilibrium"

def calculate_fibonacci_retracement(data: pd.DataFrame, window: int = 60) -> Dict[str, Any]:
    """Legacy wrapper to maintain compatibility with analysis route structure."""
    swing_high, swing_low = detect_swing_high_low(data, window)
    if swing_high == 0.0 and swing_low == 0.0:
        return {"levels": {}, "zone": "unknown", "high": 0, "low": 0}
        
    levels = compute_fib_levels(swing_high, swing_low)
    current_price = float(data["Close"].iloc[-1])
    zone = classify_zone(current_price, levels)
    
    return {
        "high": swing_high,
        "low": swing_low,
        "levels": levels,
        "zone": zone,
        "confidence": "High" if zone == "golden_pocket" else "Medium",
    }

