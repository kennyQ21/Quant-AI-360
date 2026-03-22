"""Phase 4 Portfolio Risk Engine"""
from typing import Dict, Any

def assess_risk(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Assess position risk based on ATR, confluence score, and market regime.
    Returns suggested position size (% of portfolio) and risk rating.
    """
    score = analysis.get("trade_quality", {}).get("score", 0)
    atr_pct = analysis.get("volatility", {}).get("atr_pct", 2.0)
    regime = analysis.get("market_context", {}).get("regime", "Unknown")
    fib_confidence = analysis.get("fibonacci", {}).get("confidence", "Low")

    # Base position size 2% of portfolio
    base_size = 2.0

    # Adjust for score
    if score >= 8:
        size_multiplier = 1.5
        risk_rating = "Low"
    elif score >= 6:
        size_multiplier = 1.0
        risk_rating = "Moderate"
    elif score >= 4:
        size_multiplier = 0.7
        risk_rating = "Moderate-High"
    else:
        size_multiplier = 0.3
        risk_rating = "High"

    # Adjust for regime
    if regime == "Bearish":
        size_multiplier *= 0.7
    elif regime == "Bullish":
        size_multiplier *= 1.1

    # Adjust for volatility
    if atr_pct > 3:
        size_multiplier *= 0.8

    position_size = round(min(base_size * size_multiplier, 5.0), 2)
    stop_pct = round(atr_pct * 1.5, 2)

    return {
        "position_size_pct": position_size,
        "stop_loss_pct": stop_pct,
        "risk_rating": risk_rating,
        "risk_reward": round(3.0 / (stop_pct / 100), 1) if stop_pct else 0,
    }
