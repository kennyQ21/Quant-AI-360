"""
CONFLUENCE ENGINE
Multi-detector scoring for high-probability SMC setups

Scoring System:
- Order Flow: 20 pts (NON-NEGOTIABLE: must be bullish or no trade)
- Liquidity Sweep: 20 pts (entry at swept level + reversal)
- FVG (Fresh/Tested): 15 pts (imbalance = target zone)
- AMD Model: 15 pts (3-phase institutional setup)
- VCP/Breakout: 15 pts (tight consolidation eruption)
- IFVG: 10 pts (violated zones = high probability)
- Volume Profile: 5 pts (volume confirmation)

Total: 100 pts
Thresholds:
- 75+: HIGH PROBABILITY (execute)
- 50-74: MEDIUM PROBABILITY (wait for confluence)
- <50: SKIP (poor setup)
"""
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceSignal(Enum):
    """Trading signal classifications"""
    SMC_FULL_SETUP = "SMC Full Setup"           # All signals align
    VCP_BREAKOUT = "VCP Breakout"               # Consolidation breakout
    FVG_PULLBACK = "FVG Pullback"                # FVG retest entry
    LIQUIDITY_SWEEP = "Liquidity Sweep"          # Sweep + reversal
    AMD_SETUP = "AMD Distribution"              # 3-phase complete
    IFVG_BOUNCE = "IFVG Bounce"                 # Bounce from violated zone
    BREAKOUT_RETEST = "Breakout Retest"         # Breakout + retest
    CONSOLIDATION_HOLD = "Consolidation Forming" # Not yet triggered


@dataclass
class ConfluenceSetup:
    """Complete trade setup with all components"""
    signal_name: str
    score: float
    direction: str  # LONG or SHORT
    entry_price: float
    stop_loss: float
    target1: float
    target2: float
    confidence: str  # HIGH, MEDIUM, LOW
    
    # Component breakdown
    order_flow_score: int
    liquidity_score: int
    fvg_score: int
    amd_score: int
    vcp_score: int
    ifvg_score: int
    volume_score: int
    
    # Setup components (for transparency)
    components: List[str]
    notes: str


