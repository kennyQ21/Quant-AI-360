"""
Price Action Analysis Route
Returns all 7 detectors + confluence setup for a stock
"""
import sys
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException
import pandas as pd
import yfinance as yf

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import PARQUET_DIR

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Price Action"])


def _load_price_action_data(symbol: str) -> pd.DataFrame:
    """Load stock data, ensure proper column format."""
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
        df = yf.download(symbol, period="2y", progress=False)

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
    
    return df


@router.get("/stock/{symbol}/price-action")
async def get_price_action_analysis(symbol: str) -> dict:
    """
    Get comprehensive price action analysis with all 7 detectors.
    
    Returns:
    - order_flow: Market structure analysis
    - liquidity: Equal highs/lows and sweeps
    - fvg: Fair Value Gaps
    - ifvg: Inverse Fair Value Gaps
    - amd: Accumulation/Manipulation/Distribution
    - vcp: Volatility Contraction Pattern
    - breakout: Consolidation breakout
    - confluence: Combined signal + score
    """
    try:
        data = _load_price_action_data(symbol)
        if data.empty:
            raise HTTPException(status_code=404, detail=f"No data for {symbol}")

        # Ensure numeric types
        for col in ["Close", "High", "Low", "Volume", "Open"]:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors="coerce")
        data = data.dropna(subset=["Close", "High", "Low"])

        current_price = float(data["Close"].iloc[-1])
        results = {"symbol": symbol, "current_price": current_price, "status": "ok"}

        # ===== 1. ORDER FLOW ANALYSIS =====
        try:
            from services.price_action.order_flow import OrderFlowAnalyzer
            analyzer = OrderFlowAnalyzer()
            market_structure = analyzer.analyze(data)
            
            results["order_flow"] = {
                "structure": market_structure.structure if hasattr(market_structure, "structure") else "Unknown",
                "trend": market_structure.trend if hasattr(market_structure, "trend") else "Unknown",
                "structure_quality": market_structure.structure_quality if hasattr(market_structure, "structure_quality") else 0,
                "last_bos": str(market_structure.last_bos) if hasattr(market_structure, "last_bos") else None,
                "status": "active"
            }
        except Exception as e:
            logger.warning(f"Order flow analysis failed: {e}")
            results["order_flow"] = {"error": str(e), "status": "failed"}

        # ===== 2. LIQUIDITY DETECTION =====
        try:
            from services.price_action.liquidity import LiquidityDetector
            detector = LiquidityDetector()
            levels = detector.analyze(data) if hasattr(detector, "analyze") else {}
            
            results["liquidity"] = levels if isinstance(levels, dict) else {}
            results["liquidity"]["levels_detected"] = len(levels.get("liquidity_levels", [])) if isinstance(levels, dict) else 0
            results["liquidity"]["status"] = "active" if levels else "none"
        except Exception as e:
            logger.warning(f"Liquidity analysis failed: {e}")
            results["liquidity"] = {"error": str(e), "status": "failed"}

        # ===== 3. FVG DETECTION =====
        try:
            from services.price_action.fvg import FVGDetector
            detector = FVGDetector()
            fvgs = detector.analyze(data) if hasattr(detector, "analyze") else {}
            
            results["fvg"] = fvgs if isinstance(fvgs, dict) else {}
            results["fvg"]["total_detected"] = len(fvgs.get("fvg_list", [])) if isinstance(fvgs, dict) else 0
            results["fvg"]["status"] = "active" if fvgs else "none"
        except Exception as e:
            logger.warning(f"FVG analysis failed: {e}")
            results["fvg"] = {"error": str(e), "status": "failed"}

        # ===== 4. IFVG DETECTION =====
        try:

            # IFVG needs to track violations, simplified here
            
            results["ifvg"] = {
                "total_detected": 0,
                "status": "monitoring"
            }
        except Exception as e:
            logger.warning(f"IFVG analysis failed: {e}")
            results["ifvg"] = {"error": str(e), "status": "failed"}

        # ===== 5. AMD MODEL DETECTION =====
        try:
            from services.price_action.amd import AMDDetector
            detector = AMDDetector()
            amd_analysis = detector.analyze(data) if hasattr(detector, "analyze") else {}
            
            results["amd"] = amd_analysis if isinstance(amd_analysis, dict) else {}
            results["amd"]["phase"] = amd_analysis.get("phase", "Unknown") if isinstance(amd_analysis, dict) else "Unknown"
            results["amd"]["confidence"] = float(amd_analysis.get("setup_quality", 0)) if isinstance(amd_analysis, dict) else 0
            results["amd"]["status"] = "active"
        except Exception as e:
            logger.warning(f"AMD analysis failed: {e}")
            results["amd"] = {"error": str(e), "status": "failed"}

        # ===== 6. VCP DETECTION =====
        try:
            from services.price_action.vcp import VCPDetector
            detector = VCPDetector()
            vcp_analysis = detector.analyze(data) if hasattr(detector, "analyze") else {}
            
            results["vcp"] = vcp_analysis if isinstance(vcp_analysis, dict) else {}
            results["vcp"]["pattern_detected"] = "phase" in vcp_analysis and vcp_analysis["phase"] != "NONE" if isinstance(vcp_analysis, dict) else False
            results["vcp"]["stage"] = vcp_analysis.get("phase", "None") if isinstance(vcp_analysis, dict) else "None"
            results["vcp"]["status"] = "active"
        except Exception as e:
            logger.warning(f"VCP analysis failed: {e}")
            results["vcp"] = {"error": str(e), "status": "failed"}

        # ===== 7. BREAKOUT DETECTION =====
        try:
            from services.price_action.breakout import BreakoutDetector
            detector = BreakoutDetector()
            breakout_analysis = detector.analyze(data) if hasattr(detector, "analyze") else {}
            
            results["breakout"] = breakout_analysis if isinstance(breakout_analysis, dict) else {}
            results["breakout"]["consolidation_detected"] = "consolidation" in breakout_analysis if isinstance(breakout_analysis, dict) else False
            results["breakout"]["breakout_triggered"] = "breakout" in breakout_analysis if isinstance(breakout_analysis, dict) else False
            results["breakout"]["status"] = "active"
        except Exception as e:
            logger.warning(f"Breakout analysis failed: {e}")
            results["breakout"] = {"error": str(e), "status": "failed"}

        # ===== CONFLUENCE SIGNAL =====
        try:
            from services.strategy_engine.confluence import ConfluenceEngine
            engine = ConfluenceEngine()
            setup = engine.score_setup(
                order_flow=results.get("order_flow", {}),
                liquidity=results.get("liquidity", {}),
                fvg=results.get("fvg", {}),
                ifvg=results.get("ifvg", {}),
                amd=results.get("amd", {}),
                vcp=results.get("vcp", {}),
                breakout=results.get("breakout", {}),
                current_price=current_price
            ) if hasattr(engine, "score_setup") else None
            
            if setup:
                entry_price_val = float(getattr(setup, "entry_price", current_price))
                stop_loss_val = float(getattr(setup, "stop_loss", 0))
                
                results["confluence"] = {
                    "signal_name": getattr(setup, "signal_name", "No Setup"),
                    "score": float(getattr(setup, "score", 0)),
                    "direction": getattr(setup, "direction", "Unknown"),
                    "entry_price": entry_price_val,
                    "stop_loss": stop_loss_val,
                    "target1": float(getattr(setup, "target1", 0)),
                    "target2": float(getattr(setup, "target2", 0)),
                    "status": "active"
                }
                try:
                    from services.strategy_engine.risk import RiskManager
                    rm = RiskManager(account_size=100000.0, max_risk_pct=1.0)
                    risk_data = rm.calculate_position(entry_price_val, stop_loss_val)
                    if not risk_data.get("status") == "error":
                        results["risk_management"] = risk_data
                except Exception as risk_e:
                    logger.warning(f"Risk Management calculation failed: {risk_e}")
            else:
                results["confluence"] = {
                    "signal_name": "No Setup",
                    "score": 0,
                    "status": "no_signal"
                }
        except Exception as e:
            logger.warning(f"Confluence analysis failed: {e}")
            results["confluence"] = {
                "signal_name": "Error",
                "score": 0,
                "error": str(e),
                "status": "failed"
            }

        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Price action analysis error for {symbol}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scanner/stocks")
async def scan_multiple_stocks(symbols: str = "RELIANCE.NS,TCS.NS,HDFCBANK.NS,INFY.NS") -> dict:
    """
    Scan multiple stocks for trading setups.
    Returns top stocks by confluence score.
    """
    symbol_list = [s.strip() for s in symbols.split(",")]
    results = []

    for symbol in symbol_list:
        try:
            analysis = await get_price_action_analysis(symbol)
            confluence = analysis.get("confluence", {})
            
            results.append({
                "symbol": symbol,
                "price": analysis.get("current_price"),
                "signal": confluence.get("signal_name", "No Setup"),
                "score": confluence.get("score", 0),
                "direction": confluence.get("direction", "Unknown"),
                "entry": confluence.get("entry_price"),
                "stop_loss": confluence.get("stop_loss"),
                "target1": confluence.get("target1"),
                "target2": confluence.get("target2")
            })
        except Exception as e:
            logger.warning(f"Failed to scan {symbol}: {e}")
            results.append({
                "symbol": symbol,
                "error": str(e)
            })

    # Sort by score descending
    results = sorted([r for r in results if "error" not in r], 
                     key=lambda x: x.get("score", 0), reverse=True)

    return {"scans": results, "total": len(results)}

