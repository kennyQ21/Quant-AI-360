#!/bin/bash

# Start all services with Docker Compose
# Usage: ./docker/start.sh

set -e

echo "🚀 Starting Quant AI Trading System..."
echo "====================================="

# Change to project root
cd "$(dirname "$0")/.."

# Start services
docker-compose -f docker/docker-compose.yml up -d

# Wait for services to start
echo ""
echo "⏳ Waiting for services to start..."
sleep 5

# Show status
echo ""
echo "📊 Service Status:"
docker-compose -f docker/docker-compose.yml ps

echo ""
echo "✅ Services started!"
echo ""
echo "Available endpoints:"
echo "  MCP Server:  http://localhost:8000"
echo ""
echo "View logs with: docker-compose -f docker/docker-compose.yml logs -f"
