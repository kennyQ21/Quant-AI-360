"""Sentiment Engine — basic news sentiment scoring"""
from typing import Dict, Any, List

BULLISH_KEYWORDS = [
    "surge", "rally", "jump", "gain", "record", "high", "buy", "upgrade",
    "beat", "outperform", "strong", "growth", "profit", "revenue", "positive",
    "bullish", "breakout", "expand", "acquisition", "deal", "win", "contract",
]
BEARISH_KEYWORDS = [
    "fall", "drop", "decline", "loss", "miss", "downgrade", "sell", "weak",
    "risk", "concern", "below", "disappoint", "penalty", "fraud", "probe",
    "bearish", "debt", "default", "write-off", "cut", "resign", "investigation",
]

def score_headline(headline: str) -> float:
    """Returns score from -1.0 (very bearish) to +1.0 (very bullish)."""
    text = headline.lower()
    bullish = sum(1 for kw in BULLISH_KEYWORDS if kw in text)
    bearish = sum(1 for kw in BEARISH_KEYWORDS if kw in text)
    total = bullish + bearish
    if total == 0:
        return 0.0
    return round((bullish - bearish) / total, 2)

def get_sentiment_summary(headlines: List[str]) -> Dict[str, Any]:
    if not headlines:
        return {"score": 0.0, "label": "Neutral", "count": 0}

    scores = [score_headline(h) for h in headlines]
    avg = sum(scores) / len(scores)

    label = "Bullish" if avg > 0.15 else "Bearish" if avg < -0.15 else "Neutral"

    return {
        "score": round(avg, 2),
        "label": label,
        "count": len(headlines),
        "breakdown": {"bullish": sum(1 for s in scores if s > 0),
                      "neutral": sum(1 for s in scores if s == 0),
                      "bearish": sum(1 for s in scores if s < 0)},
    }
