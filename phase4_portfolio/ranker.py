"""Phase 4 Portfolio Ranker — ranks stocks by confluence score"""
from typing import List, Dict, Any

def rank_stocks(analysis_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Rank a list of stock analysis dicts by their trade quality score.
    Returns sorted list (highest score first) with rank added.
    """
    scored = []
    for result in analysis_results:
        score = result.get("trade_quality", {}).get("score", 0)
        regime = result.get("market_context", {}).get("regime", "Unknown")
        symbol = result.get("symbol", "?")
        fib_zone = result.get("fibonacci", {}).get("zone", "unknown")
        momentum = result.get("momentum", {}).get("momentum_label", "Weak")

        scored.append({
            "symbol": symbol,
            "score": score,
            "regime": regime,
            "fib_zone": fib_zone,
            "momentum": momentum,
            "recommendation": result.get("decision_context", {}).get("recommendation", "")
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    for i, s in enumerate(scored):
        s["rank"] = i + 1

    return scored
