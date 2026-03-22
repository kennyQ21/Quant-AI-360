"""Market Regime Detection Engine"""
import numpy as np
import yfinance as yf
from typing import Dict, Any

def get_market_context(nifty_symbol: str = "^NSEI") -> Dict[str, Any]:
    try:
        data = yf.download(nifty_symbol, period="6mo", progress=False)
        if data.empty:
            return {"regime": "Unknown", "volatility": "Unknown", "sector": "Index", "interpretation": "No data"}

        close = data["Close"].squeeze()
        sma50 = close.rolling(50).mean().iloc[-1]
        sma200 = close.rolling(200).mean().iloc[-1] if len(close) >= 200 else sma50
        current = float(close.iloc[-1])

        returns = close.pct_change().dropna()
        vol_20 = float(returns.tail(20).std() * np.sqrt(252) * 100)

        if current > sma50 and float(sma50) > float(sma200):
            regime = "Bullish"
        elif current < sma50 and float(sma50) < float(sma200):
            regime = "Bearish"
        else:
            regime = "Neutral"

        volatility = "High" if vol_20 > 20 else "Moderate" if vol_20 > 12 else "Low"

        interp_map = {
            "Bullish": "Market is in a confirmed uptrend above key moving averages. Favorable for long setups.",
            "Bearish": "Market is in a confirmed downtrend below key moving averages. Caution advised for long setups.",
            "Neutral": "Market is range-bound. Wait for directional confirmation.",
        }

        return {
            "regime": regime,
            "volatility": volatility,
            "sector": "Index",
            "sma50": round(float(sma50), 2),
            "current": round(current, 2),
            "vol_annualized": round(vol_20, 2),
            "interpretation": interp_map[regime],
        }
    except Exception as e:
        return {"regime": "Unknown", "volatility": "Unknown", "sector": "Index", "interpretation": str(e)}
