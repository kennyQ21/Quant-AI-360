import logging
import yfinance as yf
from typing import Dict, Any

logger = logging.getLogger(__name__)

def analyze_sector_rotation(lookback_days: int = 20) -> Dict[str, Any]:
    """
    Phase 12 Market Intelligence: Sector Rotation
    Analyzes relative performance of key Indian sectors against the broader market.
    """
    sectors = {
        "IT": "^CNXIT",
        "Bank": "^NSEBANK",
        "Auto": "^CNXAUTO",
        "Pharma": "^CNXPHARMA",
        "FMCG": "^CNXFMCG",
        "Metal": "^CNXMETAL"
    }
    
    try:
        symbols = list(sectors.values()) + ["^NSEI"] # Add NIFTY 50 as benchmark
        data = yf.download(symbols, period=f"{lookback_days+5}d", progress=False)
        
        if data.empty or "Close" not in data.columns:
            return {"leading": [], "lagging": [], "benchmark_return": 0.0}
            
        close = data["Close"]
        # Calculate N-day return
        returns = (close.iloc[-1] - close.iloc[-lookback_days]) / close.iloc[-lookback_days]
        
        benchmark_return = returns["^NSEI"]
        
        leading = []
        lagging = []
        
        for name, symbol in sectors.items():
            if symbol in returns.index:
                sector_return = returns[symbol]
                if sector_return > benchmark_return:
                    leading.append({"sector": name, "outperformance": round((sector_return - benchmark_return) * 100, 2)})
                else:
                    lagging.append({"sector": name, "underperformance": round((benchmark_return - sector_return) * 100, 2)})
                    
        # Sort by magnitude
        leading = sorted(leading, key=lambda x: x["outperformance"], reverse=True)
        lagging = sorted(lagging, key=lambda x: x["underperformance"], reverse=True)
        
        return {
            "leading": leading,
            "lagging": lagging,
            "benchmark_return_pct": round(benchmark_return * 100, 2),
            "lookback_days": lookback_days
        }
        
    except Exception as e:
        logger.error(f"Error analyzing sector rotation: {e}")
        return {"leading": [], "lagging": [], "benchmark_return": 0.0}
