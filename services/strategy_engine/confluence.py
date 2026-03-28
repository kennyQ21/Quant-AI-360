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
    Tier-based scoring engine.

    Key improvements (Phase 4):
    - Cooldown guard: caller passes current_bar and last_fired_bar.
      Returns None if a signal was fired within cooldown_bars (default 5).
    - ATR-based stop: caller passes atr value. Stop = atr * atr_multiplier.
      Falls back to fixed stop_loss_pct if atr is 0 or None.
    - FVG recency filter: only FVGs ≤ fvg_max_age_bars old are considered fresh.
    """

    def __init__(
        self,
        stop_loss_pct: float = 2.0,
        target_ratio: float = 2.0,
        atr_multiplier: float = 1.5,
        cooldown_bars: int = 5,
        fvg_max_age_bars: int = 10,
    ):
        # Enforcing Rule 8: Reward >= 2x Risk
        self.stop_loss_pct = stop_loss_pct
        self.target_ratio = max(2.0, target_ratio)
        self.atr_multiplier = atr_multiplier
        self.cooldown_bars = cooldown_bars
        self.fvg_max_age_bars = fvg_max_age_bars
    
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
        current_price: float,
        atr: float = 0.0,
        current_bar: int = -1,
        last_fired_bar: int = -9999,
        allowed_tier: Optional[str] = None,
    ) -> Optional[ConfluenceSetup]:
        """
        Score detectors and return a ConfluenceSetup or None.

        Args:
            detectors_output: Dict from SMCScanner.run_detectors().
            current_price: Last traded price.
            atr: ATR-14 value at current bar. Used for stop-loss sizing.
                 If 0 or None, falls back to fixed stop_loss_pct.
            current_bar: Current bar index (int). Used for cooldown check.
            last_fired_bar: Bar index of the most recent signal for this
                            stock. Caller is responsible for tracking this.
                            Pass -9999 to disable cooldown.
            allowed_tier: If set, only the specified tier string
                          (e.g. "Tier1_SMC") can produce a signal — used
                          for per-strategy isolation backtests.
        """
        # ── Cooldown guard ────────────────────────────────────────────────
        if current_bar >= 0 and last_fired_bar >= 0:
            if (current_bar - last_fired_bar) < self.cooldown_bars:
                return None

        order_flow = self._to_dict(detectors_output.get('order_flow', {}))
        liquidity = self._to_dict(detectors_output.get('liquidity', {}))
        fvg = self._to_dict(detectors_output.get('fvg', {}))
        breakout = self._to_dict(detectors_output.get('breakout', {}))

        # ── Extract order flow ────────────────────────────────────────────
        trend = order_flow.get("trend", "NONE") if order_flow else "NONE"
        last_bos = order_flow.get("last_bos", "None") if order_flow else "None"

        # ── Liquidity sweeps (recency: only last sweep counts) ────────────
        recent_sweeps = liquidity.get("sweeps", []) if liquidity else []
        has_swing_sweep = len(recent_sweeps) > 0
        sweep_dir = None
        if has_swing_sweep:
            latest_sweep = recent_sweeps[-1]
            lvl_type = (
                latest_sweep.get("type", "")
                if isinstance(latest_sweep, dict)
                else getattr(latest_sweep, "type", "")
            )
            sweep_dir = "BULLISH" if ("LOW" in lvl_type or "SELL_SIDE" in lvl_type or lvl_type in ["PREV_DAY_LOW", "RANGE_LOW"]) else "BEARISH"

        # ── FVG with recency filter (≤ fvg_max_age_bars old) ──────────────
        fvg_list_raw = fvg.get("fvg_list", []) if fvg else []

        def _fvg_is_fresh(item) -> bool:
            """True if FVG is within age limit."""
            age = item.get("age_bars", 0) if isinstance(item, dict) else getattr(item, "age_bars", 0)
            # If age_bars not present, default to assuming fresh (backwards compat)
            return age <= self.fvg_max_age_bars

        fresh_fvg_list = [f for f in fvg_list_raw if _fvg_is_fresh(f)]

        # Also honour legacy "fresh_fvgs" / "untested_bullish" counts
        fresh_fvgs_count = fvg.get("fresh_fvgs", 0) if fvg else 0
        untested_bull = len(fvg.get("untested_bullish", []) if fvg else [])
        untested_bear = len(fvg.get("untested_bearish", []) if fvg else [])

        has_fvg = bool(fresh_fvg_list) or fresh_fvgs_count > 0 or (untested_bull + untested_bear) > 0

        recent_fvg_dir = None
        if fresh_fvg_list:
            item = fresh_fvg_list[-1]
            recent_fvg_dir = item.get("direction") if isinstance(item, dict) else getattr(item, "direction", None)
        elif fvg_list_raw:
            item = fvg_list_raw[-1]
            recent_fvg_dir = item.get("direction") if isinstance(item, dict) else getattr(item, "direction", None)

        # ── Breakout ──────────────────────────────────────────────────────
        consolidation_detected = breakout.get("consolidation_detected", False) if breakout else False
        breakout_triggered = breakout.get("breakout_triggered", False) if breakout else False

        setup_type = SetupTier.NONE.value
        confidence = 0
        signal = Signal.WAIT.value
        direction = "WAIT"
        reasons: List[str] = []
        entry_type = "None"

        # ── Priority Logic: Tier 1 > Tier 2 > Tier 3 ─────────────────────

        ## TIER 1 — SMC Reversal (requires sweep + fresh FVG + confirmed BOS)
        if has_swing_sweep and has_fvg and last_bos != "None":
            if allowed_tier is None or allowed_tier == SetupTier.TIER_1_SMC.value:
                setup_type = SetupTier.TIER_1_SMC.value
                confidence = 80
                entry_type = "FVG/Sweep Reversal"
                reasons = ["Liquidity Sweep Detected", "BOS Confirmed", "Fresh FVG Present"]

                direction = "LONG" if sweep_dir == "BULLISH" else "SHORT"
                signal = Signal.BUY.value if direction == "LONG" else Signal.SELL.value

                if (direction == "LONG" and trend == "UPTREND") or (direction == "SHORT" and trend == "DOWNTREND"):
                    confidence += 10
                    reasons.append("HTF Trend Alignment (+10)")

        ## TIER 2 — Trend Continuation (requires fresh FVG for entry, NOT just any FVG)
        if setup_type == SetupTier.NONE.value and bool(fresh_fvg_list) and (trend in ("UPTREND", "DOWNTREND")):
            if allowed_tier is None or allowed_tier == SetupTier.TIER_2_TREND.value:
                proposed_direction = "LONG" if trend == "UPTREND" else "SHORT"
                aligned = ("BULLISH" if proposed_direction == "LONG" else "BEARISH")
                
                # STRICT CONSTRAINT: Do not take trend continuation if it immediately enters opposing freshness
                if recent_fvg_dir and recent_fvg_dir != aligned:
                    pass
                else:
                    setup_type = SetupTier.TIER_2_TREND.value
                    confidence = 70
                    entry_type = "FVG Pullback"
                    direction = proposed_direction
                    signal = Signal.BUY.value if direction == "LONG" else Signal.SELL.value
                    reasons = [f"HTF Trend: {trend}", "Fresh FVG Pullback Entry", "FVG aligns with trend (+5)"]

                    if has_swing_sweep and sweep_dir != aligned:
                        confidence -= 15
                        reasons.append("Opposing liquidity sweep warning (-15)")

        ## TIER 3 — Breakout / VCP
        if setup_type == SetupTier.NONE.value and consolidation_detected and breakout_triggered:
            if allowed_tier is None or allowed_tier == SetupTier.TIER_3_BREAKOUT.value:
                setup_type = SetupTier.TIER_3_BREAKOUT.value
                confidence = 60
                entry_type = "Breakout/Retest"
                direction = "LONG" if trend != "DOWNTREND" else "SHORT"
                signal = Signal.BUY.value if direction == "LONG" else Signal.SELL.value
                reasons = ["Consolidation Detected", "Breakout Triggered"]

                if trend == ("UPTREND" if direction == "LONG" else "DOWNTREND"):
                    confidence += 10
                    reasons.append("Breakout aligns with Trend (+10)")

        if setup_type == SetupTier.NONE.value:
            return None

        confidence = min(max(confidence, 0), 100)

        # ── Stop-loss sizing (ATR-based preferred, fixed-% fallback) ──────
        if atr and atr > 0:
            stop_dist = atr * self.atr_multiplier
        else:
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
            components=reasons,
        )
