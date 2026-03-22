"""
MCP Server for Market Data
Exposes services via Model Context Protocol
"""
import sys
from pathlib import Path
import logging

sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)


class MarketDataServer:
    """Market Data MCP Server"""
    
    def __init__(self):
        """Initialize the server"""
        logger.info("✓ MCP Server initialized")
    
    def run(self, host: str = "127.0.0.1", port: int = 8000):
        """Run the MCP server"""
        logger.info(f"Starting MCP Server on {host}:{port}...")


if __name__ == "__main__":
    server = MarketDataServer()
    server.run()
