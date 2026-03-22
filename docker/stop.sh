#!/bin/bash

# Stop all services
# Usage: ./docker/stop.sh

set -e

echo "🛑 Stopping Quant AI Trading System..."
echo "====================================="

# Change to project root
cd "$(dirname "$0")/.."

# Stop services
docker-compose -f docker/docker-compose.yml down

echo ""
echo "✅ Services stopped!"
