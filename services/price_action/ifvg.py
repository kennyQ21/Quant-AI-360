"""
INVERSE FAIR VALUE GAP (IFVG) MONITORING
When an FVG gets violated, it flips and becomes resistance/support
These are high-probability rejection zones
"""
from typing import List, Dict
import pandas as pd
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class IFVG:
    """Inverse FVG - violated FVG that now acts as resistance/support"""
    top: float          # Top boundary
    bottom: float       # Bottom boundary
    original_direction: str  # 'BULLISH' or 'BEARISH'
    acts_as: str        # 'SUPPORT' or 'RESISTANCE'
    candle_index: int   # Where violation occurred
    violation_price: float  # Price that violated it
    touched: int = 0    # Times it has been tested


class IFVGMonitor:
    """
    Monitor FVG violations and track resulting IFVGs
    
    Concept:
    - Bullish FVG violated (close below bottom): becomes IFVG resistance
    - Bearish FVG violated (close above top): becomes IFVG support
    
    Trading: IFVG rejection zones are high probability
    """
    
    def __init__(self):
        self.ifvg_list: List[IFVG] = []
    
    def register_violation(self, fvg, violation_price: float, candle_index: int):
        """Register a violated FVG as new IFVG"""
        
        # Determine what it acts as
        if fvg.direction == 'BULLISH':
            # Bullish FVG violated = resistance
            acts_as = 'RESISTANCE'
        else:
            # Bearish FVG violated = support
            acts_as = 'SUPPORT'
        
        ifvg = IFVG(
            top=fvg.top,
            bottom=fvg.bottom,
            original_direction=fvg.direction,
            acts_as=acts_as,
            candle_index=candle_index,
            violation_price=violation_price
        )
        
        # Check if this IFVG already exists
        exists = any(
            abs(i.top - ifvg.top) < 0.001 and 
            abs(i.bottom - ifvg.bottom) < 0.001
            for i in self.ifvg_list
        )
        
        if not exists:
            self.ifvg_list.append(ifvg)
            logger.info(f"IFVG registered: {acts_as} at {ifvg.top:.2f}-{ifvg.bottom:.2f}")
    
    def check_ifvg_touches(self, high: float, low: float) -> List[IFVG]:
        """Check if price is touching any IFVG zones"""
        touched = []
        
        for ifvg in self.ifvg_list:
            is_touching = (high >= ifvg.bottom and low <= ifvg.top)
            if is_touching:
                ifvg.touched += 1
                touched.append(ifvg)
        
        return touched
    
    def get_resistance_ifvgs(self, above_price: float) -> List[IFVG]:
        """Get all resistance IFVGs above price"""
        return [i for i in self.ifvg_list if i.acts_as == 'RESISTANCE' and i.top > above_price]
    
    def get_support_ifvgs(self, below_price: float) -> List[IFVG]:
        """Get all support IFVGs below price"""
        return [i for i in self.ifvg_list if i.acts_as == 'SUPPORT' and i.bottom < below_price]
    
    def analyze(self, df: pd.DataFrame = None) -> Dict:
        """Get IFVG summary"""
        resistance = [i for i in self.ifvg_list if i.acts_as == 'RESISTANCE']
        support = [i for i in self.ifvg_list if i.acts_as == 'SUPPORT']
        
        return {
            'total_ifvgs': len(self.ifvg_list),
            'resistance_ifvgs': len(resistance),
            'support_ifvgs': len(support),
            'ifvg_list': self.ifvg_list,
        }
