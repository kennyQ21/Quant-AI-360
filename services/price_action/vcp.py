"""
VCP - VOLATILITY CONTRACTION PATTERN
Tight corrections after uptrend = exhaustion = explosive breakout
Professional pattern used by institutional traders
"""
import pandas as pd
from typing import Dict, Optional, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VCPDetector:
    """
    VCP Pattern Detection
    
    Setup:
    1. Stock in uptrend (above SMA50 > SMA150)
    2. Creates multiple corrections (pullbacks)
    3. Each correction smaller than previous (price AND volume)
    4. Final correction very tight and quiet
    5. Breakout above highest correction high on volume
    
    This is a 3-5 week pattern, explosive breakout
    """
    
    def __init__(self, lookback_bars: int = 80):
        self.lookback_bars = lookback_bars
    
    def is_in_uptrend(self, df: pd.DataFrame) -> bool:
        """Check if stock is in overall uptrend"""
        if len(df) < 50:
            return False
        
        sma_50 = df['Close'].rolling(50).mean().iloc[-1]
        sma_150 = df['Close'].rolling(150).mean().iloc[-1]
        current_price = df['Close'].iloc[-1]
        
        return current_price > sma_50 > sma_150
    
    def detect_correction_swings(self, df: pd.DataFrame) -> List[Dict]:
        """
        Detect correction swings (H-L moves)
        Returns list of corrections with size and volume info
        """
        if len(df) < 20:
            return []
        
        recent = df.tail(self.lookback_bars).copy()
        corrections = []
        
        i = 0
        while i < len(recent) - 5:
            # Find high
            high_idx = recent['High'].iloc[i:i+20].idxmax() if i + 20 <= len(recent) else recent['High'].iloc[i:].idxmax()
            high_price = recent.loc[high_idx, 'High']
            high_pos = recent.index.get_loc(high_idx)
            
            # Find low after high
            if high_pos + 5 < len(recent):
                low_idx = recent['Low'].iloc[high_pos:high_pos+20].idxmin() if high_pos + 20 <= len(recent) else recent['Low'].iloc[high_pos:].idxmin()
                low_price = recent.loc[low_idx, 'Low']
                low_pos = recent.index.get_loc(low_idx)
                
                # Calculate correction
                correction_pct = ((high_price - low_price) / low_price) * 100
                
                # Get volume
                correction_volume = recent.iloc[high_pos:low_pos+1]['Volume'].mean()
                
                corrections.append({
                    'high': high_price,
                    'low': low_price,
                    'correction_pct': correction_pct,
                    'volume': correction_volume,
                    'index': low_pos
                })
                
                i = low_pos + 1
            else:
                break
        
        return corrections
    
    def validate_vcp(self, corrections: List[Dict]) -> Optional[Dict]:
        """
        Validate if corrections form VCP pattern
        Each should be smaller than previous, in both size and volume
        """
        if len(corrections) < 2:
            return None
        
        # Need at least 2 progressively smaller corrections
        valid = True
        for i in range(1, len(corrections)):
            curr_pct = corrections[i]['correction_pct']
            prev_pct = corrections[i-1]['correction_pct']
            
            # Current correction must be smaller
            if curr_pct >= prev_pct * 0.95:  # Allow 5% tolerance
                valid = False
                break
            
            # Volume should also decline
            curr_vol = corrections[i]['volume']
            prev_vol = corrections[i-1]['volume']
            if curr_vol > prev_vol * 1.1:  # Allow 10% tolerance
                valid = False
                break
        
        if not valid:
            return None
        
        # Good VCP pattern found
        first_correction = corrections[0]['correction_pct']
        last_correction = corrections[-1]['correction_pct']
        
        # Depth should be within limits
        if first_correction < 8 or first_correction > 35:
            return None
        
        # Final correction must be very tight
        if last_correction > 5:
            return None
        
        quality_score = min(100,
            50 +  # Base
            (first_correction < 20) * 20 +  # Tight base
            (last_correction < 3) * 20 +  # Very tight final
            (len(corrections) >= 3) * 10  # 3+ corrections
        )
        
        return {
            'pivot_high': corrections[-1]['high'],
            'correction_count': len(corrections),
            'first_correction': first_correction,
            'last_correction': last_correction,
            'quality': quality_score,
            'base_duration': corrections[-1]['index'] - corrections[0]['index']
        }
    
    def detect_vcp_breakout(self, df: pd.DataFrame, pivot_high: float) -> Optional[Dict]:
        """
        Detect breakout above VCP pivot on volume
        """
        if len(df) < 1:
            return None
        
        recent = df.tail(5)
        avg_volume_20 = df['Volume'].tail(20).mean()
        
        for idx, row in recent.iterrows():
            close = row['Close']
            volume = row['Volume']
            
            # Breakout: close above pivot on volume
            if close > pivot_high and volume >= avg_volume_20 * 1.5:
                return {
                    'triggered': True,
                    'entry_price': close,
                    'volume_multiple': volume / avg_volume_20,
                    'score': 90
                }
        
        return None
    
    def analyze(self, df: pd.DataFrame) -> Dict:
        """
        Complete VCP analysis
        """
        result = {
            'phase': 'NONE',
            'vcp_pattern': None,
            'breakout': None,
            'setup_quality': 0,
            'setup_name': 'No VCP',
        }
        
        # Must be in uptrend first
        if not self.is_in_uptrend(df):
            return result
        
        # Detect corrections
        corrections = self.detect_correction_swings(df)
        
        # Validate VCP
        vcp = self.validate_vcp(corrections)
        if not vcp:
            return result
        
        result['phase'] = 'VCP_PATTERN'
        result['vcp_pattern'] = vcp
        result['setup_quality'] = vcp['quality']
        result['setup_name'] = f"VCP - {vcp['correction_count']} corrections"
        
        # Check for breakout
        breakout = self.detect_vcp_breakout(df, vcp['pivot_high'])
        if breakout:
            result['breakout'] = breakout
            result['phase'] = 'VCP_BREAKOUT'
            result['setup_quality'] = min(100, vcp['quality'] + 10)
            result['setup_name'] = "VCP BREAKOUT TRIGGERED"
        
        return result
