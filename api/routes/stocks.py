import logging
from fastapi import APIRouter, HTTPException
import yfinance as yf
from typing import Dict, Any
import pandas as pd

from api.dependencies import load_stock_data
from services.analysis.story_builder import build_story_sections

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Stocks"])

@router.get("/stock/{symbol}")
async def get_stock_quote(symbol: str, period: str = "6mo") -> Dict[str, Any]:
    """Fetch stock quote and historical candles."""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        if hist.empty:
            raise HTTPException(status_code=404, detail="Stock data not found.")
        
        # Format candles for lightweight charts
        hist.index = hist.index.tz_localize(None)
        candles = []
        for date, row in hist.iterrows():
            candles.append({
                "time": date.strftime("%Y-%m-%d"),
                "open": row["Open"],
                "high": row["High"],
                "low": row["Low"],
                "close": row["Close"],
                "volume": row["Volume"]
            })
            
        info = ticker.info or {}
        price = hist["Close"].iloc[-1]
        
        return {
            "symbol": symbol,
            "company_name": info.get("longName", symbol),
            "price": round(price, 2),
            "candles": candles
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

