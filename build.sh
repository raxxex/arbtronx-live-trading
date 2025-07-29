#!/bin/bash
# Build script for Render deployment

echo "🚀 Starting ARBTRONX build process..."

# Upgrade build tools first
echo "📦 Upgrading build tools..."
pip install --upgrade pip setuptools wheel

# Install build dependencies first
echo "📦 Installing build dependencies..."
pip install setuptools>=65.0.0 wheel>=0.38.0

# Install packages with pre-compiled wheels only
echo "📦 Installing dependencies with pre-compiled wheels..."
pip install --only-binary=all --no-cache-dir fastapi uvicorn gunicorn python-dotenv pydantic aiohttp websockets ccxt pandas numpy loguru python-dateutil

echo "✅ Build complete!"
