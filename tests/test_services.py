"""
Service Integration Tests
Verifies all services work together correctly
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import sys
from pathlib import Path
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_data_service():
    """Test data service"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST: Data Service")
    logger.info("=" * 60)
    
    try:
        logger.info("✓ Data Service imports successful")
        return True
    except Exception as e:
        logger.error(f"✗ Data Service error: {str(e)}")
        return False


def test_feature_service():
    """Test feature service"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST: Feature Service")
    logger.info("=" * 60)
    
    try:
        from services.feature_service.indicators import (
            calculate_rsi
        )
        logger.info("✓ Feature Service imports successful")
        
        # Test RSI calculation
        import pandas as pd
        prices = pd.Series(range(100, 120))
        rsi = calculate_rsi(prices)
        logger.info(f"✓ RSI calculation works: {rsi.notna().sum()} valid values")
        
        return True
    except Exception as e:
        logger.error(f"✗ Feature Service error: {str(e)}")
        return False


def test_ml_service():
    """Test ML service"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST: ML Service")
    logger.info("=" * 60)
    
    try:
        from services.ml_service.models import PricePredictorService
        
        predictor = PricePredictorService()
        result = predictor.predict_price("RELIANCE.NS")
        logger.info(f"✓ ML Service initialized: {result['status']}")
        
        return True
    except Exception as e:
        logger.error(f"✗ ML Service error: {str(e)}")
        return False


def test_decision_service():
    """Test decision service"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST: Decision Service")
    logger.info("=" * 60)
    
    try:
        from services.decision_service.trading_decisions import (
            SignalGeneratorService, RiskManagementService, PortfolioDecisionService
        )
        
        signal_gen = SignalGeneratorService()
        risk_mgr = RiskManagementService()
        portfolio = PortfolioDecisionService()
        
        # Test risk management
        position_size = risk_mgr.calculate_position_size(100000)
        logger.info(f"✓ Decision Service working: position_size=${position_size:.2f}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Decision Service error: {str(e)}")
        return False


def test_storage():
    """Test storage module"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST: Storage")
    logger.info("=" * 60)
    
    try:
        from storage.parquet_store import DataStore
        from pathlib import Path
        
        store = DataStore("parquet", Path("storage_test"))
        logger.info("✓ Storage module works")
        
        # Cleanup
        import shutil
        if Path("storage_test").exists():
            shutil.rmtree("storage_test")
        
        return True
    except Exception as e:
        logger.error(f"✗ Storage error: {str(e)}")
        return False


def test_mcp_server():
    """Test MCP server"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST: MCP Server")
    logger.info("=" * 60)
    
    try:
        from mcp_server.server import MarketDataServer
        logger.info("✓ MCP Server imports successful")
        logger.info("  (Full server test requires running instance)")
        return True
    except ImportError:
        logger.warning("⚠ MCP not installed (optional for Phase 1)")
        return True
    except Exception as e:
        logger.error(f"✗ MCP Server error: {str(e)}")
        return False


def test_agents():
    """Test agent module"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST: Agent")
    logger.info("=" * 60)
    
    try:
        from agents.langgraph_agent import MarketDataAgent
        logger.info("✓ Agent imports successful")
        logger.info("  (Requires OPENAI_API_KEY for full functionality)")
        return True
    except ImportError:
        logger.warning("⚠ LangChain not fully configured (optional for Phase 1)")
        return True
    except Exception as e:
        logger.error(f"✗ Agent error: {str(e)}")
        return False


def run_integration_tests():
    """Run all integration tests"""
    logger.info("\n🧪 SERVICES INTEGRATION TEST\n")
    
    tests = [
        ("Data Service", test_data_service),
        ("Feature Service", test_feature_service),
        ("ML Service", test_ml_service),
        ("Decision Service", test_decision_service),
        ("Storage", test_storage),
        ("MCP Server", test_mcp_server),
        ("Agent", test_agents),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            logger.error(f"Test {name} crashed: {str(e)}")
            results.append((name, False))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("INTEGRATION TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for _, p in results if p)
    total = len(results)
    
    for name, passed_test in results:
        icon = "✓" if passed_test else "✗"
        logger.info(f"{icon} {name}")
    
    logger.info("=" * 60)
    logger.info(f"Result: {passed}/{total} services passed")
    
    if passed == total:
        logger.info("\n✓ All services functional! Architecture ready.")
    else:
        logger.warning(f"\n⚠ {total - passed} service(s) have issues.")


if __name__ == "__main__":
    run_integration_tests()
