#!/bin/bash

# Build and run using Docker Compose
# Usage: ./docker/build.sh

set -e

echo "🐳 Building Quant AI Trading System with Docker..."
echo "=================================================="

# Change to project root
cd "$(dirname "$0")/.."

# Build images
echo "📦 Building Docker images..."
docker-compose -f docker/docker-compose.yml build

echo ""
echo "✅ Docker images built successfully!"
echo ""
echo "Next commands:"
echo "  Start services:     docker-compose -f docker/docker-compose.yml up -d"
echo "  View logs:          docker-compose -f docker/docker-compose.yml logs -f"
echo "  Stop services:      docker-compose -f docker/docker-compose.yml down"
echo "  Clean up:           docker-compose -f docker/docker-compose.yml down -v"
