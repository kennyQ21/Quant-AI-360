"""
SMC SCANNER
Runs all 7 detectors + confluence scoring on multiple stocks
Returns top N setups ranked by confluence score
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import pandas as pd
import logging

from services.price_action import (
    OrderFlowAnalyzer,
    LiquidityDetector,
    FVGDetector,
    IFVGMonitor,
    AMDDetector,
    VCPDetector,
    BreakoutDetector
)
from services.strategy_engine.confluence import ConfluenceEngine

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ScannerResult:
    """Single stock scan result"""
    symbol: str
    current_price: float
    setup_name: str
    score: float
    direction: str
    entry: float
    stop_loss: float
    target1: float
    target2: float
    confidence: str
    components: List[str]
    notes: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


class SMCScanner:
    """
    SMC (Smart Money Concepts) Scanner
    
    Workflow:
    1. Load OHLCV data for each stock (last 200 candles)
    2. Run all 7 detectors in parallel
    3. Score with confluence engine
    4. Rank by score (75+ = high probability)
    5. Return top N setups
    """
    
    def __init__(
        self,
        symbols: List[str],
        confluence_weights: Optional[Dict] = None,
        min_score: float = 50.0,
        max_results: int = 20
    ):
        """
        symbols: List of stock symbols to scan
        confluence_weights: Custom scoring weights
        min_score: Minimum confluence score (skip below)
        max_results: Return top N setups
        """
        self.symbols = symbols
        self.min_score = min_score
        self.max_results = max_results
        
        # Initialize all detectors
        self.order_flow = OrderFlowAnalyzer()
        self.liquidity = LiquidityDetector()
        self.fvg = FVGDetector()
        self.ifvg = IFVGMonitor()
        self.amd = AMDDetector()
        self.vcp = VCPDetector()
        self.breakout = BreakoutDetector()
        self.confluence = ConfluenceEngine()
        
        logger.info(f"Initialized SMC Scanner for {len(symbols)} symbols")
    
    def run_detectors(self, df: pd.DataFrame, symbol: str) -> Dict:
        """
        Run all 7 detectors on single stock OHLCV data
        
        Returns: Dict with all detector outputs
        """
        try:
            results = {
                'symbol': symbol,
                'timestamp': df.index[-1] if len(df) > 0 else None,
                'order_flow': self.order_flow.analyze(df),
                'liquidity': self.liquidity.analyze(df),
                'fvg': self.fvg.analyze(df),
                'ifvg': self.ifvg.analyze(df),
                'amd': self.amd.analyze(df),
                'vcp': self.vcp.analyze(df),
                'breakout': self.breakout.analyze(df),
            }
            
            logger.debug(f"{symbol}: All detectors completed")
            return results
            
        except Exception as e:
            logger.error(f"{symbol}: Detector error - {str(e)}")
            return {'symbol': symbol, 'error': str(e)}
    
    def scan_stock(self, symbol: str, df: pd.DataFrame) -> Optional[ScannerResult]:
        """
        Scan single stock: run detectors + confluence scoring
        
        Returns: ScannerResult if valid setup found, None otherwise
        """
        if len(df) < 20:
            logger.warning(f"{symbol}: Insufficient data ({len(df)} candles)")
            return None
        
        try:
            # Run all detectors
            detector_output = self.run_detectors(df, symbol)
            
            if 'error' in detector_output:
                logger.warning(f"{symbol}: Error in detectors - {detector_output['error']}")
                return None
            
            # Get current price
            current_price = df['Close'].iloc[-1]
            
            # Score with confluence engine
            setup = self.confluence.score_setup(
                order_flow=detector_output.get('order_flow'),
                liquidity=detector_output.get('liquidity'),
                fvg=detector_output.get('fvg'),
                ifvg=detector_output.get('ifvg'),
                amd=detector_output.get('amd'),
                vcp=detector_output.get('vcp'),
                breakout=detector_output.get('breakout'),
                current_price=current_price
            )
            
            if not setup or setup.score < self.min_score:
                return None
            
            # Convert to scanner result
            return ScannerResult(
                symbol=symbol,
                current_price=current_price,
                setup_name=setup.signal_name,
                score=setup.score,
                direction=setup.direction,
                entry=setup.entry_price,
                stop_loss=setup.stop_loss,
                target1=setup.target1,
                target2=setup.target2,
                confidence=setup.confidence,
                components=setup.components,
                notes=setup.notes
            )
            
        except Exception as e:
            logger.error(f"{symbol}: Scan error - {str(e)}")
            return None
    
    def scan_all(self, data_loader) -> List[ScannerResult]:
        """
        Scan all symbols and return ranked results
        
        data_loader: Function that returns (symbol, df) for each symbol
        
        Returns: List of ScannerResult sorted by score (highest first)
        """
        results = []
        
        logger.info(f"Starting scan of {len(self.symbols)} symbols...")
        
        for symbol in self.symbols:
            try:
                # Load data for symbol
                df = data_loader(symbol)
                
                if df is None or len(df) == 0:
                    logger.warning(f"{symbol}: No data available")
                    continue
                
                # Scan stock
                result = self.scan_stock(symbol, df)
                
                if result:
                    results.append(result)
                    logger.info(
                        f"{symbol}: {result.setup_name} - Score: {result.score:.1f} "
                        f"({result.confidence}) - {result.direction}"
                    )
                else:
                    logger.debug(f"{symbol}: No setup found")
                
            except Exception as e:
                logger.error(f"{symbol}: Failed to scan - {str(e)}")
                continue
        
        # Sort by score (highest first)
        results_sorted = sorted(results, key=lambda x: x.score, reverse=True)
        
        # Return top N
        top_results = results_sorted[:self.max_results]
        
        logger.info(
            f"Scan complete: Found {len(results)} setups, returning top {len(top_results)}"
        )
        
        return top_results
    
    def print_results(self, results: List[ScannerResult]) -> None:
        """Pretty print scan results"""
        if not results:
            print("No setups found")
            return
        
        print("\n" + "="*120)
        print(f"{'SYMBOL':<8} {'SETUP':<20} {'SCORE':<8} {'CONF':<8} {'DIR':<6} {'ENTRY':<10} {'STOP':<10} {'TARGET':<10} {'REASON':<30}")
        print("="*120)
        
        for result in results:
            components_str = ", ".join(result.components[:2])  # First 2 components
            
            print(
                f"{result.symbol:<8} "
                f"{result.setup_name:<20} "
                f"{result.score:<8.1f} "
                f"{result.confidence:<8} "
                f"{result.direction:<6} "
                f"${result.entry:<9.2f} "
                f"${result.stop_loss:<9.2f} "
                f"${result.target1:<9.2f} "
                f"{components_str:<30}"
            )
        
        print("="*120)
        print(f"Total setups: {len(results)} | High confidence (75+): {sum(1 for r in results if r.score >= 75)}")
        print()
    
    def export_results(self, results: List[ScannerResult], filepath: str) -> None:
        """Export results to CSV"""
        if not results:
            logger.warning("No results to export")
            return
        
        df_results = pd.DataFrame([r.to_dict() for r in results])
        df_results.to_csv(filepath, index=False)
        logger.info(f"Exported {len(results)} results to {filepath}")
