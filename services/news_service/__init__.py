"""News Service — fetches headlines via yfinance news"""
import yfinance as yf
from typing import Dict, Any, List

def get_news(symbol: str, max_items: int = 5) -> Dict[str, Any]:
    try:
        ticker = yf.Ticker(symbol)
        news = ticker.news or []
        headlines = []
        for item in news[:max_items]:
            content = item.get("content", {})
            title = content.get("title") if isinstance(content, dict) else item.get("title", "")
            if title:
                headlines.append(title)

        return {
            "headlines": headlines,
            "count": len(headlines),
            "source": "Yahoo Finance",
        }
    except Exception as e:
        return {"headlines": [], "count": 0, "source": "Yahoo Finance", "error": str(e)}