class ConfluenceEngine:
    """
    Multi-detector scoring engine
    """
    
    def __init__(self, stop_loss_pct: float = 2.0, target_ratio: float = 2.0):
        """
        stop_loss_pct: % distance for stop loss from entry
        target_ratio: risk:reward ratio (e.g., 2.0 = 1:2)
        """
        self.stop_loss_pct = stop_loss_pct
        self.target_ratio = target_ratio
    
    def _to_dict(self, obj: Any) -> Union[Dict, Any]:
        """Recursively convert dataclass to dict if needed"""
        if obj is None:
            return None
        
        if hasattr(obj, '__dataclass_fields__'):
            # It's a dataclass, convert it
            result = {}
            for field_name, field_value in asdict(obj).items():
                result[field_name] = self._to_dict(field_value) if hasattr(field_value, '__dataclass_fields__') else field_value
            return result
        elif isinstance(obj, dict):
            # It's a dict, recurse on values
            return {k: self._to_dict(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            # It's a list, recurse on items but keep as list (for liquidity_levels, fvg_list, etc)
            return obj
        else:
            return obj
    
    def _score_order_flow(self, order_flow_analysis: Dict) -> Tuple[int, bool]:
        """
        Score order flow component
        
        NON-NEGOTIABLE: Returns (score, is_bullish)
        - Must be bullish trend or no trade possible
        Returns: (score 0-20, is_bullish)
        """
        if not order_flow_analysis or order_flow_analysis.get('phase') == 'NONE':
            return 0, False
        
        trend = order_flow_analysis.get('trend')
        quality = order_flow_analysis.get('quality', 0)
        
        # Bullish setup
        if trend == 'UPTREND':
            base_score = 15
            quality_bonus = min(5, quality / 20)  # Quality 0-100 normalized to 0-5
            return int(base_score + quality_bonus), True
        
        # Bearish setup
        elif trend == 'DOWNTREND':
            base_score = 15
            quality_bonus = min(5, quality / 20)
            return int(base_score + quality_bonus), False
        
        # Range = no clear direction (medium quality)
        elif trend == 'RANGE':
            return 5, None  # Neutral, still tradeable with extra confluence
        
        return 0, False
    
    def _score_liquidity(self, liquidity_analysis: Any, entry_price: float) -> int:
        """
        Score liquidity component
        
        Best: Entry at liquidity level with reversal = 20 pts
        Good: Entry near liquidity = 15 pts
        OK: Liquidity present = 10 pts
        """
        if not liquidity_analysis:
            return 0
        
        # Convert to dict if it's a dataclass
        if hasattr(liquidity_analysis, '__dataclass_fields__'):
            liquidity_analysis = asdict(liquidity_analysis)
        
        levels = liquidity_analysis.get('liquidity_levels', [])
        if not levels:
            return 0
        
        # Check proximity to liquidity
        tolerance = entry_price * 0.01  # 1% tolerance
        
        # Handle both LiquidityLevel objects and dicts
        at_liquidity = False
        for level in levels:
            level_price = level.price if hasattr(level, 'price') else level.get('price', 0)
            if abs(level_price - entry_price) < tolerance:
                at_liquidity = True
                break
        
        if at_liquidity:
            # Bonus for high strength level
            strengths = []
            for level in levels:
                strength = level.strength if hasattr(level, 'strength') else level.get('strength', 0)
                strengths.append(strength)
            strength = max(strengths) if strengths else 0
            return min(20, 15 + int(strength / 20))
        
        return 5  # Partial credit for presence
    
    def _score_fvg(self, fvg_analysis: Any) -> int:
        """
        Score FVG component
        
        Fresh FVG = 15 pts (untested, full potential)
        Tested FVG = 12 pts (touched but not filled)
        Entry in gap = 15 pts (imbalance = directional move)
        """
        if not fvg_analysis:
            return 0
        
        # Convert to dict if it's a dataclass
        if hasattr(fvg_analysis, '__dataclass_fields__'):
            fvg_analysis = asdict(fvg_analysis)
        
        total = fvg_analysis.get('total_fvgs', fvg_analysis.get('total_count', 0))
        if total == 0:
            return 0
        
        fresh_fvgs = fvg_analysis.get('fresh_fvgs', fvg_analysis.get('fresh_count', 0))
        tested_fvgs = fvg_analysis.get('tested_fvgs', fvg_analysis.get('tested_count', 0))
        
        if fresh_fvgs > 0:
            return 15
        elif tested_fvgs > 0:
            return 12
        
        return 5  # Partial for filled/violated
    
    def _score_amd(self, amd_analysis: Dict) -> int:
        """
        Score AMD (Accumulation/Manipulation/Distribution) component
        
        Complete 3-phase sequence = 15 pts
        Distribution phase active = 12 pts
        Accumulation detected = 8 pts
        """
        if not amd_analysis or amd_analysis.get('phase') == 'NONE':
            return 0
        
        phase = amd_analysis.get('phase')
        score = amd_analysis.get('score', 0)
        
        if phase == 'COMPLETE_SETUP':
            return 15
        elif phase == 'DISTRIBUTION':
            return 12
        elif phase == 'MANIPULATION':
            return 10
        else:
            return int(score / 10) if score else 5
    
    def _score_vcp_breakout(self, vcp_analysis: Dict, breakout_analysis: Dict) -> int:
        """
        Score VCP and Breakout combined
        
        VCP triggered breakout = 15 pts
        Fresh breakout = 12 pts
        Consolidation forming = 8 pts
        """
        points = 0
        
        # VCP score
        if vcp_analysis and vcp_analysis.get('phase') == 'BREAKOUT_TRIGGERED':
            points += 12
        elif vcp_analysis and vcp_analysis.get('phase') == 'PATTERN_FORMING':
            points += 5
        
        # Breakout score
        if breakout_analysis and breakout_analysis.get('phase') == 'BREAKOUT_TRIGGERED':
            points += 12
        elif breakout_analysis and breakout_analysis.get('phase') == 'CONSOLIDATION':
            points += 5
        
        return min(15, points)
    
    def _score_ifvg(self, ifvg_analysis: Any) -> int:
        """
        Score IFVG (Inverse FVG - violated zones)
        
        IFVG at entry = 10 pts (high probability rejection zone)
        IFVG nearby = 6 pts (valid support/resistance)
        """
        if not ifvg_analysis:
            return 0
        
        # Convert to dict if it's a dataclass
        if hasattr(ifvg_analysis, '__dataclass_fields__'):
            ifvg_analysis = asdict(ifvg_analysis)
        
        count = ifvg_analysis.get('total_count', ifvg_analysis.get('ifvg_count', 0))
        if count == 0:
            return 0
        
        if count >= 2:
            return 10
        elif count == 1:
            return 6
        
        return 3
    
    def _score_volume(self, order_flow: Dict, liquidity: Dict, 
                     fvg: Dict, breakout: Dict) -> int:
        """
        Score volume profile
        
        High volume setup = 5 pts
        Normal volume = 3 pts
        Low volume = 0 pts (warning)
        """
        volume_signals = 0
        
        # Check if any detector has volume confirmation
        if fvg and fvg.get('gap_size_avg', 0) > 0.5:  # Significant gaps
            volume_signals += 1
        
        if breakout and breakout.get('breakout'):
            if breakout['breakout'].get('volume_multiple', 0) > 1.5:
                volume_signals += 1
        
        if volume_signals >= 2:
            return 5
        elif volume_signals == 1:
            return 3
        
        return 0
    
    def score_setup(
        self,
        order_flow: Any,
        liquidity: Any,
        fvg: Any,
        ifvg: Any,
        amd: Any,
        vcp: Any,
        breakout: Any,
        current_price: float
    ) -> Optional[ConfluenceSetup]:
        """
        Score complete setup and return ConfluenceSetup if viable
        
        Returns: ConfluenceSetup or None if score < 50 or order flow not bullish/bearish
        """
        # Convert dataclasses to dicts if needed
        order_flow = self._to_dict(order_flow)
        liquidity = self._to_dict(liquidity)
        fvg = self._to_dict(fvg)
        ifvg = self._to_dict(ifvg)
        amd = self._to_dict(amd)
        vcp = self._to_dict(vcp)
        breakout = self._to_dict(breakout)
        
        # Get order flow direction (NON-NEGOTIABLE CHECK)
        of_score, is_bullish = self._score_order_flow(order_flow)
        
        if is_bullish is None:
            # Range market - requires extra confluence
            min_confluence_score = 60
        else:
            # Clear trend - standard threshold
            min_confluence_score = 50
        
        # Score all components
        liq_score = self._score_liquidity(liquidity, current_price)
        fvg_score = self._score_fvg(fvg)
        amd_score = self._score_amd(amd)
        vcp_score = self._score_vcp_breakout(vcp, breakout)
        ifvg_score = self._score_ifvg(ifvg)
        vol_score = self._score_volume(order_flow, liquidity, fvg, breakout)
        
        # Total score
        total_score = of_score + liq_score + fvg_score + amd_score + vcp_score + ifvg_score + vol_score
        
        # Filter: must have order flow confirmation
        if of_score < 5:
            return None
        
        # Filter: must meet minimum confluence
        if total_score < min_confluence_score:
            return None
        
        # Determine direction
        direction = 'LONG' if is_bullish else 'SHORT'
        
        # Calculate entry, stops, targets
        entry_price = current_price
        stop_loss = entry_price * (1 - self.stop_loss_pct / 100) if is_bullish \
                    else entry_price * (1 + self.stop_loss_pct / 100)
        
        risk = abs(entry_price - stop_loss)
        reward = risk * self.target_ratio
        
        target1 = entry_price + reward if is_bullish else entry_price - reward
        target2 = entry_price + (reward * 1.5) if is_bullish else entry_price - (reward * 1.5)
        
        # Determine confidence level
        if total_score >= 75:
            confidence = 'HIGH'
        elif total_score >= 60:
            confidence = 'MEDIUM'
        else:
            confidence = 'LOW'
        
        # Determine signal name
        components = []
        if fvg_score >= 12:
            components.append("Fresh FVG")
        if amd_score >= 12:
            components.append("AMD Complete")
        if vcp_score >= 12:
            components.append("VCP Breakout")
        if liq_score >= 15:
            components.append("Liquidity Sweep")
        if ifvg_score >= 8:
            components.append("IFVG Bounce")
        
        # Generate signal name
        if len(components) >= 4:
            signal_name = ConfluenceSignal.SMC_FULL_SETUP.value
        elif "VCP Breakout" in components or "Breakout" in str(breakout):
            signal_name = ConfluenceSignal.VCP_BREAKOUT.value
        elif "Fresh FVG" in components:
            signal_name = ConfluenceSignal.FVG_PULLBACK.value
        elif "AMD Complete" in components:
            signal_name = ConfluenceSignal.AMD_SETUP.value
        elif "Liquidity Sweep" in components:
            signal_name = ConfluenceSignal.LIQUIDITY_SWEEP.value
        else:
            signal_name = ConfluenceSignal.BREAKOUT_RETEST.value
        
        # Build notes
        notes = f"Score breakdown [OF:{of_score} LIQ:{liq_score} FVG:{fvg_score} AMD:{amd_score} VCP:{vcp_score} IFVG:{ifvg_score} VOL:{vol_score}]"
        
        return ConfluenceSetup(
            signal_name=signal_name,
            score=total_score,
            direction=direction,
            entry_price=entry_price,
            stop_loss=stop_loss,
            target1=target1,
            target2=target2,
            confidence=confidence,
            order_flow_score=of_score,
            liquidity_score=liq_score,
            fvg_score=fvg_score,
            amd_score=amd_score,
            vcp_score=vcp_score,
            ifvg_score=ifvg_score,
            volume_score=vol_score,
            components=components,
            notes=notes
        )
    
    def score_multiple(
        self,
        detectors_output: Dict,
        current_price: float
    ) -> Optional[ConfluenceSetup]:
        """
        Convenience method using detector outputs dict
        
        Input: {
            'order_flow': order_flow_analysis,
            'liquidity': liquidity_analysis,
            'fvg': fvg_analysis,
            'ifvg': ifvg_analysis,
            'amd': amd_analysis,
            'vcp': vcp_analysis,
            'breakout': breakout_analysis
        }
        """
        return self.score_setup(
            order_flow=detectors_output.get('order_flow'),
            liquidity=detectors_output.get('liquidity'),
            fvg=detectors_output.get('fvg'),
            ifvg=detectors_output.get('ifvg'),
            amd=detectors_output.get('amd'),
            vcp=detectors_output.get('vcp'),
            breakout=detectors_output.get('breakout'),
            current_price=current_price
        )
