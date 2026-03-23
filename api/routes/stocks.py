from fastapi import APIRouter, HTTPException
import yfinance as yf
from typing import Dict, Any
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import PARQUET_DIR

from services.market_regime.engine import get_market_context
from services.price_action.fibonacci import calculate_fibonacci_retracement
from services.price_action.engine import analyze_trend
from services.liquidity_sweep.engine import detect_liquidity_sweep
from services.momentum.engine import get_momentum
from services.relative_strength.engine import get_relative_strength
from services.volatility.engine import get_volatility
from services.sentiment.engine import get_sentiment_summary
from services.news_service import get_news
from services.core.scenario_engine import generate_scenarios

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


def _load_analysis_data(symbol: str) -> pd.DataFrame:
    """Load stock data from parquet or fall back to yfinance."""
    parquet_path = PARQUET_DIR / f"{symbol}.parquet"
    if parquet_path.exists():
        try:
            df = pd.read_parquet(parquet_path)
            if not df.empty:
                # Flatten MultiIndex columns
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
                return df
        except Exception:
            pass

    df = yf.download(symbol, period="1y", progress=False)
    
    # Handle MultiIndex columns from yfinance
    if isinstance(df.columns, pd.MultiIndex):
        # Flatten columns to single index
        df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
    
    return df


def _build_story_sections_stock(
    structure: dict,
    fib: dict,
    liquidity: dict,
    rs: dict,
    current_price: float,
) -> dict:
    """Build detailed 5-section stock story."""
    trend = structure.get("trend", "Unknown")
    sma = structure.get("sma50", 0)

    # 1. Structure Analysis
    if trend == "Bullish":
        structure_text = f"The stock is demonstrating a robust upward trajectory, firmly sustained above the 50-day SMA of ₹{round(sma, 1) if sma else 0}. This reflects consistent buyer accumulation with higher-low formations indicating clear institutional support. Positive sentiment dominates."
    elif trend == "Bearish":
        structure_text = f"The stock is locked in a prolonged downtrend, facing resistance and trading below the 50-day SMA of ₹{round(sma, 1) if sma else 0}. Sellers maintain firm control with lower-high structures. Structural breakdown remains the highest probability outcome."
    else:
        structure_text = f"Currently in range-bound consolidation without clear directional bias relative to the 50-day SMA (₹{round(sma, 1) if sma else 0}). The asset is searching for a catalyst. Breakout or breakdown likely in the coming sessions as volatility compression peaks."

    # 2. Fibonacci Analysis
    fib_zone = fib.get("zone", "unknown")
    fib_high = fib.get("high", 0)
    fib_low = fib.get("low", 0)
    
    if fib_zone == "golden_pocket":
        fib_text = f"Price has retraced into the Golden Pocket (₹{round(fib.get('levels',{}).get('0.618',0),1)}-₹{round(fib.get('levels',{}).get('0.5',0),1)}). This is a high-probability reversal zone—smart money typically bounces from this level. Setup looks very favorable for continuation trades."
    elif fib_zone == "failed_retracement":
        fib_text = "Price broke decisively below the 0.786 Fibonacci level—a failed retracement signal. This structural breakdown indicates the opposing side has overwhelmed support. Severe structural risk if buyers don't step in immediately."
    else:
        fib_text = f"Price is in the {fib_zone.replace('_', ' ')} zone (₹{round(fib_high,1)} swing high to ₹{round(fib_low,1)} swing low). While not at a critical turning point, reaction here will determine immediate micro-trend direction."

    # 3. Liquidity Analysis
    if liquidity.get("detected"):
        liq_text = f"A prominent {liquidity.get('type','Liquidity sweep')} was detected at ₹{liquidity.get('level',0)}. This institutional stop-hunting behavior typically precedes violent mean-reversion. High-probability reversal setup forming."
    else:
        liq_text = "No major liquidity sweeps detected. Price action remains organic and clean, responding naturally to supply/demand zones. Fewer manipulation signals present."

    # 4. Relative Strength Analysis
    rs_ratio = rs.get("rs_ratio", 0)
    if rs.get("outperforming"):
        rs_text = f"Exceptional relative strength—outperforming NIFTY by {rs_ratio}%. This indicates deep institutional accumulation. Stock likely to hold up better during market corrections compared to market."
    elif rs.get("underperforming"):
        rs_text = f"Severe underperformance vs NIFTY (down {rs_ratio}%). Suggests lack of capital inflow and possible fundamental weakness. Risky vs alternatives."
    else:
        rs_text = f"Performance tracking NIFTY inline (RS: {rs_ratio}%). Acts as a market beta-tracker without specific alpha generation."

    # 5. Overall Verdict
    bias = "BULLISH" if trend == "Bullish" else "BEARISH" if trend == "Bearish" else "NEUTRAL"
    conclusion = f"Technical Verdict: {bias}. Considering structure, Fibonacci positioning, liquidity behavior, and relative strength—focus on the scenarios below for actionable entry/exit levels."

    return {
        "structure": structure_text,
        "fibonacci": fib_text,
        "liquidity": liq_text,
        "relative_strength": rs_text,
        "conclusion": conclusion
    }



