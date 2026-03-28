from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import pandas as pd
from pathlib import Path

router = APIRouter(tags=["Portfolio"])

@router.get("/portfolio/pnl")
async def get_portfolio_pnl() -> Dict[str, Any]:
    """Fetch Portfolio PnL metrics and latest trades from master log."""
    try:
        log_path = Path("data/results/phase2_master_log.csv")
        if not log_path.exists():
            return {"error": "No trade logs found. Run backtest first."}
            
        df = pd.read_csv(log_path)
        
        if df.empty:
            return {"error": "Trade log is empty."}
            
        # Basic metrics
        total_trades = len(df)
        winners = len(df[df['profit_loss_pct'] > 0])
        win_rate = (winners / total_trades) * 100 if total_trades > 0 else 0
        
        avg_win = df[df['profit_loss_pct'] > 0]['profit_loss_pct'].mean() if winners > 0 else 0
        avg_loss = df[df['profit_loss_pct'] <= 0]['profit_loss_pct'].mean() if (total_trades - winners) > 0 else 0
        
        # Cumulative PnL Curve
        df['equity_curve'] = df['profit_loss_pct'].cumsum()
        
        # Latest 50 trades
        latest_trades = df.tail(50).iloc[::-1].fillna(0).to_dict(orient="records")
        
        # Daily Equity curve format for charts
        curve_data = []
        for idx, row in df.iterrows():
            curve_data.append({
                "time": row["exit_date"],
                "value": row["equity_curve"]
            })
            
        return {
            "metrics": {
                "total_trades": total_trades,
                "win_rate": round(win_rate, 2),
                "avg_win_pct": round(avg_win, 2),
                "avg_loss_pct": round(avg_loss, 2),
                "profit_factor": round(abs(avg_win / avg_loss), 2) if avg_loss != 0 else 0,
                "total_return_pct": round(df['profit_loss_pct'].sum(), 2)
            },
            "recent_trades": latest_trades,
            "equity_curve": curve_data
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/portfolio/rank")
async def get_portfolio_ranking(symbols: str = "RELIANCE.NS,TCS.NS,HDFCBANK.NS") -> Dict[str, Any]:
    """Rank a comma-separated list of stocks by confluence score."""
    try:
        symbol_list = [s.strip() for s in symbols.split(",")]
        # This would call analysis for each symbol in a real implementation
        return {"ranked_symbols": symbol_list, "note": "Use /stock/{symbol}/analysis-360 for full analysis"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
