"""
Technical Indicators Calculator
Prepares data for Phase 2: Calculates RSI, MACD, Bollinger Bands, ATR, etc.
"""
import pandas as pd
import numpy as np
import logging
from ta.trend import ADXIndicator, SMAIndicator, EMAIndicator, MACD
from ta.momentum import StochasticOscillator, ROCIndicator, RSIIndicator
from ta.volatility import KeltnerChannel, BollingerBands
from ta.volume import OnBalanceVolumeIndicator, MFIIndicator

logger = logging.getLogger(__name__)

def add_features_to_data(df: pd.DataFrame) -> pd.DataFrame:
    """Add all Phase 2 technical indicators to dataframe using the 'ta' library."""
    try:
        # Prevent SettingWithCopyWarning
        df = df.copy()

        # yfinance returns multi-index columns for single stocks; we must squeeze to 1D continuous Series
        close = df['Close'].squeeze()
        high = df['High'].squeeze()
        low = df['Low'].squeeze()
        volume = df['Volume'].squeeze()

        # Trend Indicators
        df['SMA_20'] = SMAIndicator(close=close, window=20).sma_indicator()
        df['SMA_50'] = SMAIndicator(close=close, window=50).sma_indicator()
        df['SMA_200'] = SMAIndicator(close=close, window=200).sma_indicator()
        df['EMA_12'] = EMAIndicator(close=close, window=12).ema_indicator()
        df['EMA_26'] = EMAIndicator(close=close, window=26).ema_indicator()
        df['ADX'] = ADXIndicator(high=high, low=low, close=close).adx()

        # Momentum Indicators
        df['RSI_14'] = RSIIndicator(close=close, window=14).rsi()
        macd = MACD(close=close)
        df['MACD'] = macd.macd()
        df['MACD_Signal'] = macd.macd_signal()
        df['MACD_Hist'] = macd.macd_diff()
        
        stoch = StochasticOscillator(high=high, low=low, close=close)
        df['Stoch_K'] = stoch.stoch()
        df['Stoch_D'] = stoch.stoch_signal()
        df['ROC'] = ROCIndicator(close=close).roc()

        # Volatility Indicators
        bb = BollingerBands(close=close)
        df['BB_Upper'] = bb.bollinger_hband()
        df['BB_Mid'] = bb.bollinger_mavg()
        df['BB_Lower'] = bb.bollinger_lband()
        
        # Calculate ATR
        from ta.volatility import AverageTrueRange
        df['ATR_14'] = AverageTrueRange(high=high, low=low, close=close, window=14).average_true_range()
        df['Std_Dev'] = close.rolling(window=20).std()
        
        kc = KeltnerChannel(high=high, low=low, close=close)
        df['KC_Upper'] = kc.keltner_channel_hband()
        df['KC_Lower'] = kc.keltner_channel_lband()

        # Volume Indicators
        df['OBV'] = OnBalanceVolumeIndicator(close=close, volume=volume).on_balance_volume()
        df['MFI'] = MFIIndicator(high=high, low=low, close=close, volume=volume).money_flow_index()
        df['Volume_MA'] = volume.rolling(window=20).mean()

        # Basic Returns
        df['Returns'] = close.pct_change()
        df['Log_Returns'] = np.log(close / close.shift(1))
        
        logger.info(f"Added all Phase 2 features to data: {df.shape}")
        return df
    
    except Exception as e:
        logger.error(f"Error adding features: {str(e)}")
        return df


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    from services.data_service.market_data import load_data
    
    # Load sample data
    data = load_data("RELIANCE.NS")
    
    if not data.empty:
        # Add features
        data_with_features = add_features_to_data(data)
        print(f"\nDataFrame shape before: {load_data('RELIANCE.NS').shape}")
        print(f"DataFrame shape after: {data_with_features.shape}")
        print(f"\nNew columns: {list(data_with_features.columns)}")
        print("\nLast 5 rows:")
        print(data_with_features.tail())
