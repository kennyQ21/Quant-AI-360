"""News Service — fetches headlines via yfinance news"""
import yfinance as yf
from typing import Dict, Any, List

def get_news(symbol: str, max_items: int = 10) -> Dict[str, Any]:
    try:
        ticker = yf.Ticker(symbol)
        news = ticker.news or []
        articles = []
        
        bullish_words = ['up', 'surge', 'gain', 'jump', 'rise', 'record', 'high', 'beat', 'growth', 'buy', 'strong', 'outperform']
        bearish_words = ['down', 'plunge', 'loss', 'drop', 'fall', 'low', 'miss', 'decline', 'sell', 'weak', 'underperform']
        
        bullish_count = 0
        bearish_count = 0
        
        for item in news[:max_items]:
            content = item.get("content", {})
            
            # YF payload might differ; fallback to flat dict
            title = content.get("title") if isinstance(content, dict) and 'title' in content else item.get("title", "")
            summary = content.get("summary") if isinstance(content, dict) and 'summary' in content else item.get("summary", "")
            provider = content.get("provider", {}).get("displayName") if isinstance(content, dict) and isinstance(content.get("provider"), dict) else item.get("publisher", "")
            link = content.get("canonicalUrl", {}).get("url") if isinstance(content, dict) and isinstance(content.get("canonicalUrl"), dict) else item.get("link", "")
            pub_date = content.get("pubDate") if isinstance(content, dict) and 'pubDate' in content else item.get("providerPublishTime", 0)

            if not title:
                continue
                
            text_to_analyze = f"{title} {summary}".lower()
            article_bullish = sum(1 for w in bullish_words if w in text_to_analyze)
            article_bearish = sum(1 for w in bearish_words if w in text_to_analyze)
            
            sentiment = "Neutral"
            if article_bullish > article_bearish:
                sentiment = "Bullish"
                bullish_count += 1
            elif article_bearish > article_bullish:
                sentiment = "Bearish"
                bearish_count += 1
                
            articles.append({
                "title": title,
                "summary": summary,
                "provider": provider,
                "link": link,
                "pub_date": pub_date,
                "sentiment": sentiment
            })

        overall_sentiment = "Neutral"
        if bullish_count > bearish_count:
            overall_sentiment = "Bullish"
        elif bearish_count > bullish_count:
            overall_sentiment = "Bearish"

        return {
            "articles": articles,
            "count": len(articles),
            "source": "Yahoo Finance",
            "analysis": {
                "overall_sentiment": overall_sentiment,
                "bullish_articles": bullish_count,
                "bearish_articles": bearish_count
            }
        }
    except Exception as e:
        return {"articles": [], "count": 0, "source": "Yahoo Finance", "error": str(e), "analysis": {}}
