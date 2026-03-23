"""
CONFLUENCE ENGINE (TIER SYSTEM)
Multi-detector scoring for high-probability setups based on Tiers.

Tier 1 (High conviction): Liquidity Sweep + FVG + BOS
Tier 2 (Trend continuation): Trend + FVG pullback
Tier 3 (Breakout): Consolidation breakout
"""
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SetupTier(Enum):
    TIER_1_SMC = "Tier1_SMC"
    TIER_2_TREND = "Tier2_Trend"
    TIER_3_BREAKOUT = "Tier3_Breakout"
    NONE = "None"
    
class ConfluenceSignal(Enum):
    """Backwards compatibility dummy for API imports"""
    SMC_FULL_SETUP = "SMC Full Setup"
    VCP_BREAKOUT = "VCP Breakout"
    FVG_PULLBACK = "FVG Pullback"
    LIQUIDITY_SWEEP = "Liquidity Sweep"
    AMD_SETUP = "AMD Distribution"
    IFVG_BOUNCE = "IFVG Bounce"
    BREAKOUT_RETEST = "Breakout Retest"
    CONSOLIDATION_HOLD = "Consolidation Forming"

class Signal(Enum):
    BUY = "BUY"
    SELL = "SELL"
    WAIT = "WAIT"

@dataclass
class ConfluenceSetup:
    setup_type: str
    confidence: float
    signal: str
    direction: str  # LONG, SHORT, WAIT
    reasons: List[str]
    entry_type: str
    
    # Financial metrics
    entry_price: float
    stop_loss: float
    target1: float
    target2: float
    risk_reward: float
    
    # Backwards compatibility properties used by existing frontend logic
    signal_name: str
    score: float
    notes: str
    components: List[str]

