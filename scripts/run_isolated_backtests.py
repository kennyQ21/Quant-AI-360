import pandas as pd
import logging
from pathlib import Path
from tqdm import tqdm
from services.strategy_engine.scanner import SMCScanner
from services.backtesting.event_backtester import EventDrivenBacktester

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

def run_all_isolated_backtests():
    data_dir = Path("data/parquet")
    files = list(data_dir.glob("*.parquet"))[:5] # Test on first 5 stocks
    
    strategies = [
        "Liquidity Sweep",
        "FVG",
        "VCP"
    ]
    
    results_list = []
    
    for f in tqdm(files, desc="Processing stocks"):
        symbol = f.stem
        df = pd.read_parquet(f)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        scanner = SMCScanner(symbols=[symbol])
        bt = EventDrivenBacktester()
        
        # Test just the last 1000 days for standard validation
        slice_df = df.iloc[-300:]
        
        for strat in strategies:
            res = bt.run_strategy(symbol, slice_df, strat, scanner)
            
            results_list.append({
                'Symbol': symbol,
                'Strategy': strat,
                'Total Return %': res.metrics['total_return_pct'],
                'Trades': res.metrics['total_trades'],
                'Win Rate': res.metrics['win_rate'],
                'Profit Factor': res.metrics['profit_factor']
            })
            
    res_df = pd.DataFrame(results_list)
    print("\n=== ISOLATED STRATEGY RESULTS ===")
    
    # Aggregate by strategy
    agg = res_df.groupby('Strategy').agg({
        'Total Return %': 'mean',
        'Trades': 'sum',
        'Win Rate': 'mean',
        'Profit Factor': 'mean'
    }).reset_index()
    
    print(agg.to_string(index=False))
    
    # Save to memory/markdown
    with open("documentation/PHASE1_ISOLATED_BACKTESTS.md", "w") as out:
        out.write("# Phase 1: Isolated Strategy Backtests\n\n")
        out.write("This validates the generic edge for individual strategies using strict T+1 execution, 0.2% round-trip costs, and strict SL/TP.\n\n")
        out.write("### Aggregated Results\n\n")
        out.write(agg.to_markdown(index=False))
        out.write("\n\n### Detailed Results\n\n")
        out.write(res_df.to_markdown(index=False))

if __name__ == "__main__":
    run_all_isolated_backtests()
