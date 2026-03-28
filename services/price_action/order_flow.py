"""
ORDER FLOW & MARKET STRUCTURE ANALYZER
Foundation of the price action system
Tracks structure, detects BOS (Break of Structure) and CHoCH (Change of Character)
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class StructurePoint:
    """Represents a swing high or swing low"""
    price: float
    index: int
    type: str  # 'SH' (swing high) or 'SL' (swing low)
    date: Optional[str] = None


@dataclass
class MarketStructure:
    """Current market structure state"""
    trend: str  # 'UPTREND', 'DOWNTREND', 'RANGE'
    structure_quality: int  # Number of consecutive confirming points (0-5+)
    last_bos: Optional[StructurePoint] = None
    last_choch: Optional[StructurePoint] = None
    is_fresh_choch: bool = False  # True if CHoCH just happened


class OrderFlowAnalyzer:
    """
    Order Flow and Market Structure Analysis
    
    Key Concepts:
    - Swing High/Low: Price extremes detected by ATR-based algorithm
    - Structure: Sequence of highs and lows (uptrend: HH + HL, downtrend: LH + LL)
    - BOS (Break of Structure): Price closes beyond most recent structure point
    - CHoCH (Change of Character): First BOS against prevailing trend
    - Structure Quality: How many consecutive structure points confirm the trend
    """
    
    def __init__(self, atr_length: int = 14, swing_tolerance: float = 0.3):
        """
        Args:
            atr_length: Period for ATR calculation
            swing_tolerance: Distance in % for grouping highs/lows as same level
        """
        self.atr_length = atr_length
        self.swing_tolerance = swing_tolerance
        
        self.structure_points: List[StructurePoint] = []
        self.bos_history: List[StructurePoint] = []
        self.choch_history: List[StructurePoint] = []
        self.current_structure = MarketStructure(
            trend='RANGE',
            structure_quality=0
        )
    
    def detect_swing_highs(self, df: pd.DataFrame, lookback: int = 5) -> List[StructurePoint]:
        """
        Detect swing highs using local maxima
        Swing high: high that is higher than <lookback> candles before and after
        """
        if len(df) < lookback * 2:
            return []
        
        swings = []
        highs = np.asarray(df['High'])
        for i in range(lookback, len(df) - lookback):
            current_high = float(highs[i])
            
            # Check if it's a local maximum
            is_swing_high = True
            
            # Check previous lookback candles
            for j in range(i - lookback, i):
                if float(highs[j]) >= current_high:
                    is_swing_high = False
                    break
            
            # Check next lookback candles
            if is_swing_high:
                for j in range(i + 1, i + lookback + 1):
                    if float(highs[j]) >= current_high:
                        is_swing_high = False
                        break
            
            if is_swing_high:
                swings.append(StructurePoint(
                    price=current_high,
                    index=i,
                    type='SH',
                    date=str(df.index[i]) if hasattr(df.index[i], '__str__') else None
                ))
        
        return swings
    
    def detect_swing_lows(self, df: pd.DataFrame, lookback: int = 5) -> List[StructurePoint]:
        """
        Detect swing lows using local minima
        Swing low: low that is lower than <lookback> candles before and after
        """
        if len(df) < lookback * 2:
            return []
        
        swings = []
        lows = np.asarray(df['Low'])
        for i in range(lookback, len(df) - lookback):
            current_low = float(lows[i])
            
            # Check if it's a local minimum
            is_swing_low = True
            
            # Check previous lookback candles
            for j in range(i - lookback, i):
                if float(lows[j]) <= current_low:
                    is_swing_low = False
                    break
            
            # Check next lookback candles
            if is_swing_low:
                for j in range(i + 1, i + lookback + 1):
                    if float(lows[j]) <= current_low:
                        is_swing_low = False
                        break
            
            if is_swing_low:
                swings.append(StructurePoint(
                    price=current_low,
                    index=i,
                    type='SL',
                    date=str(df.index[i]) if hasattr(df.index[i], '__str__') else None
                ))
        
        return swings
    
    def get_structure_sequence(self) -> List[StructurePoint]:
        """Get all structure points in chronological order"""
        all_points = self.structure_points.copy()
        all_points.sort(key=lambda x: x.index)
        return all_points
    
    def classify_structure(self, sequence: List[StructurePoint]) -> Tuple[str, int]:
        """
        Classify current market structure
        
        Returns:
            (trend, quality_score)
            trend: 'UPTREND', 'DOWNTREND', 'RANGE'
            quality_score: Number of consecutive confirming points (0-5+)
        """
        if len(sequence) < 4:
            return 'RANGE', 0
        
        # Take last 4 structure points
        recent = sequence[-4:]
        
        # Sort by index to ensure chronological order
        recent.sort(key=lambda x: x.index)
        
        # Extract pattern
        last_sh = None  # Most recent swing high
        last_sl = None  # Most recent swing low
        prev_sh = None
        prev_sl = None
        
        for point in recent:
            if point.type == 'SH':
                prev_sh = last_sh
                last_sh = point
            else:  # SL
                prev_sl = last_sl
                last_sl = point
        
        # Classify structure
        if last_sh and prev_sh and last_sl and prev_sl:
            higher_high = last_sh.price > prev_sh.price
            higher_low = last_sl.price > prev_sl.price
            lower_high = last_sh.price < prev_sh.price
            lower_low = last_sl.price < prev_sl.price
            
            if higher_high and higher_low:
                # Count consecutive HH + HL pattern
                quality = self._count_uptrend_quality(sequence)
                return 'UPTREND', quality
            
            elif lower_high and lower_low:
                # Count consecutive LH + LL pattern
                quality = self._count_downtrend_quality(sequence)
                return 'DOWNTREND', quality
            
            else:
                return 'RANGE', 1
        
        return 'RANGE', 0
    
    def _count_uptrend_quality(self, sequence: List[StructurePoint]) -> int:
        """Count how many consecutive HH + HL points confirm uptrend"""
        if len(sequence) < 4:
            return 0
        
        count = 0
        recent = sequence[-4:]
        recent.sort(key=lambda x: x.index)
        
        for i in range(2, len(recent)):
            current_point = recent[i]
            prev_point = recent[i-2]
            
            if current_point.type == prev_point.type:  # Same type (SH or SL)
                if current_point.price > prev_point.price:
                    count += 1
        
        return count
    
    def _count_downtrend_quality(self, sequence: List[StructurePoint]) -> int:
        """Count how many consecutive LH + LL points confirm downtrend"""
        if len(sequence) < 4:
            return 0
        
        count = 0
        recent = sequence[-4:]
        recent.sort(key=lambda x: x.index)
        
        for i in range(2, len(recent)):
            current_point = recent[i]
            prev_point = recent[i-2]
            
            if current_point.type == prev_point.type:  # Same type
                if current_point.price < prev_point.price:
                    count += 1
        
        return count
    
    def detect_bos(self, price: float, close: float, structure_sequence: List[StructurePoint], 
                   trend: str, open_price: float = None) -> Optional[StructurePoint]:
        """
        Detect Break of Structure - Strict Prop-Desk Level
        
        - In uptrend: price strictly closes above most recent swing high with a bullish candle
        - In downtrend: price strictly closes below most recent swing low with a bearish candle
        
        Returns:
            StructurePoint of the BOS, or None if no BOS
        """
        if not structure_sequence:
            return None
            
        is_bullish_candle = open_price is not None and close > open_price
        is_bearish_candle = open_price is not None and close < open_price
        
        # Get most recent structure point of the relevant type
        if trend == 'UPTREND':
            # In uptrend, look for strong close above most recent SH
            for point in reversed(structure_sequence):
                if point.type == 'SH':
                    if close > point.price and (open_price is None or is_bullish_candle):
                        return point  # Strong BOS detected
                    else:
                        return None
        
        elif trend == 'DOWNTREND':
            # In downtrend, look for strong close below most recent SL
            for point in reversed(structure_sequence):
                if point.type == 'SL':
                    if close < point.price and (open_price is None or is_bearish_candle):
                        return point  # Strong BOS detected
                        return None
        
        return None
    
    def detect_choch(self, close: float, structure_sequence: List[StructurePoint],
                     trend: str) -> Optional[StructurePoint]:
        """
        Detect Change of Character
        
        CHoCH is the FIRST BOS against the prevailing trend.
        - If downtrend and price closes above a swing high: bullish CHoCH
        - If uptrend and price closes below a swing low: bearish CHoCH
        
        Returns:
            StructurePoint of CHoCH point, or None
        """
        if not structure_sequence or len(structure_sequence) < 2:
            return None
        
        if trend == 'DOWNTREND':
            # Looking for bullish CHoCH: close above swing high
            for point in reversed(structure_sequence):
                if point.type == 'SH':
                    if close > point.price:
                        # This is a CHoCH only if we haven't seen one recently
                        return point
                    else:
                        return None
        
        elif trend == 'UPTREND':
            # Looking for bearish CHoCH: close below swing low
            for point in reversed(structure_sequence):
                if point.type == 'SL':
                    if close < point.price:
                        return point
                    else:
                        return None
        
        return None
    
    def analyze(self, df: pd.DataFrame) -> MarketStructure:
        """
        Complete analysis of market structure
        
        Args:
            df: DataFrame with OHLCV data
        
        Returns:
            MarketStructure object with current state
        """
        # Detect swing points
        sh_points = self.detect_swing_highs(df, lookback=5)
        sl_points = self.detect_swing_lows(df, lookback=5)
        
        # Combine and sort by index
        self.structure_points = sh_points + sl_points
        self.structure_points.sort(key=lambda x: x.index)
        
        # Get sequence
        sequence = self.get_structure_sequence()
        
        # Classify structure
        trend, quality = self.classify_structure(sequence)
        
        # Get latest candle info
        latest_close = float(np.asarray(df['Close'])[-1])
        latest_open = float(np.asarray(df['Open'])[-1])
        latest_price = float(np.asarray(df['High'])[-1])
        
        # Detect BOS
        bos = self.detect_bos(latest_price, latest_close, sequence, trend, latest_open)
        if bos:
            self.current_structure.last_bos = bos
        
        # Detect CHoCH
        choch = self.detect_choch(latest_close, sequence, trend)
        if choch and (not self.current_structure.last_choch or 
                     choch.index != self.current_structure.last_choch.index):
            self.current_structure.last_choch = choch
            self.current_structure.is_fresh_choch = True
        else:
            self.current_structure.is_fresh_choch = False
        
        # Update current structure
        if self.current_structure.trend != trend:
            self.current_structure.last_bos = None
            
        self.current_structure.trend = trend
        self.current_structure.structure_quality = quality
        
        return self.current_structure
    
    def get_market_structure_summary(self) -> Dict:
        """Get human-readable summary of market structure"""
        return {
            'trend': self.current_structure.trend,
            'structure_quality': self.current_structure.structure_quality,
            'last_bos_price': self.current_structure.last_bos.price if self.current_structure.last_bos else None,
            'last_choch_price': self.current_structure.last_choch.price if self.current_structure.last_choch else None,
            'is_fresh_choch': self.current_structure.is_fresh_choch,
            'total_structure_points': len(self.structure_points),
        }
