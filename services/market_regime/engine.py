"""Market Regime Detection Engine - Hardened Prop Desk Version"""
import numpy as np
import yfinance as yf
import pandas as pd
from typing import Dict, Any

class MarketRegimeEngine:
    """
    Identifies the broader market environment to dictate valid strategies.
    Regimes: TRENDING_BULL, TRENDING_BEAR, RANGING, BROKEN
    """
    
    def __init__(self, vix_threshold: float = 35.0):
        self.vix_threshold = vix_threshold
        
    def classify_regime(self, market_data: pd.DataFrame, vix_data: pd.DataFrame = None) -> pd.Series:
        df = market_data.copy()
        
        if "EMA_20" not in df.columns:
            df["EMA_20"] = df["Close"].ewm(span=20, adjust=False).mean()
        if "EMA_50" not in df.columns:
            df["EMA_50"] = df["Close"].ewm(span=50, adjust=False).mean()
            
        def evaluate_day(row, vix_val=None):
            if vix_val is not None and vix_val > self.vix_threshold:
                return "BROKEN"
                
            close = row["Close"]
            ema20 = row["EMA_20"]
            ema50 = row["EMA_50"]
            
            if close > ema20 and ema20 > ema50:
                return "TRENDING_BULL"
            elif close < ema20 and ema20 < ema50:
                return "TRENDING_BEAR"
            else:
                return "RANGING"
                
        if vix_data is not None and not vix_data.empty:
            df = df.join(vix_data["Close"].rename("VIX_Close"), how="left")
            df["VIX_Close"] = df["VIX_Close"].ffill()
            regimes = df.apply(lambda r: evaluate_day(r, r.get("VIX_Close")), axis=1)
        else:
            regimes = df.apply(lambda r: evaluate_day(r), axis=1)
            
        return regimes

    def get_valid_strategies(self, regime: str) -> list[str]:
        if regime == "BROKEN":
            return []
        elif regime == "TRENDING_BULL":
            return ["Trend_Continuation_Long", "Volatility_Breakout_Long"]
        elif regime == "TRENDING_BEAR":
            return ["Trend_Continuation_Short", "Volatility_Breakout_Short"]
        elif regime == "RANGING":
            return ["Range_Mean_Reversion"]
        return []

def get_market_context(nifty_symbol: str = "^NSEI", vix_symbol: str = "^INDIAVIX") -> Dict[str, Any]:
    try:
        data = yf.download(nifty_symbol, period="3mo", progress=False)
        if hasattr(data.columns, "levels") and isinstance(data.columns, pd.MultiIndex):
            if nifty_symbol in data.columns.levels[1]:
                close = data["Close"][nifty_symbol].squeeze()
            else:
                close = data["Close"].squeeze()
        else:
            close = data["Close"].squeeze()
            
        vix_data = yf.download(vix_symbol, period="3mo", progress=False)
        if hasattr(vix_data.columns, "levels") and isinstance(vix_data.columns, pd.MultiIndex):
            if vix_symbol in vix_data.columns.levels[1]:
                vix_close = vix_data["Close"][vix_symbol].squeeze()
            else:
                vix_close = vix_data["Close"].squeeze()
        else:
            vix_close = vix_data["Close"].squeeze()
        
        if data.empty:
            return {"regime": "BROKEN", "valid_strategies": [], "interpretation": "No data"}
            
        ema20 = close.ewm(span=20, adjust=False).mean().iloc[-1]
        ema50 = close.ewm(span=50, adjust=False).mean().iloc[-1]
        current = float(close.iloc[-1])
        current_vix = float(vix_close.iloc[-1]) if not vix_data.empty else 15.0

        if current_vix > 35:
            regime = "BROKEN"
            strategies = []
        elif current > ema20 > ema50:
            regime = "TRENDING_BULL"
            strategies = ["Trend_Continuation_Long", "Volatility_Breakout_Long"]
        elif current < ema20 < ema50:
            regime = "TRENDING_BEAR"
            strategies = ["Trend_Continuation_Short", "Volatility_Breakout_Short"]
        else:
            regime = "RANGING"
            strategies = ["Range_Mean_Reversion"]

        interp_map = {
            "TRENDING_BULL": "Market is in a confirmed uptrend.",
            "TRENDING_BEAR": "Market is in a confirmed downtrend.",
            "RANGING": "Market is range-bound.",
            "BROKEN": "Market volatility broken (VIX > 35). Stay in cash."
        }

        return {
            "regime": regime,
            "valid_strategies": strategies,
            "vix": round(current_vix, 2),
            "ema20": round(float(ema20), 2),
            "ema50": round(float(ema50), 2),
            "current": round(current, 2),
            "interpretation": interp_map[regime],
        }
    except Exception as e:
        return {"regime": "BROKEN", "valid_strategies": [], "interpretation": str(e)}
