"""
Quant AI 360° Analysis Route
Provides comprehensive stock analysis combining price action, momentum,
Fibonacci levels, liquidity sweeps, market context, ML signals, and news.
"""
import sys
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException
import pandas as pd
import yfinance as yf

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

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Analysis"])


def _load_data(symbol: str) -> pd.DataFrame:
    """Load stock data from parquet or fall back to yfinance."""
    df = None
    parquet_path = PARQUET_DIR / f"{symbol}.parquet"
    if parquet_path.exists():
        try:
            df = pd.read_parquet(parquet_path)
            if not df.empty:
                logger.info(f"Loaded {len(df)} rows from parquet for {symbol}")
        except Exception as e:
            logger.warning(f"Failed to load parquet for {symbol}: {e}")
            df = None

    if df is None or df.empty:
        logger.info(f"Loading from yfinance for {symbol}")
        df = yf.download(symbol, period="1y", progress=False)

    # Handle MultiIndex columns from yfinance or parquet
    if isinstance(df.columns, pd.MultiIndex):
        # Flatten columns to single index
        df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
        
    return df


def _build_story_sections(
    structure: dict,
    fib: dict,
    liquidity: dict,
    rs: dict,
    current_price: float,
) -> dict:
    """Build structured 5-section stock story with DETAILED reasoning."""
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
        liq_text = "No major liquidity sweeps detected. Price action remains organic and clean, responding naturallyto supply/demand zones. Fewer manipulation signals present."

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


@router.get("/stock/{symbol}/analysis-360")
async def get_analysis(symbol: str):
    """Get 360° stock analysis."""
    try:
        data = _load_data(symbol)
        if data.empty:
            raise HTTPException(status_code=404, detail=f"No data available for {symbol}")

        current_price = float(data["Close"].iloc[-1])
        structure = analyze_trend(data)
        fib = calculate_fibonacci_retracement(data)
        liquidity = detect_liquidity_sweep(data)
        momentum = get_momentum(data)
        rs = get_relative_strength(symbol, data)
        market = get_market_context()
        volatility = get_volatility(data)
        sentiment = get_sentiment_summary(symbol)
        news = get_news(symbol)
        open("/tmp/news.txt","w").write(str(news))

        story_sections = _build_story_sections(structure, fib, liquidity, rs, current_price)
        scenarios = generate_scenarios(
            symbol=symbol,
            current_price=current_price,
            trend=structure.get("trend", "Unknown"),
            fib_levels=fib.get("levels", {}),
            momentum_label=momentum.get("momentum_label", "Weak"),
            regime=market.get("regime", "Unknown"),
        )

        avg_vol = float(data["Volume"].tail(20).mean()) if "Volume" in data.columns else 0
        last_vol = float(data["Volume"].iloc[-1]) if "Volume" in data.columns else 0
        vol_ratio = round(last_vol / avg_vol, 2) if avg_vol > 0 else 1.0

        prev_close = float(data["Close"].iloc[-2]) if len(data) > 1 else current_price
        change = current_price - prev_close
        change_pct = (change / prev_close * 100) if prev_close != 0 else 0

        confluence_score = min(int((
            (structure.get("score", 5) / 10 * 3) +
            (rs.get("score", 5) / 10 * 2) +
            (momentum.get("score", 5) / 10 * 2) +
            (3 if volatility.get("elevated") else 0)
        )), 10)

        return {
            "symbol": symbol,
            "current_price": round(current_price, 2),
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
            "volume_ratio": vol_ratio,
            "trend": structure.get("trend"),
            "story_sections": story_sections,
            "story": story_sections.get("conclusion", ""),
            "scenarios": scenarios,
            "confluence_breakdown": {
                "trend": {"label": "Structure", "earned": 1 if structure.get("trend") != "Unknown" else 0, "max": 1},
                "momentum": {"label": "Momentum", "earned": 1 if momentum.get("momentum_label") != "Weak" else 0, "max": 1},
                "fib": {"label": "Fibonacci", "earned": 1 if fib.get("zone") == "golden_pocket" else 0, "max": 1},
                "liq": {"label": "Liquidity", "earned": 1 if liquidity.get("detected") else 0, "max": 1},
            },
            "confluence_score_10": confluence_score,
            "trade_quality": {
                "score": confluence_score,
                "signal_strength": "Strong" if confluence_score >= 7 else "Moderate" if confluence_score >= 4 else "Weak",
            },
            "fibonacci": fib,
            "market_regime": market,
            "sentiment": sentiment,
            "TEST_FIELD": "HELLO",
            "news": {
                **news,
                "headlines": news.get("headlines", [])[:3] if isinstance(news, dict) else (news[:3] if isinstance(news, list) else [])
            } if isinstance(news, dict) else {
                "headlines": news[:3] if isinstance(news, list) else []
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
