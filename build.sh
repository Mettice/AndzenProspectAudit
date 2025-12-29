#!/bin/bash
# Build script for Railway deployment
# Installs Python dependencies and Playwright browsers

set -e

echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo "🌐 Installing Playwright browsers..."
playwright install chromium
playwright install-deps chromium

echo "✅ Build complete!"

