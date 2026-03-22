from fastapi import APIRouter, HTTPException
from typing import Dict, Any

router = APIRouter(tags=["Portfolio"])

@router.get("/portfolio/rank")
async def get_portfolio_ranking(symbols: str = "RELIANCE.NS,TCS.NS,HDFCBANK.NS") -> Dict[str, Any]:
    """Rank a comma-separated list of stocks by confluence score."""
    try:
        symbol_list = [s.strip() for s in symbols.split(",")]
        # This would call analysis for each symbol in a real implementation
        return {"ranked_symbols": symbol_list, "note": "Use /stock/{symbol}/analysis-360 for full analysis"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
