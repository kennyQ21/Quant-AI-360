"""
CONSOLIDATION BREAKOUT DETECTOR
Simple but powerful: tight range + breakout on volume = high probability trade
"""
import pandas as pd
from typing import Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BreakoutDetector:
    """
    Consolidation Breakout Detection
    
    Setup:
    1. Identify consolidation (tight range, 10-40 bars)
    2. Range must be <8-10% of price
    3. Volume declining during consolidation
    4. Breakout on volume 1.5x+ average
    5. Filter false breakouts with 0.5% requirement
    """
    
    def __init__(self, min_bars: int = 10, max_bars: int = 40, max_range_pct: float = 10.0):
        self.min_bars = min_bars
        self.max_bars = max_bars
        self.max_range_pct = max_range_pct
    
    def detect_consolidation(self, df: pd.DataFrame) -> Optional[Dict]:
        """
        Detect consolidation (tight sideways range)
        
        Returns:
            Dict with consolidation details or None
        """
        if len(df) < self.max_bars + 10:
            return None
        
        # Try different consolidation lengths
        for bars in range(self.min_bars, self.max_bars + 1):
            recent = df.tail(bars)
            
            # Check range tightness
            high = recent['High'].max()
            low = recent['Low'].min()
            range_pct = ((high - low) / low) * 100
            
            if range_pct > self.max_range_pct:
                continue
            
            # Check volume decline
            recent_vol = recent['Volume'].tail(3).mean()
            old_vol = recent['Volume'].head(3).mean()
            
            if recent_vol >= old_vol:  # Volume not declining
                continue
            
            # Check that most candles are inside range
            inside_count = sum(1 for idx, row in recent.iterrows() 
                             if low <= row['Close'] <= high)
            
            if inside_count < bars * 0.7:  # At least 70% inside
                continue
            
            # Consolidation found
            return {
                'high': high,
                'low': low,
                'range_pct': range_pct,
                'duration': bars,
                'volume_ratio': recent_vol / old_vol,
                'quality': min(100, 50 + (10 - range_pct) * 5 + (1 - recent_vol/old_vol) * 30)
            }
        
        return None
    
    def detect_breakout(self, df: pd.DataFrame, cons_high: float, cons_low: float) -> Optional[Dict]:
        """
        Detect breakout from consolidation
        
        Key: Must close above/below range, not just wick
        Must be significant volume
        """
        if len(df) < 1:
            return None
        
        avg_volume_20 = df['Volume'].tail(20).mean()
        
        # Check last 5 candles for breakout
        recent = df.tail(5)
        
        for idx, row in recent.iterrows():
            close = row['Close']
            high = row['High']
            low = row['Low']
            volume = row['Volume']
            
            # UPSIDE BREAKOUT
            if close > cons_high and volume >= avg_volume_20 * 1.5:
                # Requirement: close is significantly above (0.5%)
                if close >= cons_high * 1.005:
                    return {
                        'direction': 'UP',
                        'entry_price': close,
                        'stop_price': cons_low,
                        'volume_multiple': volume / avg_volume_20,
                        'breakout_strength': (close - cons_high) / cons_high * 100,
                        'candle_near_high': (close >= high * 0.98),  # Close near high = strong
                        'score': min(100, 70 + (volume / avg_volume_20 - 1.5) * 15 + (close >= high * 0.98) * 15)
                    }
            
            # DOWNSIDE BREAKOUT
            elif close < cons_low and volume >= avg_volume_20 * 1.5:
                # Requirement: close is significantly below (0.5%)
                if close <= cons_low * 0.995:
                    return {
                        'direction': 'DOWN',
                        'entry_price': close,
                        'stop_price': cons_high,
                        'volume_multiple': volume / avg_volume_20,
                        'breakout_strength': (cons_low - close) / cons_low * 100,
                        'candle_near_low': (close <= low * 1.02),
                        'score': min(100, 70 + (volume / avg_volume_20 - 1.5) * 15 + (close <= low * 1.02) * 15)
                    }
        
        return None
    
    def detect_retest(self, df: pd.DataFrame, cons_high: float, cons_low: float, 
                     breakout_direction: str) -> Optional[Dict]:
        """
        Detect retest of breakout level
        Second entry opportunity with tighter stop
        
        After breakout up, price pulls back to test old resistance (now support)
        """
        if len(df) < 3:
            return None
        
        recent = df.tail(5)
        avg_volume_20 = df['Volume'].tail(20).mean()
        
        if breakout_direction == 'UP':
            # Look for touch of cons_high from above
            for idx, row in recent.iterrows():
                low = row['Low']
                volume = row['Volume']
                
                # Retest: touches old high from above
                if low <= cons_high and volume < avg_volume_20 * 1.2:  # Low volume = weak
                    return {
                        'retest_level': cons_high,
                        'retest_type': 'SUPPORT_RETEST',
                        'new_stop': cons_low,  # Tighter stop
                        'volume_profile': 'WEAK',  # Low volume = quality retest
                        'score': 85
                    }
        
        elif breakout_direction == 'DOWN':
            # Look for touch of cons_low from below
            for idx, row in recent.iterrows():
                high = row['High']
                volume = row['Volume']
                
                # Retest: touches old low from below
                if high >= cons_low and volume < avg_volume_20 * 1.2:
                    return {
                        'retest_level': cons_low,
                        'retest_type': 'RESISTANCE_RETEST',
                        'new_stop': cons_high,
                        'volume_profile': 'WEAK',
                        'score': 85
                    }
        
        return None
    
    def analyze(self, df: pd.DataFrame) -> Dict:
        """
        Complete consolidation breakout analysis
        """
        result = {
            'phase': 'NONE',
            'consolidation': None,
            'breakout': None,
            'retest': None,
            'setup_quality': 0,
            'setup_name': 'No Setup',
        }
        
        # Detect consolidation
        cons = self.detect_consolidation(df)
        if not cons:
            return result
        
        result['consolidation'] = cons
        result['phase'] = 'CONSOLIDATION'
        result['setup_quality'] = cons['quality']
        result['setup_name'] = f"Consolidation - {cons['duration']} bars"
        
        # Check for breakout
        breakout = self.detect_breakout(df, cons['high'], cons['low'])
        if breakout:
            result['breakout'] = breakout
            result['phase'] = 'BREAKOUT_TRIGGERED'
            result['setup_quality'] = breakout['score']
            result['setup_name'] = f"Breakout {breakout['direction']}"
            
            # Check for retest
            retest = self.detect_retest(df, cons['high'], cons['low'], breakout['direction'])
            if retest:
                result['retest'] = retest
                result['setup_name'] += " + RETEST FORMING"
        
        return result
