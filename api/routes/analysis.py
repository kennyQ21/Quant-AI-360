import logging
from fastapi import APIRouter, HTTPException

from api.dependencies import load_stock_data
from services.analysis.story_builder import build_story_sections
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

from trading_system import TradingSystem, MarketRegime

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Analysis"])

# Instantiate single source of truth globally
ts = TradingSystem()

@router.get("/stock/{symbol}/analysis-360")
async def get_analysis(symbol: str):
    """Get 360° stock analysis."""
    try:
        data = load_stock_data(symbol)
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

        story_sections = build_story_sections(structure, fib, liquidity, rs, current_price)
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

        regime_str = str(market.get("regime", "Ranging")).upper().replace(" ", "_")
        regime_map = {
            "BULL_MARKET": MarketRegime.TRENDING_UP,
            "TRENDING_UP": MarketRegime.TRENDING_UP,
            "BEAR_MARKET": MarketRegime.TRENDING_DOWN,
            "TRENDING_DOWN": MarketRegime.TRENDING_DOWN,
        }
        active_regime = regime_map.get(regime_str, MarketRegime.RANGING)

        # ONE SOURCE OF TRUTH: Execute Core System
        # returns List[TradeSignal]
        signals = ts.analyze_data(symbol, data.copy(), active_regime)

        if signals:
            best_sig = sorted(signals, key=lambda x: x.setup_score, reverse=True)[0]
            confluence_score = best_sig.setup_score
            system_signal = {
                "strategy": str(best_sig.strategy),
                "direction": str(best_sig.direction),
                "entry": best_sig.target_entry,
                "stop_loss": best_sig.stop_price,
                "take_profit": best_sig.target_price,
                "score": best_sig.setup_score,
                "ml_probability": best_sig.ml_probability
            }
        else:
            confluence_score = 0
            system_signal = None

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
            "confluence_score_10": confluence_score,
            "trade_quality": {
                "score": confluence_score,
                "signal_strength": "Strong" if confluence_score >= 8 else "Moderate" if confluence_score >= 5 else "Weak",
                "system_signal": system_signal
            },
            "fibonacci": fib,
            "market_regime": market,
            "volatility": volatility,
            "sentiment": sentiment,
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
