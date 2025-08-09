#!/bin/bash
# Quick Setup - Auto Portfolio Monitor
# Automatically detects your API keys and starts monitoring

echo "🚀 Auto Portfolio Monitor - Quick Setup"
echo "======================================="
echo
echo "This script will:"
echo "✅ Install required packages"
echo "✅ Auto-detect your Binance API keys"
echo "✅ Scan your live positions"
echo "✅ Monitor ALL relevant trading pairs via WebSocket"
echo "✅ Show real-time portfolio updates"
echo

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️ $1${NC}"; }

# Check Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required"
    exit 1
fi
print_status "Python 3 found"

# Install packages
print_info "Installing required packages..."
pip3 install --upgrade pip --quiet
pip3 install ccxt websockets asyncio pandas numpy --quiet

if [ $? -eq 0 ]; then
    print_status "Packages installed successfully"
else
    print_error "Package installation failed"
    exit 1
fi

# Check for API keys in environment
print_info "Checking for Binance API credentials..."

API_KEY_FOUND=false
SECRET_FOUND=false

# Check common environment variable names
for var in BINANCE_API_KEY BINANCE_KEY API_KEY BINANCE_ACCESS_KEY; do
    if [ ! -z "${!var}" ]; then
        API_KEY_FOUND=true
        print_status "Found API key in $var"
        break
    fi
done

for var in BINANCE_SECRET BINANCE_SECRET_KEY API_SECRET BINANCE_API_SECRET; do
    if [ ! -z "${!var}" ]; then
        SECRET_FOUND=true
        print_status "Found secret in $var"
        break
    fi
done

# Check for config files
if [ "$API_KEY_FOUND" = false ] || [ "$SECRET_FOUND" = false ]; then
    print_info "Checking for configuration files..."
    
    for file in .env config.json binance.json secrets.json .secrets; do
        if [ -f "$file" ]; then
            print_status "Found config file: $file"
            break
        fi
    done
fi

if [ "$API_KEY_FOUND" = false ] || [ "$SECRET_FOUND" = false ]; then
    print_warning "API credentials not found in environment variables"
    print_info "The monitor will attempt to find them in config files"
    print_info "Make sure you have your Binance API key and secret available"
fi

echo
print_info "Starting Auto Portfolio Monitor..."
echo

# Run the monitor
python3 auto_portfolio_monitor.py

echo
print_info "Monitor stopped. Check auto_portfolio_monitor.log for details."