class ConfluenceEngine:
    """
    Tier-based scoring engine
    """
    
    def __init__(self, stop_loss_pct: float = 2.0, target_ratio: float = 2.0):
        # Enforcing Rule 8: Reward >= 2x Risk
        self.stop_loss_pct = stop_loss_pct
        self.target_ratio = max(2.0, target_ratio) 
    
    def _to_dict(self, obj: Any) -> Union[Dict, Any]:
        """Recursively convert dataclass to dict if needed"""
        if obj is None:
            return None
        
        if hasattr(obj, '__dataclass_fields__'):
            result = {}
            for field_name, field_value in asdict(obj).items():
                result[field_name] = self._to_dict(field_value) if hasattr(field_value, '__dataclass_fields__') else field_value
            return result
        elif isinstance(obj, dict):
            return {k: self._to_dict(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return obj
        else:
            return obj
    
    def score_setup(
        self,
        order_flow: Any,
        liquidity: Any,
        fvg: Any,
        ifvg: Any,
        amd: Any,
        vcp: Any,
        breakout: Any,
        current_price: float,
        min_confluence_score: int = 50
    ) -> Optional[ConfluenceSetup]:
        detectors_output = {
            'order_flow': order_flow,
            'liquidity': liquidity,
            'fvg': fvg,
            'breakout': breakout
        }
        return self.score_multiple(detectors_output, current_price)

    def score_multiple(
        self,
        detectors_output: Dict,
        current_price: float
    ) -> Optional[ConfluenceSetup]:
        
        order_flow = self._to_dict(detectors_output.get('order_flow', {}))
        liquidity = self._to_dict(detectors_output.get('liquidity', {}))
        fvg = self._to_dict(detectors_output.get('fvg', {}))
        breakout = self._to_dict(detectors_output.get('breakout', {}))
        
        # Extract Features
        trend = order_flow.get("trend", "NONE") if order_flow else "NONE"
        last_bos = order_flow.get("last_bos", "None") if order_flow else "None"
        
        recent_sweeps = liquidity.get("sweeps", []) if liquidity else []
        has_swing_sweep = len(recent_sweeps) > 0
        sweep_dir = None
        if has_swing_sweep:
            latest_sweep = recent_sweeps[-1]
            lvl_type = latest_sweep.get("type", "") if isinstance(latest_sweep, dict) else getattr(latest_sweep, "type", "")
            if "LOW" in lvl_type or lvl_type in ["PREV_DAY_LOW", "RANGE_LOW"]:
                sweep_dir = "BULLISH" 
            else:
                sweep_dir = "BEARISH"
                
        fresh_fvgs = fvg.get("fresh_fvgs", 0) if fvg else 0
        total_fvgs = fvg.get("total_fvgs", 0) if fvg else 0
        has_fvg = fresh_fvgs > 0 or total_fvgs > 0
        
        fvg_list = fvg.get("fvg_list", []) if fvg else []
        recent_fvg_dir = None
        if fvg_list and hasattr(fvg_list, '__len__') and len(fvg_list) > 0:
            item = fvg_list[-1]
            recent_fvg_dir = item.get("direction") if isinstance(item, dict) else getattr(item, "direction", None)

        consolidation_detected = breakout.get("consolidation_detected", False) if breakout else False
        breakout_triggered = breakout.get("breakout_triggered", False) if breakout else False
        
        setup_type = SetupTier.NONE.value
        confidence = 0
        signal = Signal.WAIT.value
        direction = "WAIT"
        reasons = []
        entry_type = "None"
        
        # Priority Logic: Tier 1 > Tier 2 > Tier 3
        
        ## TIER 1 - SMC Reversal
        if has_swing_sweep and has_fvg and last_bos != "None":
            setup_type = SetupTier.TIER_1_SMC.value
            confidence = 80
            entry_type = "FVG/Sweep Reversal"
            reasons = ["Liquidity Sweep Detected", "BOS Confirmed", "FVG Present"]
            
            if sweep_dir == "BULLISH":
                direction = "LONG"
                signal = Signal.BUY.value
            else:
                direction = "SHORT"
                signal = Signal.SELL.value
                
            # Boosters
            if (direction == "LONG" and trend == "UPTREND") or (direction == "SHORT" and trend == "DOWNTREND"):
                confidence += 10
                reasons.append("HTF Trend Alignment (+10)")
                
        ## TIER 2 - Trend Continuation
        elif (trend == "UPTREND" or trend == "DOWNTREND") and has_fvg:
            setup_type = SetupTier.TIER_2_TREND.value
            confidence = 65
            entry_type = "FVG Pullback"
            
            direction = "LONG" if trend == "UPTREND" else "SHORT"
            signal = Signal.BUY.value if direction == "LONG" else Signal.SELL.value
            
            reasons = [f"HTF Trend: {trend}", "FVG Pullback Entry"]
            
            if recent_fvg_dir and recent_fvg_dir != ("BULLISH" if direction == "LONG" else "BEARISH"):
                confidence -= 10
                reasons.append("Recent FVG pushes against trend (-10)")
            else:
                confidence += 5
                reasons.append("FVG aligns with trend (+5)")
                
            if has_swing_sweep and sweep_dir != ("BULLISH" if direction == "LONG" else "BEARISH"):
                confidence -= 15
                reasons.append("Opposing liquidity sweep warning (-15)")

        ## TIER 3 - Breakout / VCP
        elif consolidation_detected and breakout_triggered:
            setup_type = SetupTier.TIER_3_BREAKOUT.value
            confidence = 60
            entry_type = "Breakout/Retest"
            
            direction = "LONG" if trend != "DOWNTREND" else "SHORT"
            signal = Signal.BUY.value if direction == "LONG" else Signal.SELL.value
            
            reasons = ["Consolidation Detected", "Breakout Triggered"]
            
            if trend == ("UPTREND" if direction == "LONG" else "DOWNTREND"):
                confidence += 10
                reasons.append("Breakout aligns with Trend (+10)")

        # Return empty if nothing passes
        if setup_type == SetupTier.NONE.value:
            return None
            
        confidence = min(max(confidence, 0), 100)
        
        # R:R Logic
        stop_dist = current_price * (self.stop_loss_pct / 100)
        stop_loss_val = current_price - stop_dist if direction == "LONG" else current_price + stop_dist
        
        risk = abs(current_price - stop_loss_val)
        reward = risk * self.target_ratio
        
        target1_val = current_price + reward if direction == "LONG" else current_price - reward
        target2_val = current_price + (reward * 1.5) if direction == "LONG" else current_price - (reward * 1.5)

        return ConfluenceSetup(
            setup_type=setup_type,
            confidence=confidence,
            signal=signal,
            direction=direction,
            reasons=reasons,
            entry_type=entry_type,
            entry_price=current_price,
            stop_loss=stop_loss_val,
            target1=target1_val,
            target2=target2_val,
            risk_reward=self.target_ratio,
            signal_name=setup_type,
            score=confidence,
            notes=", ".join(reasons),
            components=reasons
        )
