

text = """from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import requests
import pandas as pd
import io

router = APIRouter(tags=["Market"])

@router.get("/market/context")
async def get_market() -> Dict[str, Any]:
    \"\"\"Retrieve NIFTY 50 market context (regime, trend, volatility).\"\"\"
    try:
        from services.market_regime.engine import get_market_context
        ctx = get_market_context("^NSEI")
        return ctx
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/market/indices/{index_name}")
async def get_index_symbols(index_name: str) -> Dict[str, Any]:
    \"\"\"Retrieve symbols for a given NSE index.\"\"\"
    urls = {
        "nifty50": "https://nsearchives.nseindia.com/content/indices/ind_nifty50list.csv",
        "nifty500": "https://nsearchives.nseindia.com/content/indices/ind_nifty500list.csv",
        "nifty_midcap_150": "https://nsearchives.nseindia.com/content/indices/ind_niftymidcap150list.csv",
        "nifty_smallcap_100": "https://nsearchives.nseindia.com/content/indices/ind_niftysmallcap100list.csv"
    }
    
    mapping = {
        "nifty50": "nifty50",
        "nifty500": "nifty500",
        "nifty midcap 200": "nifty_midcap_150",
        "nifty midcap 150": "nifty_midcap_150",
        "nifty smallcap 100": "nifty_smallcap_100"
    }
    
    key = mapping.get(index_name.lower().replace("-", " "), "nifty50")
    url = urls.get(key)
    if not url: return {"index": index_name, "symbols": []}
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            df = pd.read_csv(io.StringIO(r.text))
            symbols = [s + ".NS" for s in df["Symbol"].tolist()]
            # limit to avoid timing out the scanner for 500 stocks locally
            # let's return max first 150 for safety unless specified
            return {"index": key, "symbols": symbols}
        else:
            raise HTTPException(status_code=r.status_code, detail="Failed to fetch index")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
"""
with open("api/routes/market.py", "w") as f:
    f.write(text)
print("api/routes/market.py was written")
