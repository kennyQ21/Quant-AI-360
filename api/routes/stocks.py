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


@router.get("/stock/{symbol}/analysis-360")
async def get_360_analysis(symbol: str) -> Dict[str, Any]:
    """Get 360° stock analysis."""
    try:
        data = _load_analysis_data(symbol)
        if data.empty:
            raise HTTPException(status_code=404, detail=f"No data available for {symbol}")

        current_price = float(data["Close"].iloc[-1])
        prev_close = float(data["Close"].iloc[-2]) if len(data) > 1 else current_price
        change = current_price - prev_close
        change_pct = (change / prev_close * 100) if prev_close != 0 else 0

        # Attempt to load services, with graceful fallbacks
        structure = {}
        fib = {}
        liquidity = {}
        momentum = {"momentum_label": "Weak"}
        rs = {}
        market = {"regime": "Unknown"}
        volatility = {}
        sentiment = "Neutral"
        news = []

        try:
            structure = analyze_trend(data) or {}
        except Exception as e:
            pass

        try:
            fib = calculate_fibonacci_retracement(data) or {}
        except Exception as e:
            pass

        try:
            liquidity = detect_liquidity_sweep(data) or {}
        except Exception as e:
            pass

        try:
            momentum = get_momentum(data) or {"momentum_label": "Weak"}
        except Exception as e:
            pass

        try:
            rs = get_relative_strength(symbol) or {}
        except Exception as e:
            pass

        try:
            market = get_market_context() or {"regime": "Unknown"}
        except Exception as e:
            pass

        try:
            volatility = get_volatility(data) or {}
        except Exception as e:
            pass

        try:
            sentiment = get_sentiment_summary(symbol) or "Neutral"
        except Exception as e:
            pass

        try:
            news = get_news(symbol) or []
        except Exception as e:
            pass

        trend = structure.get("trend", "Unknown") if structure else "Unknown"
        sma = structure.get("sma50", 0) if structure else 0

        # Build story sections with available data
        if trend == "Bullish":
            structure_text = f"The stock is demonstrating upward momentum, trading above key levels. Bullish bias confirmed."
        elif trend == "Bearish":
            structure_text = f"The stock is facing downward pressure with key resistance levels being tested. Bearish bias confirmed."
        else:
            structure_text = f"The stock is trading in a neutral zone, searching for directional confirmation."

        fib_zone = fib.get("zone", "unknown") if fib else "unknown"
        if fib_zone == "golden_pocket":
            fib_text = "Price has retraced into a high-probability reversal zone."
        elif fib_zone == "failed_retracement":
            fib_text = "Price broke below critical support levels, indicating potential breakdown."
        else:
            fib_text = f"Price is in the {fib_zone} Fibonacci zone."

        if liquidity.get("detected"):
            liq_text = f"Liquidity sweep detected at key level. Mean-reversion potential forming."
        else:
            liq_text = "Price action remains clean without major manipulations."

        rs_ratio = rs.get("rs_ratio", 0) if rs else 0
        if rs.get("outperforming"):
            rs_text = f"Stock outperforming NIFTY by {rs_ratio}%. Strong institutional interest."
        elif rs.get("underperforming"):
            rs_text = f"Stock underperforming NIFTY by {rs_ratio}%. Relative weakness noted."
        else:
            rs_text = f"Stock tracking NIFTY performance (RS: {rs_ratio}%)."

        bias = "BULLISH" if trend == "Bullish" else "BEARISH" if trend == "Bearish" else "NEUTRAL"
        conclusion = f"Technical Verdict: {bias}. Review scenarios below for entry/exit opportunities."

        story_sections = {
            "structure": structure_text,
            "fibonacci": fib_text,
            "liquidity": liq_text,
            "relative_strength": rs_text,
            "conclusion": conclusion
        }

        # Generate scenarios
        scenarios = []
        try:
             scenarios = generate_scenarios(
                symbol=symbol,
                current_price=current_price,
                trend=trend,
                fib_levels=fib.get("levels", {}) if fib else {},
                momentum_label=momentum.get("momentum_label", "Weak"),
                regime=market.get("regime", "Unknown"),
            ) or []
        except Exception:
            scenarios = []

        confluence_score = 5
        if trend != "Unknown":
            confluence_score += 2
        if fib.get("zone") == "golden_pocket":
            confluence_score += 2
        if liquidity.get("detected"):
            confluence_score += 1
        if rs.get("outperforming"):
            confluence_score += 1
        confluence_score = min(confluence_score, 10)

        # Build Fibonacci data
        fib_confidence = "Low"
        if fib.get("zone") == "golden_pocket":
            fib_confidence = "High"
        elif fib.get("zone") in ["equilibrium", "expansion"]:
            fib_confidence = "Medium"

        # Build Relative Strength data
        rs_ratio = rs.get("rs_ratio", 0) if rs else 0
        rel_strength_data = {
            "rs_ratio": rs_ratio,
            "outperforming": rs.get("outperforming", False),
            "interpretation": rs_text
        }

        # Build Decision Context
        decision_bias = "Bullish" if trend == "Bullish" else "Bearish" if trend == "Bearish" else "Neutral"
        setup_quality = "Strong" if confluence_score >= 7 else "Moderate" if confluence_score >= 4 else "Weak"
        risk_level = "Low" if confluence_score >= 8 else "Medium" if confluence_score >= 5 else "High"
        decision_context = {
            "bias": decision_bias,
            "setup_quality": setup_quality,
            "score": confluence_score,
            "risk": risk_level,
            "recommendation": f"Signal strength is {setup_quality}. Trade with position sizing matching your risk tolerance.",
            "action_threshold": "Wait for confirmation signals before entry." if confluence_score < 5 else "Setup is forming, monitor for entry."
        }

        # Build Market Context
        market_context = {
            "regime": market.get("regime", "Unknown"),
            "volatility": volatility.get("level", "Normal") if volatility else "Normal",
            "sector": "Large Cap IT" if "TCS" in symbol or "INFY" in symbol else "Large Cap Bank" if "BANK" in symbol or "SBIN" in symbol else "Large Cap Energy" if "RELIANCE" in symbol else "Diversified",
            "interpretation": market.get("interpretation", "Monitor market structure for shifts.")
        }

        # Build Market Alignment
        alignment_score = 0
        if trend != "Unknown":
            alignment_score += 1
        if market.get("regime") in ["Bullish", "Bearish"]:
            alignment_score += 1
        if volatility.get("level") == "Normal":
            alignment_score += 1
        
        market_alignment = {
            "score": alignment_score,
            "max": 3,
            "interpretation": f"Chart structure aligns with market regime ({alignment_score}/3 factors confirmed)."
        }

        # Build Sentiment data
        if isinstance(sentiment, str):
            sentiment_data = {"label": sentiment}
        else:
            sentiment_data = {"label": sentiment.get("label", "Neutral")} if sentiment else {"label": "Neutral"}

        # Build Fibonacci data for display
        fibonacci_data = {
            "confidence": fib_confidence,
            "zone": fib.get("zone", "unknown"),
            "high": fib.get("high", current_price * 1.1) if fib else current_price * 1.1,
            "low": fib.get("low", current_price * 0.9) if fib else current_price * 0.9,
            "levels": fib.get("levels", {}) if fib else {},
            "interpretation": fib_text
        }

        # Build News data
        news_data = {"headlines": news if isinstance(news, list) else []} if news else {"headlines": []}

        return {
            "symbol": symbol,
            "price": round(current_price, 2),
            "change_pct": round(change_pct, 2),
            "trend": trend,
            "story_sections": story_sections,
            "scenarios": scenarios,
            "confluence_breakdown": {
                "trend": {"label": "Structure", "earned": 1 if trend != "Unknown" else 0, "max": 1},
                "momentum": {"label": "Momentum", "earned": 1 if momentum.get("momentum_label") != "Weak" else 0, "max": 1},
                "fib": {"label": "Fibonacci", "earned": 1 if fib.get("zone") == "golden_pocket" else 0, "max": 1},
                "liq": {"label": "Liquidity", "earned": 1 if liquidity.get("detected") else 0, "max": 1},
            },
            "confidence": confluence_score,
            "trade_quality": {
                "score": confluence_score,
                "signal_strength": "Strong" if confluence_score >= 7 else "Moderate" if confluence_score >= 4 else "Weak",
            },
            "decision_context": decision_context,
            "relative_strength": rel_strength_data,
            "market_context": market_context,
            "market_alignment": market_alignment,
            "sentiment": sentiment_data,
            "fibonacci": fibonacci_data,
            "news": news_data,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
