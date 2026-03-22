"""Relative Strength Engine — Stock vs NIFTY"""
import pandas as pd
import yfinance as yf
from typing import Dict, Any

def get_relative_strength(symbol: str, data: pd.DataFrame, benchmark: str = "^NSEI") -> Dict[str, Any]:
    try:
        bench = yf.download(benchmark, period="3mo", progress=False)
        if bench.empty or data.empty:
            return {"rs_ratio": 1.0, "outperforming": False, "interpretation": "Benchmark unavailable"}

        stock_ret = float(data["Close"].values[-1] / data["Close"].values[0] - 1) * 100
        bench_ret = float(bench["Close"].values[-1] / bench["Close"].values[0] - 1) * 100

        rs_ratio = round(stock_ret - bench_ret, 2)
        outperforming = rs_ratio > 0

        if rs_ratio > 5:
            interp = f"Stock is strongly outperforming NIFTY by {rs_ratio:.1f}% \u2014 institutional accumulation likely driving relative strength."
        elif rs_ratio > 0:
            interp = f"Stock is marginally outperforming NIFTY by {rs_ratio:.1f}% \u2014 mild relative strength, monitor for persistence."
        elif rs_ratio > -5:
            interp = f"Stock is underperforming NIFTY by {abs(rs_ratio):.1f}% \u2014 weak relative strength, proceed with caution."
        else:
            interp = f"Stock is significantly underperforming NIFTY by {abs(rs_ratio):.1f}% \u2014 institutional distribution creating persistent headwind."

        return {
            "stock_return_3m": round(stock_ret, 2),
            "nifty_return_3m": round(bench_ret, 2),
            "rs_ratio": rs_ratio,
            "outperforming": outperforming,
            "interpretation": interp,
        }
    except Exception as e:
        return {"rs_ratio": 0.0, "outperforming": False, "interpretation": str(e)}
