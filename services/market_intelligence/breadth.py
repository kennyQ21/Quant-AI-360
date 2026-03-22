import logging
import yfinance as yf
from typing import Dict, Any

logger = logging.getLogger(__name__)

def calculate_market_breadth(index_components: list = None) -> Dict[str, Any]:
    """
    Phase 12 Market Intelligence: Market Breadth (A/D)
    Calculates Advance/Decline ratio for the market to gauge underlying strength.
    """
    if not index_components:
        # Fallback to a representative basket of NIFTY stocks
        index_components = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", "SBIN.NS"] 
        
    try:
        data = yf.download(index_components, period="5d", progress=False)
        if data.empty or "Close" not in data.columns:
            return {"advancing": 0, "declining": 0, "ad_ratio": 1.0, "status": "unknown"}
            
        returns = data["Close"].pct_change().iloc[-1]
        
        advancing = (returns > 0).sum()
        declining = (returns < 0).sum()
        
        ad_ratio = advancing / declining if declining > 0 else float(advancing)
        
        return {
            "advancing": int(advancing),
            "declining": int(declining),
            "ad_ratio": round(float(ad_ratio), 2),
            "status": "Bullish" if ad_ratio > 1.2 else "Bearish" if ad_ratio < 0.8 else "Neutral"
        }
    except Exception as e:
        logger.error(f"Error calculating market breadth: {e}")
        return {"advancing": 0, "declining": 0, "ad_ratio": 1.0, "status": "Error"}
