#!/bin/bash
# Build script for Render deployment

echo "🚀 Starting ARBTRONX build process..."

# Upgrade pip first
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install packages with pre-compiled wheels only
echo "📦 Installing dependencies with pre-compiled wheels..."
pip install --only-binary=all --no-cache-dir -r requirements.txt

echo "✅ Build complete!"
