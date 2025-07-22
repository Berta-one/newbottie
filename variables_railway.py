# =============================================================================
# RAILWAY AUTO-POPULATE ALL VARIABLES - ONE COMMAND
# =============================================================================
# This script automatically sets ALL your bot variables in Railway

Write-Host "🚂 RAILWAY AUTO-SETUP - POPULATING ALL VARIABLES..." -ForegroundColor Green
Write-Host "This will set 25+ environment variables in Railway automatically!" -ForegroundColor Yellow
Write-Host ""

# Check if Railway CLI is installed
Write-Host "📦 Checking Railway CLI..." -ForegroundColor Cyan
if (-not (Get-Command railway -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Railway CLI not found. Installing..." -ForegroundColor Red
    Write-Host "Installing Railway CLI via npm..." -ForegroundColor Yellow
    npm install -g @railway/cli
    
    if (-not (Get-Command railway -ErrorAction SilentlyContinue)) {
        Write-Host "❌ Failed to install Railway CLI. Please install manually:" -ForegroundColor Red
        Write-Host "npm install -g @railway/cli" -ForegroundColor White
        exit
    }
}

Write-Host "✅ Railway CLI found!" -ForegroundColor Green

# Login to Railway
Write-Host ""
Write-Host "🔐 Logging into Railway..." -ForegroundColor Cyan
Write-Host "(Browser will open for authentication)" -ForegroundColor Gray
railway login

# Set ALL variables in one go
Write-Host ""
Write-Host "🔧 SETTING ALL VARIABLES IN RAILWAY..." -ForegroundColor Green
Write-Host "Setting 25+ environment variables..." -ForegroundColor Yellow

# Core API Settings
railway variables set BINANCE_API_KEY="your_api_key_here"
railway variables set BINANCE_API_SECRET="your_api_secret_here"
railway variables set BINANCE_TESTNET_API_KEY="your_testnet_api_key_here"
railway variables set BINANCE_TESTNET_API_SECRET="your_testnet_api_secret_here"

# API Endpoints
railway variables set BINANCE_TESTNET_URL="https://testnet.binance.vision/api"
railway variables set BINANCE_LIVE_URL="https://api.binance.com/api"

# Core Bot Settings
railway variables set USE_TESTNET="true"
railway variables set AUTO_TRADE_ENABLED="false"
railway variables set DASHBOARD_PASSWORD="bottie"

# Scanning Configuration
railway variables set SCAN_MODE="SELECTED"
railway variables set MIN_CONFIDENCE="0.65"
railway variables set MAX_POSITIONS="3"
railway variables set SCAN_INTERVAL="300"
railway variables set MIN_QUANTUM_CONFIDENCE="0.7"
railway variables set SCAN_INTERVAL_MINUTES="30"

# Risk Management
railway variables set RISK_PERCENTAGE="0.015"
railway variables set MAX_RISK_PER_TRADE="0.015"
railway variables set RISK_LEVEL="Balanced"
railway variables set MAX_TOTAL_LOSS_PERCENT="10.0"
railway variables set MAX_TRADING_HOURS_PER_DAY="24"

# Trading Strategy
railway variables set STRATEGY="Breakout"
railway variables set TRADING_SYMBOLS="BTCUSDT,ETHUSDT,BNBUSDT"
railway variables set PORTFOLIO_VALUE="10000"
railway variables set MAX_CONCURRENT_POSITIONS="3"

# Custom Pairs
railway variables set CUSTOM_SYMBOLS="BTCUSDT,ETHUSDT,ADAUSDT,SOLUSDT,BNBUSDT"

# Advanced Settings
railway variables set FORCE_LIVE_MODE="false"
railway variables set PORT="8501"
railway variables set DEBUG_MODE="false"
railway variables set LOG_LEVEL="INFO"
railway variables set MAX_LOG_SIZE_MB="100"
railway variables set LOG_FILE_COUNT="10"

# Notification Settings (Optional)
railway variables set TELEGRAM_BOT_TOKEN="your_telegram_token"
railway variables set TELEGRAM_CHAT_ID="your_chat_id"
railway variables set EMAIL_ENABLED="false"
railway variables set EMAIL_SMTP_SERVER="smtp.gmail.com"
railway variables set EMAIL_SMTP_PORT="587"
railway variables set EMAIL_USERNAME="your_email@gmail.com"
railway variables set EMAIL_PASSWORD="your_app_password"

Write-Host ""
Write-Host "✅ ALL VARIABLES SET IN RAILWAY!" -ForegroundColor Green

# Show current variables
Write-Host ""
Write-Host "📋 CURRENT RAILWAY VARIABLES:" -ForegroundColor Yellow
railway variables

Write-Host ""
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "🎉 RAILWAY SETUP COMPLETE!" -ForegroundColor Green
Write-Host "=" * 70 -ForegroundColor Cyan

Write-Host ""
Write-Host "🔧 NEXT STEPS - UPDATE YOUR API KEYS:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Set your REAL Binance API key:" -ForegroundColor White
Write-Host "   railway variables set BINANCE_API_KEY='YOUR_ACTUAL_API_KEY'" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Set your REAL Binance API secret:" -ForegroundColor White
Write-Host "   railway variables set BINANCE_API_SECRET='YOUR_ACTUAL_SECRET'" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. (Optional) If you have testnet keys:" -ForegroundColor White
Write-Host "   railway variables set BINANCE_TESTNET_API_KEY='YOUR_TESTNET_KEY'" -ForegroundColor Cyan
Write-Host "   railway variables set BINANCE_TESTNET_API_SECRET='YOUR_TESTNET_SECRET'" -ForegroundColor Cyan
Write-Host ""
Write-Host "4. Deploy your bot:" -ForegroundColor White
Write-Host "   railway up" -ForegroundColor Cyan

Write-Host ""
Write-Host "🛡️ SAFETY SETTINGS CONFIGURED:" -ForegroundColor Green
Write-Host "✅ USE_TESTNET=true (safe start)" -ForegroundColor White
Write-Host "✅ AUTO_TRADE_ENABLED=false (manual control)" -ForegroundColor White
Write-Host "✅ Conservative risk settings (1.5% per trade)" -ForegroundColor White
Write-Host "✅ Maximum loss protection (10% total)" -ForegroundColor White
Write-Host "✅ Dashboard password protected (bottie)" -ForegroundColor White

Write-Host ""
Write-Host "🚀 DEPLOYMENT COMMAND:" -ForegroundColor Yellow
Write-Host "railway up" -ForegroundColor White

Write-Host ""
Write-Host "🎯 YOUR SOPHISTICATED BOTTIE BOT IS READY FOR RAILWAY!" -ForegroundColor Green
Write-Host "All quantum-enhanced features configured and secured! 🤖⚛️" -ForegroundColor Magenta