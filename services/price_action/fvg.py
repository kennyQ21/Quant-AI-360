"""
FAIR VALUE GAP (FVG) DETECTION
Identifies imbalances created when price moves fast, leaving gaps
These gaps tend to get filled as price naturally rebalances
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FVGState(Enum):
    """Possible states of an FVG"""
    FRESH = "FRESH"           # Gap not yet tested
    TESTED = "TESTED"         # Price entered zone but didn't close through
    FILLED = "FILLED"         # Price closed through entire gap
    VIOLATED = "VIOLATED"     # Price closed beyond in wrong direction (becomes IFVG)
    STALE = "STALE"           # FVG age exceeded max_age


@dataclass
class FVG:
    """Fair Value Gap representation"""
    top: float          # Top boundary of gap
    bottom: float       # Bottom boundary of gap
    direction: str      # 'BULLISH' or 'BEARISH'
    candle_index: int   # Where the gap was created
    state: FVGState = FVGState.FRESH
    touches: int = 0    # How many times price touched the zone
    
    def __post_init__(self):
        """Calculate gap size"""
        self.gap_size = abs(self.top - self.bottom)
        self.gap_size_pct = (self.gap_size / min(self.top, self.bottom)) * 100
    
    def contains_price(self, price: float) -> bool:
        """Check if price is inside the FVG zone"""
        return min(self.top, self.bottom) <= price <= max(self.top, self.bottom)
    
    def is_tested(self, price: float) -> bool:
        """Price entered the zone"""
        return self.contains_price(price)
    
    def is_filled(self, high: float, low: float) -> bool:
        """Price fully closed through the zone"""
        if self.direction == 'BULLISH':
            # For bullish FVG, need to close above top
            return low >= self.top
        else:  # BEARISH
            # For bearish FVG, need to close below bottom
            return high <= self.bottom
    
    def is_violated(self, close: float) -> bool:
        """FVG violated - price closed beyond it"""
        if self.direction == 'BULLISH':
            # Bullish FVG violated if close below bottom
            return close < self.bottom
        else:  # BEARISH
            # Bearish FVG violated if close above top
            return close > self.top


class FVGDetector:
    """
    Fair Value Gap Detection
    
    Concept: When price moves fast (strong momentum), it creates gaps.
    These imbalances need to be filled - price will likely return.
    
    Bullish FVG: Candle 1 high < Candle 3 low (gap left above candle 1)
    Bearish FVG: Candle 1 low > Candle 3 high (gap left below candle 1)
    
    Quality: Strong middle candle (candle 2) = strong momentum
    """
    
    def __init__(self, min_gap_size_pct: float = 0.2, max_gap_size_pct: float = 3.0, max_age: int = 30, min_volume_multiplier: float = 1.5):
        """
        Args:
            min_gap_size_pct: Minimum gap size to consider (0.2% = filter noise)
            max_gap_size_pct: Maximum gap size to consider (3%+ is rare/unreliable)
            max_age: Maximum age (in candles) before an FVG becomes stale.
            min_volume_multiplier: Minimum volume multiplier vs average for validation.
        """
        self.min_gap_size_pct = min_gap_size_pct
        self.max_gap_size_pct = max_gap_size_pct
        self.max_age = max_age
        self.min_volume_multiplier = min_volume_multiplier
        self.fvg_list: List[FVG] = []
    
    def detect_bullish_fvg(self, h1: float, l1: float, 
                           h2: float, l2: float,
                           h3: float, l3: float,
                           index: int) -> Optional[FVG]:
        """
        Detect bullish FVG
        Candle 1 high < Candle 3 low = imbalance above candle 1
        
        Middle candle should be strong: large body, small wicks
        """
        # Check if gap exists
        if h1 >= l3:
            return None  # No gap
        
        gap_size = l3 - h1
        gap_size_pct = (gap_size / h1) * 100
        
        # Filter by size
        if gap_size_pct < self.min_gap_size_pct or gap_size_pct > self.max_gap_size_pct:
            return None
        
        # Check middle candle quality (strong momentum)
        middle_body = abs(h2 - l2)  # Body size

        
        # Strong candle = large body, small wicks
        if middle_body < gap_size * 0.5:  # Body should be substantial
            return None  # Middle candle not strong enough
        
        return FVG(
            top=l3,
            bottom=h1,
            direction='BULLISH',
            candle_index=index - 1,  # Index of candle 2 (middle)
            state=FVGState.FRESH
        )
    
    def detect_bearish_fvg(self, h1: float, l1: float,
                           h2: float, l2: float,
                           h3: float, l3: float,
                           index: int) -> Optional[FVG]:
        """
        Detect bearish FVG
        Candle 1 low > Candle 3 high = imbalance below candle 1
        """
        # Check if gap exists
        if l1 <= h3:
            return None  # No gap
        
        gap_size = l1 - h3
        gap_size_pct = (gap_size / l1) * 100
        
        # Filter by size
        if gap_size_pct < self.min_gap_size_pct or gap_size_pct > self.max_gap_size_pct:
            return None
        
        # Check middle candle quality
        middle_body = abs(h2 - l2)
        
        if middle_body < gap_size * 0.5:
            return None
        
        return FVG(
            top=l1,
            bottom=h3,
            direction='BEARISH',
            candle_index=index - 1,
            state=FVGState.FRESH
        )
    
    def detect_all_fvgs(self, df: pd.DataFrame, lookback: int = 100) -> List[FVG]:
        """
        Detect all FVGs in recent price action
        
        Args:
            df: OHLCV DataFrame
            lookback: How many candles to scan
        
        Returns:
            List of all detected FVGs
        """
        if len(df) < 3 + lookback:
            lookback = len(df) - 3
        
        if lookback < 3:
            return []
        
        fvgs = []
        start_idx = max(0, len(df) - lookback - 3)
        
        # Calculate moving average volume for impulsive validation
        if 'Volume' in df.columns:
            # 20-period volume SMA
            df['Vol_MA20'] = df['Volume'].rolling(window=20, min_periods=1).mean()
        
        # Check every 3 consecutive candles
        for i in range(start_idx, len(df) - 2):
            c1_h = df['High'].iloc[i]
            c1_l = df['Low'].iloc[i]
            c2_h = df['High'].iloc[i + 1]
            c2_l = df['Low'].iloc[i + 1]
            c3_h = df['High'].iloc[i + 2]
            c3_l = df['Low'].iloc[i + 2]
            
            # Check impulsive validation volume
            if 'Volume' in df.columns and 'Vol_MA20' in df.columns:
                vol2 = float(np.asarray(df['Volume'])[i + 1])
                avg_vol = df['Vol_MA20'].iloc[i + 1]
                if avg_vol > 0 and vol2 < avg_vol * self.min_volume_multiplier:
                    continue  # Invalid FVG due to lack of impulsive volume
            
            # Try bullish FVG
            bullish = self.detect_bullish_fvg(c1_h, c1_l, c2_h, c2_l, c3_h, c3_l, i + 2)
            if bullish:
                fvgs.append(bullish)
            
            # Try bearish FVG
            bearish = self.detect_bearish_fvg(c1_h, c1_l, c2_h, c2_l, c3_h, c3_l, i + 2)
            if bearish:
                fvgs.append(bearish)
        
        return fvgs
    
    def update_fvg_states(self, df: pd.DataFrame):
        """
        Update state of all tracked FVGs based on current price
        Call this on every new candle
        """
        current_high = df['High'].iloc[-1]
        current_low = df['Low'].iloc[-1]
        current_close = df['Close'].iloc[-1]
        current_idx = len(df) - 1
        
        for fvg in self.fvg_list:
            if fvg.state in [FVGState.FILLED, FVGState.VIOLATED, FVGState.STALE]:
                continue  # Already resolved
                
            # Stale check
            if current_idx - fvg.candle_index > self.max_age:
                fvg.state = FVGState.STALE
                continue
            
            # Check if price entered zone
            if fvg.is_tested(current_high) or fvg.is_tested(current_low):
                if fvg.state == FVGState.FRESH:
                    fvg.touches += 1
                    fvg.state = FVGState.TESTED
            
            # Check if price filled the gap
            if fvg.is_filled(current_high, current_low):
                fvg.state = FVGState.FILLED
            
            # Check if price violated the gap (becomes IFVG)
            elif fvg.is_violated(current_close):
                fvg.state = FVGState.VIOLATED
    
    def analyze(self, df: pd.DataFrame) -> Dict:
        """
        Complete FVG analysis
        
        Returns:
            Dict with FVG statistics and setup information
        """
        # Detect FVGs
        new_fvgs = self.detect_all_fvgs(df, lookback=100)
        
        # Add unique FVGs to list (avoid duplicates)
        for new_fvg in new_fvgs:
            exists = False
            for existing in self.fvg_list:
                if abs(new_fvg.top - existing.top) < 0.001 and \
                   abs(new_fvg.bottom - existing.bottom) < 0.001 and \
                   new_fvg.direction == existing.direction:
                    exists = True
                    break
            if not exists:
                self.fvg_list.append(new_fvg)
        
        # Update states
        self.update_fvg_states(df)
        
        # Get fresh FVGs (not yet tested or filled)
        fresh_fvgs = [f for f in self.fvg_list if f.state == FVGState.FRESH]
        
        # Get tested FVGs (price entered but not filled)
        tested_fvgs = [f for f in self.fvg_list if f.state == FVGState.TESTED]
        
        return {
            'total_fvgs': len(self.fvg_list),
            'fresh_fvgs': len(fresh_fvgs),
            'tested_fvgs': len(tested_fvgs),
            'filled_fvgs': len([f for f in self.fvg_list if f.state == FVGState.FILLED]),
            'violated_fvgs': len([f for f in self.fvg_list if f.state == FVGState.VIOLATED]),
            'fvg_list': self.fvg_list,
            'fresh_fvg_details': [{'price': f.top, 'direction': f.direction, 'size_pct': f.gap_size_pct} for f in fresh_fvgs],
        }
    
    def get_nearest_fresh_fvg_above(self, price: float) -> Optional[FVG]:
        """Get nearest fresh FVG above current price"""
        fresh_above = [f for f in self.fvg_list if f.state == FVGState.FRESH and f.top > price]
        if not fresh_above:
            return None
        return min(fresh_above, key=lambda x: x.top - price)
    
    def get_nearest_fresh_fvg_below(self, price: float) -> Optional[FVG]:
        """Get nearest fresh FVG below current price"""
        fresh_below = [f for f in self.fvg_list if f.state == FVGState.FRESH and f.bottom < price]
        if not fresh_below:
            return None
        return max(fresh_below, key=lambda x: price - x.bottom)
