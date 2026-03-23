import math
from typing import Dict

class RiskManager:
    """Prop-Desk Level Risk Management"""
    def __init__(self, account_size: float = 100000.0, max_risk_pct: float = 1.0):
        self.account_size = account_size
        self.max_risk_pct = max_risk_pct
        self.max_risk_amount = self.account_size * (self.max_risk_pct / 100.0)

    def calculate_position(self, entry_price: float, stop_loss: float) -> Dict:
        if not entry_price or not stop_loss or entry_price == stop_loss:
            return {"status": "error", "message": "Invalid entry or stop loss"}
            
        risk_per_share = abs(entry_price - stop_loss)
        risk_pct_per_share = risk_per_share / entry_price
        
        # Max shares based on our total dollar risk allowance
        suggested_shares = math.floor(self.max_risk_amount / risk_per_share)
        position_size_dollars = suggested_shares * entry_price
        
        # Actual risk based on rounded down shares
        actual_risk_dollars = suggested_shares * risk_per_share
        
        leverage_needed = position_size_dollars / self.account_size

        return {
            "account_size": self.account_size,
            "max_risk_pct": self.max_risk_pct,
            "max_risk_dollars": self.max_risk_amount,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "risk_per_share": round(risk_per_share, 4),
            "stop_distance_pct": round(risk_pct_per_share * 100, 2),
            "suggested_shares": suggested_shares,
            "position_size_dollars": round(position_size_dollars, 2),
            "actual_risk_dollars": round(actual_risk_dollars, 2),
            "leverage_needed": round(leverage_needed, 2)
        }
