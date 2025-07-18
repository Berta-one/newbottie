#!/bin/bash

echo "🚀 Starting Railway Crypto Trading Bot..."

# Set timezone
export TZ=UTC

# Create directories
mkdir -p logs
mkdir -p models
mkdir -p data

# Load environment if .env exists
if [ -f .env ]; then
    echo "📋 Loading .env variables"
    export $(cat .env | grep -v '#' | xargs)
fi

# Check API keys
if [ -z "$BINANCE_API_KEY" ] || [ -z "$BINANCE_API_SECRET" ]; then
    echo "⚠️ Warning: API keys not set"
    echo "Set BINANCE_API_KEY and BINANCE_API_SECRET"
fi

# Start bot
echo "🎯 Starting Railway bot..."
python railway_deployment_main.py 2>&1 | tee logs/startup.log
