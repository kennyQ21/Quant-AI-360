"""
Quant AI Trading — FastAPI Backend
Serves ML predictions, charts, news, and trading suggestions.
"""
import sys
from pathlib import Path
import logging

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Routers
from api.routes.stocks import router as stocks_router
from api.routes.portfolio import router as portfolio_router
from api.routes.market import router as market_router
from api.routes.analysis import router as analysis_router
from api.routes.price_action import router as price_action_router

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Quant AI Trading API",
    description="ML-powered stock analysis, predictions, and trading suggestions",
    version="1.0.0",
)

# CORS — allow dashboard to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routes
app.include_router(stocks_router, prefix="/api")
app.include_router(portfolio_router, prefix="/api")
app.include_router(market_router, prefix="/api")
app.include_router(analysis_router, prefix="/api")
app.include_router(price_action_router, prefix="/api")

@app.get("/")
async def root():
    return {"status": "ok", "service": "Quant AI Trading API", "version": "1.0.0"}

@app.get("/api/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
