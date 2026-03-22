"""Volatility Engine — ATR, Bollinger Bands"""
import pandas as pd
import numpy as np
from typing import Dict, Any

def get_volatility(data: pd.DataFrame) -> Dict[str, Any]:
    if data.empty or len(data) < 20:
        return {"atr": 0, "atr_pct": 0, "bb_squeeze": False, "volatility_label": "Unknown"}

    # ATR
    high = data["High"].squeeze()
    low = data["Low"].squeeze()
    close = data["Close"].squeeze()

    tr = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low - close.shift(1)).abs()
    ], axis=1).max(axis=1)
    atr = float(tr.rolling(14).mean().iloc[-1])
    atr_pct = float(atr / close.iloc[-1] * 100)

    # Bollinger Bands
    bb_mid = close.rolling(20).mean()
    bb_std = close.rolling(20).std()
    bb_upper = bb_mid + 2 * bb_std
    bb_lower = bb_mid - 2 * bb_std
    bb_width = float((bb_upper.iloc[-1] - bb_lower.iloc[-1]) / bb_mid.iloc[-1] * 100)

    # Historical volatility
    returns = close.pct_change().dropna()
    hv_20 = float(returns.tail(20).std() * np.sqrt(252) * 100)

    # Squeeze: BB bandwidth is tighter than usual (< 10%)
    bb_squeeze = bb_width < 10

    volatility_label = "High" if atr_pct > 2.5 else "Moderate" if atr_pct > 1.0 else "Low"

    return {
        "atr": round(atr, 2),
        "atr_pct": round(atr_pct, 2),
        "bb_upper": round(float(bb_upper.iloc[-1]), 2),
        "bb_lower": round(float(bb_lower.iloc[-1]), 2),
        "bb_width_pct": round(bb_width, 2),
        "bb_squeeze": bb_squeeze,
        "hv_20": round(hv_20, 2),
        "volatility_label": volatility_label,
    }
