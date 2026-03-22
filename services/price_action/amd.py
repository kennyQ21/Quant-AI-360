"""
AMD MODEL - ACCUMULATION, MANIPULATION, DISTRIBUTION
Three-phase market structure model
Smart money accumulates → fakes out retail → distributes on the real move
"""
import pandas as pd
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AMDPhase(Enum):
    """Three phases of price movement"""
    ACCUMULATION = "ACCUMULATION"
    MANIPULATION = "MANIPULATION"
    DISTRIBUTION = "DISTRIBUTION"
    NONE = "NONE"


@dataclass
class AMDSetup:
    """Complete AMD model setup"""
    phase: AMDPhase
    accumulation_start: Optional[int] = None
    accumulation_end: Optional[int] = None
    manipulation_candle: Optional[int] = None
    fake_breakout_direction: Optional[str] = None  # 'UP' or 'DOWN'
    distribution_start: Optional[int] = None
    score: int = 0  # 0-100 quality score


class AMDDetector:
    """
    AMD Model Detection
    
    Accumulation: Sideways range, declining volume, tight ATR
    Manipulation: False breakout with volume spike (stop hunt)
    Distribution: Strong move opposite to fake breakout
    
    This is the #1 pattern before major moves
    """
    
    def __init__(self, atr_period: int = 14):
        self.atr_period = atr_period
        self.current_setup: Optional[AMDSetup] = None
    
    def detect_accumulation(self, df: pd.DataFrame, min_bars: int = 15) -> Optional[Tuple[int, int, int]]:
        """
        Detect accumulation phase
        
        Returns:
            (start_index, end_index, quality_score) or None
        """
        if len(df) < min_bars + 10:
            return None
        
        # Check different lookback periods
        for lookback in [15, 20, 25, 30, 40]:
            if len(df) < lookback + 10:
                continue
            
            recent = df.tail(lookback).copy()
            
            # Check 1: Range is tight
            high = recent['High'].max()
            low = recent['Low'].min()
            range_pct = ((high - low) / low) * 100
            
            if range_pct > 10:  # Too wide
                continue
            
            # Check 2: Volume declining
            recent_volume = recent['Volume'].tail(5).mean()
            old_volume = recent['Volume'].head(5).mean()
            
            if recent_volume >= old_volume:  # Volume not declining
                continue
            
            # Check 3: ATR is low
            high_20 = df['High'].tail(20).max()
            low_20 = df['Low'].tail(20).min()
            atr_recent = (high_20 - low_20) / 2
            
            high_all = df['High'].tail(50).max()
            low_all = df['Low'].tail(50).min()
            atr_all = (high_all - low_all) / 2
            
            if atr_recent >= atr_all * 0.5:  # ATR not low enough
                continue
            
            # All checks passed - accumulation detected
            start = len(df) - lookback
            end = len(df) - 1
            quality = min(100, int(40 + (range_pct < 5) * 30 + (recent_volume < old_volume * 0.5) * 30))
            
            return (start, end, quality)
        
        return None
    
    def detect_manipulation(self, df: pd.DataFrame, accumulation_low: float, 
                           accumulation_high: float) -> Optional[Dict]:
        """
        Detect manipulation candle
        False breakout with volume spike
        
        Returns:
            Dict with manipulation details or None
        """
        if len(df) < 1:
            return None
        
        recent_candles = df.tail(5)
        avg_volume_20 = df['Volume'].tail(20).mean()
        
        for i, (idx, row) in enumerate(recent_candles.iterrows()):
            close = row['Close']
            high = row['High']
            low = row['Low']
            volume = row['Volume']
            
            # Check manipulation criteria
            # Breakout up then close back in range
            if high > accumulation_high and close <= accumulation_high:
                if volume >= avg_volume_20 * 1.5:  # Volume spike
                    return {
                        'index': len(df) - 5 + i,
                        'direction': 'UP',
                        'volume_spike': volume / avg_volume_20,
                        'high': high,
                        'close': close,
                        'score': min(100, int(50 + (volume / avg_volume_20 - 1) * 30))
                    }
            
            # Breakout down then close back in range
            elif low < accumulation_low and close >= accumulation_low:
                if volume >= avg_volume_20 * 1.5:
                    return {
                        'index': len(df) - 5 + i,
                        'direction': 'DOWN',
                        'volume_spike': volume / avg_volume_20,
                        'low': low,
                        'close': close,
                        'score': min(100, int(50 + (volume / avg_volume_20 - 1) * 30))
                    }
        
        return None
    
    def detect_distribution(self, df: pd.DataFrame, manipulation_direction: str,
                           accumulation_low: float, accumulation_high: float) -> Optional[Dict]:
        """
        Detect distribution phase
        Strong move opposite to fake breakout
        """
        if len(df) < 3:
            return None
        
        recent = df.tail(3)
        closes = recent['Close'].values
        volumes = recent['Volume'].values
        avg_volume_20 = df['Volume'].tail(20).mean()
        
        # After fake breakup, distribution should be DOWN
        if manipulation_direction == 'UP':
            lower_closes = sum(1 for i in range(1, len(closes)) if closes[i] < closes[i-1])
            if lower_closes >= 2:  # Price moving down
                high_volume = sum(1 for v in volumes if v >= avg_volume_20 * 1.2)
                if high_volume >= 2:
                    return {
                        'distribution_direction': 'DOWN',
                        'momentum': 'STRONG',
                        'score': 80
                    }
        
        # After fake breakdown, distribution should be UP
        else:
            higher_closes = sum(1 for i in range(1, len(closes)) if closes[i] > closes[i-1])
            if higher_closes >= 2:
                high_volume = sum(1 for v in volumes if v >= avg_volume_20 * 1.2)
                if high_volume >= 2:
                    return {
                        'distribution_direction': 'UP',
                        'momentum': 'STRONG',
                        'score': 80
                    }
        
        return None
    
    def analyze(self, df: pd.DataFrame) -> Dict:
        """
        Complete AMD analysis
        
        Returns:
            Dict with phase detection and setup quality
        """
        result = {
            'phase': 'NONE',
            'accumulation': None,
            'manipulation': None,
            'distribution': None,
            'setup_quality': 0,
            'setup_name': 'No Setup',
        }
        
        # Check for accumulation
        acc = self.detect_accumulation(df)
        if acc:
            result['accumulation'] = {
                'start': acc[0],
                'end': acc[1],
                'score': acc[2]
            }
            result['phase'] = 'ACCUMULATION'
            
            # If accumulation found, check for manipulation
            acc_high = df['High'].iloc[acc[0]:acc[1]+1].max()
            acc_low = df['Low'].iloc[acc[0]:acc[1]+1].min()
            
            manip = self.detect_manipulation(df, acc_low, acc_high)
            if manip:
                result['manipulation'] = manip
                result['phase'] = 'MANIPULATION'
                
                # Check for distribution after manipulation
                dist = self.detect_distribution(df, manip['direction'], acc_low, acc_high)
                if dist:
                    result['distribution'] = dist
                    result['phase'] = 'DISTRIBUTION'
                    result['setup_quality'] = min(100, acc[2] + manip['score'] - 30)
                    result['setup_name'] = f"AMD FULL - Fake {manip['direction']}"
        
        return result
