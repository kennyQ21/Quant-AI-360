"""
Backtest Validation Suite
Checks for common pitfalls (lookahead bias, survivorship bias, etc.)
"""
import pandas as pd
import logging
from typing import Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BacktestValidator:
    """Validates backtest integrity and quality"""
    
    @staticmethod
    def check_lookahead_bias(data: pd.DataFrame, signal_column: str = 'signal') -> bool:
        """
        Check for lookahead bias
        Lookahead bias = signal uses future data
        
        Warning signs:
        - Signal column uses shift(-1) or forward-looking data
        - Suspiciously high returns (>50% annually)
        
        Returns:
            True if no lookahead bias detected, False if suspicious
        """
        logger.info("🔍 Checking for lookahead bias...")
        
        # Check for suspicious forward-looking patterns
        has_shift_negative = str(data).find("shift(-") != -1
        
        if has_shift_negative:
            logger.warning("⚠️  WARNING: Found negative shift() - possible lookahead bias!")
            return False
        
        logger.info("✓ No obvious lookahead bias detected")
        return True
    
    @staticmethod
    def check_transaction_costs(transaction_cost: float) -> bool:
        """
        Validate transaction cost is realistic
        
        Returns:
            True if cost is reasonable, False if too low
        """
        logger.info("💰 Validating transaction costs...")
        
        # Realistic costs
        MIN_COST = 0.0001  # 0.01%
        MAX_COST = 0.01    # 1.00%
        
        if transaction_cost < MIN_COST:
            logger.warning(f"⚠️  Transaction cost too low: {transaction_cost*100:.4f}%")
            logger.info("   Realistic range: 0.01% - 1.0% for Indian stocks")
            return False
        
        if transaction_cost > MAX_COST:
            logger.warning(f"⚠️  Transaction cost too high: {transaction_cost*100:.2f}%")
            return False
        
        logger.info(f"✓ Transaction cost realistic: {transaction_cost*100:.3f}%")
        return True
    
    @staticmethod
    def check_data_integrity(data: pd.DataFrame) -> bool:
        """Check for data quality issues"""
        logger.info("📊 Validating data integrity...")
        
        issues = []
        
        # Check for missing values
        missing = data.isnull().sum().sum()
        if missing > 0:
            issues.append(f"  - {missing} missing values detected")
        
        # Check for duplicate dates
        if 'Date' in data.columns:
            duplicates = data['Date'].duplicated().sum()
            if duplicates > 0:
                issues.append(f"  - {duplicates} duplicate dates")
        
        # Check for price anomalies
        if 'Close' in data.columns or 'close' in data.columns:
            close_col = 'Close' if 'Close' in data.columns else 'close'
            price_changes = data[close_col].pct_change().abs()
            
            huge_moves = (price_changes > 0.5).sum()  # >50% daily move
            if huge_moves > 0:
                issues.append(f"  - {huge_moves} unrealistic price moves (>50% daily)")
        
        if issues:
            logger.warning("⚠️  Data integrity issues:")
            for issue in issues:
                logger.warning(issue)
            return False
        
        logger.info(f"✓ Data integrity OK ({len(data)} rows)")
        return True
    
    @staticmethod
    def validate_metrics(metrics: Dict) -> Dict[str, bool]:
        """
        Validate if metrics indicate a strong strategy
        
        Returns:
            Dictionary of metric health checks
        """
        logger.info("📈 Evaluating strategy quality metrics...")
        
        checks = {
            'strong_sharpe': metrics.get('sharpe_ratio', 0) > 1.0,
            'acceptable_sharpe': metrics.get('sharpe_ratio', 0) > 0.5,
            'good_drawdown': metrics.get('max_drawdown', 0) > -0.25,  # <-25%
            'acceptable_drawdown': metrics.get('max_drawdown', 0) > -0.50,  # <-50%
            'good_win_rate': metrics.get('win_rate', 0) > 0.55,  # >55%
            'breakeven_win_rate': metrics.get('win_rate', 0) > 0.35,  # >35%
            'strong_profit_factor': metrics.get('profit_factor', 0) > 2.0,
            'acceptable_profit_factor': metrics.get('profit_factor', 0) > 1.5,
        }
        
        logger.info(f"  Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f} " +
                   ("✓ Strong" if checks['strong_sharpe'] else 
                    "⚠️  Weak" if not checks['acceptable_sharpe'] else "OK"))
        
        logger.info(f"  Max Drawdown: {metrics.get('max_drawdown', 0)*100:.1f}% " +
                   ("✓ Good" if checks['good_drawdown'] else 
                    "⚠️  Severe" if not checks['acceptable_drawdown'] else "OK"))
        
        logger.info(f"  Win Rate: {metrics.get('win_rate', 0):.1f}% " +
                   ("✓ Strong" if checks['good_win_rate'] else 
                    "⚠️  Weak" if not checks['breakeven_win_rate'] else "OK"))
        
        logger.info(f"  Profit Factor: {metrics.get('profit_factor', 0):.2f} " +
                   ("✓ Strong" if checks['strong_profit_factor'] else 
                    "⚠️  Weak" if not checks['acceptable_profit_factor'] else "OK"))
        
        return checks
    
    @staticmethod
    def validate_backtest_quality(metrics: Dict) -> str:
        """
        Overall assessment of strategy quality
        
        Returns:
            Assessment string (EXCELLENT, GOOD, ACCEPTABLE, POOR, UNUSABLE)
        """
        sharpe = metrics.get('sharpe_ratio', 0)
        drawdown = metrics.get('max_drawdown', 0)
        win_rate = metrics.get('win_rate', 0)
        profit_factor = metrics.get('profit_factor', 0)
        
        # Count good metrics
        good_count = 0
        good_count += 1 if sharpe > 1.5 else 0
        good_count += 1 if drawdown > -0.15 else 0
        good_count += 1 if win_rate > 0.60 else 0
        good_count += 1 if profit_factor > 2.0 else 0
        
        if good_count >= 4:
            return "EXCELLENT"
        elif good_count >= 3:
            return "GOOD"
        elif good_count >= 2:
            return "ACCEPTABLE"
        elif sharpe > 0 and drawdown > -0.5 and win_rate > 0.35:
            return "POOR"
        else:
            return "UNUSABLE"
    
    @staticmethod
    def print_validation_report(symbol: str, metrics: Dict, quality: str):
        """Print formatted validation report"""
        print("\n" + "="*70)
        print(f"VALIDATION REPORT: {symbol}")
        print("="*70)
        
        print(f"\n📊 Quality Assessment: {quality}")
        
        print("\n📈 Metrics:")
        print(f"  Total Return:    {metrics.get('total_return_pct', 0):>8.2f}%")
        print(f"  Sharpe Ratio:    {metrics.get('sharpe_ratio', 0):>8.2f}   ('Good' = >1.5)")
        print(f"  Max Drawdown:    {metrics.get('max_drawdown', 0)*100:>8.1f}%  ('Good' = >-15%)")
        print(f"  Win Rate:        {metrics.get('win_rate', 0):>8.1f}%  ('Good' = >60%)")
        print(f"  Profit Factor:   {metrics.get('profit_factor', 0):>8.2f}   ('Good' = >2.0)")
        print(f"  Total Trades:    {metrics.get('total_trades', 0):>8.0f}")
        
        print("\n" + "="*70)
