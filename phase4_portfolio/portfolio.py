import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class PortfolioAllocator:
    """
    Phase 4 Portfolio Engine: Capital Allocation & Rebalancing
    Includes Hysteresis and Weekly Rebalance logic to minimize turnover.
    """
    def __init__(self, initial_capital: float = 100000.0, top_n: int = 5, hysteresis_threshold: int = 15):
        self.capital = initial_capital
        self.top_n = top_n
        self.hysteresis_threshold = hysteresis_threshold
        self.current_portfolio = {} # symbol -> allocation %
        
    def allocate(self, ranked_stocks: List[Dict[str, Any]], rebalance_threshold: float = 0.05) -> Dict[str, float]:
        """
        Allocate capital to top ranked stocks using equal weight + hysteresis.
        
        Args:
            ranked_stocks: List of dicts with 'symbol' and 'rank'. Sorted by rank (1 is best).
            rebalance_threshold: Min % drift required to execute a trade (>5%).
            
        Returns:
            Dict of symbol -> target allocation percentage.
        """
        new_portfolio = {}
        
        # 1. Evaluate existing holdings against hysteresis threshold
        for holding in self.current_portfolio.keys():
            # Find the new rank of this holding
            current_rank = next((s["rank"] for s in ranked_stocks if s["symbol"] == holding), 999)
            
            # Hysteresis trigger: Keep it if it hasn't dropped below rank 15
            if current_rank <= self.hysteresis_threshold:
                new_portfolio[holding] = 0.0 # Will calculate weight shortly
        
        # 2. Fill remaining slots with the absolute best ranked stocks
        available_slots = self.top_n - len(new_portfolio)
        for stock in ranked_stocks:
            if available_slots <= 0:
                break
            if stock["symbol"] not in new_portfolio:
                new_portfolio[stock["symbol"]] = 0.0
                available_slots -= 1
                
        # 3. Calculate target weights (Equal weighting for simplicity)
        if len(new_portfolio) == 0:
            return {}
            
        target_weight = 1.0 / len(new_portfolio)
        for sym in new_portfolio.keys():
            new_portfolio[sym] = target_weight
            
        # 4. Apply 5% Trade Threshold: Only rebalance if difference > 5%
        final_allocations = {}
        for sym, t_weight in new_portfolio.items():
            current_w = self.current_portfolio.get(sym, 0.0)
            if abs(t_weight - current_w) >= rebalance_threshold or current_w == 0.0:
                final_allocations[sym] = t_weight
            else:
                final_allocations[sym] = current_w # Maintain existing weight if shift is minor
                
        self.current_portfolio = final_allocations
        return final_allocations
