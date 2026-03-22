"""
LIQUIDITY DETECTION
Identifies equal highs and equal lows where retail stop losses cluster
Smart money hunts these liquidity levels and sweeps through them
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class LiquidityLevel:
    """Represents a liquidity pool (equal highs or equal lows)"""
    price: float
    type: str  # 'EQUAL_HIGH', 'EQUAL_LOW', 'PREV_DAY_HIGH', 'PREV_DAY_LOW', 'RANGE_HIGH', 'RANGE_LOW'
    touches: int  # How many times this level was touched
    first_touch_index: int
    last_touch_index: int
    strength: float  # Strength score (0-100)
    tolerance: float  # % tolerance for grouping as same level
    
    def add_touch(self, index: int):
        """Register another touch of this level"""
        self.touches += 1
        self.last_touch_index = index
    
    def is_equal_level(self, price: float, tolerance: float) -> bool:
        """Check if price is within tolerance of this level"""
        diff_pct = abs(price - self.price) / self.price * 100
        return diff_pct <= tolerance


class LiquidityDetector:
    """
    Detects liquidity pools (equal highs, equal lows)
    Also tracks recent highs/lows that act as magnets
    
    Liquidity pools form at:
    1. Previous day high/low
    2. Previous week high/low
    3. Range highs/lows (consolidation boundaries)
    4. Equal highs: 2+ highs within 0.3% of each other
    5. Equal lows: 2+ lows within 0.3% of each other
    """
    
    def __init__(self, tolerance_pct: float = 0.3):
        """
        Args:
            tolerance_pct: % tolerance for grouping prices as same level
                          0.3% = default, works well for most stocks
        """
        self.tolerance_pct = tolerance_pct
        self.liquidity_levels: List[LiquidityLevel] = []
        self.prev_day_high = None
        self.prev_day_low = None
        self.prev_week_high = None
        self.prev_week_low = None
    
    def detect_equal_highs(self, df: pd.DataFrame, lookback: int = 50) -> List[LiquidityLevel]:
        """
        Detect equal highs: 2+ swing highs within tolerance
        
        Args:
            df: OHLCV DataFrame
            lookback: How many candles to scan back
        
        Returns:
            List of LiquidityLevel objects representing equal high zones
        """
        if len(df) < lookback:
            lookback = len(df)
        
        recent_data = df.tail(lookback).copy()
        highs = recent_data['High'].values
        
        # Find local highs (peaks)
        local_highs = []
        for i in range(1, len(highs) - 1):
            if highs[i] >= highs[i-1] and highs[i] >= highs[i+1]:
                local_highs.append({
                    'price': highs[i],
                    'index': len(df) - lookback + i
                })
        
        if not local_highs:
            return []
        
        # Group equal highs
        equal_high_zones = []
        used = set()
        
        for i, high in enumerate(local_highs):
            if i in used:
                continue
            
            # Find all other highs within tolerance
            zone_members = [i]
            zone_price = high['price']
            zone_indices = [high['index']]
            
            for j, other_high in enumerate(local_highs):
                if i != j and j not in used:
                    if other_high.get('price', 0):  # Safety check
                        diff_pct = abs(other_high['price'] - zone_price) / zone_price * 100
                        if diff_pct <= self.tolerance_pct:
                            zone_members.append(j)
                            zone_indices.append(other_high['index'])
                            used.add(j)
            
            # If 2+ hourly highs within tolerance = equal high level
            if len(zone_members) >= 2:
                avg_price = np.mean([local_highs[m]['price'] for m in zone_members])
                level = LiquidityLevel(
                    price=avg_price,
                    type='EQUAL_HIGH',
                    touches=len(zone_members),
                    first_touch_index=min(zone_indices),
                    last_touch_index=max(zone_indices),
                    strength=min(100, 50 + len(zone_members) * 15),  # More touches = stronger
                    tolerance=self.tolerance_pct
                )
                equal_high_zones.append(level)
            
            used.add(i)
        
        return equal_high_zones
    
    def detect_equal_lows(self, df: pd.DataFrame, lookback: int = 50) -> List[LiquidityLevel]:
        """
        Detect equal lows: 2+ swing lows within tolerance
        
        Args:
            df: OHLCV DataFrame
            lookback: How many candles to scan back
        
        Returns:
            List of LiquidityLevel objects representing equal low zones
        """
        if len(df) < lookback:
            lookback = len(df)
        
        recent_data = df.tail(lookback).copy()
        lows = recent_data['Low'].values
        
        # Find local lows (valleys)
        local_lows = []
        for i in range(1, len(lows) - 1):
            if lows[i] <= lows[i-1] and lows[i] <= lows[i+1]:
                local_lows.append({
                    'price': lows[i],
                    'index': len(df) - lookback + i
                })
        
        if not local_lows:
            return []
        
        # Group equal lows
        equal_low_zones = []
        used = set()
        
        for i, low in enumerate(local_lows):
            if i in used:
                continue
            
            # Find all other lows within tolerance
            zone_members = [i]
            zone_price = low['price']
            zone_indices = [low['index']]
            
            for j, other_low in enumerate(local_lows):
                if i != j and j not in used:
                    if other_low.get('price', 0):
                        diff_pct = abs(other_low['price'] - zone_price) / zone_price * 100
                        if diff_pct <= self.tolerance_pct:
                            zone_members.append(j)
                            zone_indices.append(other_low['index'])
                            used.add(j)
            
            # If 2+ hourly lows within tolerance = equal low level
            if len(zone_members) >= 2:
                avg_price = np.mean([local_lows[m]['price'] for m in zone_members])
                level = LiquidityLevel(
                    price=avg_price,
                    type='EQUAL_LOW',
                    touches=len(zone_members),
                    first_touch_index=min(zone_indices),
                    last_touch_index=max(zone_indices),
                    strength=min(100, 50 + len(zone_members) * 15),
                    tolerance=self.tolerance_pct
                )
                equal_low_zones.append(level)
            
            used.add(i)
        
        return equal_low_zones
    
    def detect_previous_day_levels(self, df: pd.DataFrame) -> Tuple[Optional[float], Optional[float]]:
        """
        Detect previous day's high and low
        Useful for swing trading
        """
        if len(df) < 2:
            return None, None
        
        # Group by date, if available
        try:
            if 'Date' in df.columns:
                dates = pd.to_datetime(df['Date'])
                unique_dates = dates.dt.date.unique()
                
                if len(unique_dates) >= 2:
                    prev_day_data = df[pd.to_datetime(df['Date']).dt.date == unique_dates[-2]]
                    if not prev_day_data.empty:
                        prev_day_h = prev_day_data['High'].max()
                        prev_day_l = prev_day_data['Low'].min()
                        return prev_day_h, prev_day_l
        except Exception:
            pass
        
        # Fallback: assume last 24 candles if 1-hour candles
        if len(df) >= 24:
            prev_day_data = df.iloc[-48:-24]
            if not prev_day_data.empty:
                prev_day_h = prev_day_data['High'].max()
                prev_day_l = prev_day_data['Low'].min()
                return prev_day_h, prev_day_l
        
        return None, None
    
    def detect_range_extremes(self, df: pd.DataFrame, range_bars: int = 50) -> Tuple[float, float]:
        """
        Detect range highs and lows
        Used to identify consolidation boundaries
        """
        if len(df) < range_bars:
            range_bars = len(df)
        
        recent = df.tail(range_bars)
        range_high = recent['High'].max()
        range_low = recent['Low'].min()
        
        return range_high, range_low
    
    def analyze(self, df: pd.DataFrame) -> Dict:
        """
        Complete liquidity analysis
        
        Returns:
            Dict with all detected liquidity levels
        """
        self.liquidity_levels = []
        
        # Detect different types of liquidity
        equal_highs = self.detect_equal_highs(df, lookback=50)
        equal_lows = self.detect_equal_lows(df, lookback=50)
        
        prev_day_h, prev_day_l = self.detect_previous_day_levels(df)
        range_h, range_l = self.detect_range_extremes(df, range_bars=50)
        
        # Add to levels list
        self.liquidity_levels.extend(equal_highs)
        self.liquidity_levels.extend(equal_lows)
        
        # Add previous day levels
        if prev_day_h:
            level = LiquidityLevel(
                price=prev_day_h,
                type='PREV_DAY_HIGH',
                touches=1,
                first_touch_index=len(df)-1,
                last_touch_index=len(df)-1,
                strength=60,
                tolerance=self.tolerance_pct
            )
            self.liquidity_levels.append(level)
        
        if prev_day_l:
            level = LiquidityLevel(
                price=prev_day_l,
                type='PREV_DAY_LOW',
                touches=1,
                first_touch_index=len(df)-1,
                last_touch_index=len(df)-1,
                strength=60,
                tolerance=self.tolerance_pct
            )
            self.liquidity_levels.append(level)
        
        # Add range extremes
        level = LiquidityLevel(
            price=range_h,
            type='RANGE_HIGH',
            touches=1,
            first_touch_index=0,
            last_touch_index=len(df)-1,
            strength=40,
            tolerance=self.tolerance_pct
        )
        self.liquidity_levels.append(level)
        
        level = LiquidityLevel(
            price=range_l,
            type='RANGE_LOW',
            touches=1,
            first_touch_index=0,
            last_touch_index=len(df)-1,
            strength=40,
            tolerance=self.tolerance_pct
        )
        self.liquidity_levels.append(level)
        
        return {
            'liquidity_levels': self.liquidity_levels,
            'total_liquidity_zones': len(self.liquidity_levels),
            'highest_strength': max([lvl.strength for lvl in self.liquidity_levels]) if self.liquidity_levels else 0,
        }
    
    def find_nearest_liquidity_above(self, price: float) -> Optional[LiquidityLevel]:
        """Find nearest liquidity level above current price"""
        above_levels = [lvl for lvl in self.liquidity_levels if lvl.price > price]
        if not above_levels:
            return None
        return min(above_levels, key=lambda x: x.price - price)
    
    def find_nearest_liquidity_below(self, price: float) -> Optional[LiquidityLevel]:
        """Find nearest liquidity level below current price"""
        below_levels = [lvl for lvl in self.liquidity_levels if lvl.price < price]
        if not below_levels:
            return None
        return max(below_levels, key=lambda x: price - x.price)
