from fastapi import APIRouter, HTTPException
from typing import Dict, Any

router = APIRouter(tags=["Market"])

@router.get("/market/context")
async def get_market() -> Dict[str, Any]:
    """Retrieve NIFTY 50 market context (regime, trend, volatility)."""
    try:
        from services.market_regime.engine import get_market_context
        ctx = get_market_context("^NSEI")
        return ctx
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
