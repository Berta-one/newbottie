#!/usr/bin/env python3
"""
Setup script for Render environment variables
This script helps you configure the bot for Render deployment
"""

import os
import json

def check_current_setup():
    """Check current environment setup"""
    print("🔍 CURRENT ENVIRONMENT STATUS")
    print("=" * 40)
    
    # Check if running on Render
    is_render = "RENDER" in os.environ
    print(f"Platform: {'Render' if is_render else 'Local/Other'}")
    
    # Check API keys
    api_key = os.getenv('BINANCE_API_KEY', '')
    api_secret = os.getenv('BINANCE_API_SECRET', '')
    finnhub_key = os.getenv('FINNHUB_API_KEY', '')
    
    print(f"Binance API Key: {'✅ SET' if api_key and 'your_' not in api_key else '❌ NOT SET'}")
    print(f"Binance Secret: {'✅ SET' if api_secret and 'your_' not in api_secret else '❌ NOT SET'}")
    print(f"Finnhub Key: {'✅ SET' if finnhub_key and 'your_' not in finnhub_key else '❌ NOT SET'}")
    
    return is_render, bool(api_key and 'your_' not in api_key)

def generate_render_env_vars():
    """Generate environment variables for Render deployment"""
    print("\n📝 RENDER ENVIRONMENT VARIABLES")
    print("=" * 40)
    print("Copy these to your Render service environment variables:")
    print()
    
    env_vars = {
        # Core API Keys (YOU NEED TO REPLACE THESE)
        "BINANCE_API_KEY": "your_actual_binance_api_key_here",
        "BINANCE_API_SECRET": "your_actual_binance_secret_here", 
        "FINNHUB_API_KEY": "your_actual_finnhub_key_here",
        
        # Trading Configuration
        "TRADE_ENABLED": "1",
        "DEMO_MODE": "0",
        "EXECUTION_INTERVAL_S": "20",
        "TRADE_QUOTE_PER_ORDER": "100",
        "MAX_SPEND_PER_SYMBOL": "1000",
        "SELL_FRACTION": "0.5",
        "MAX_OPEN_POSITIONS": "10",
        
        # Sentiment Analysis
        "SENTIMENT_ENABLED": "1",
        "SENTIMENT_WINDOW_S": "900",
        "SENTIMENT_ASSETS": "BTC,ETH,BNB,SOL,ADA,XRP,DOGE,AVAX,DOT,MATIC",
        
        # Dashboard & Security
        "DASHBOARD_PASSWORD": "bottie2024",
        "JWT_SECRET_KEY": "your_secure_random_jwt_secret_here",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "60",
        
        # Logging
        "LOG_LEVEL": "INFO",
        
        # Render-specific
        "PORT": "8000",
        "HOST": "0.0.0.0"
    }
    
    for key, value in env_vars.items():
        print(f"{key}={value}")
    
    return env_vars

def create_local_env_file():
    """Create local .env file with proper structure"""
    env_content = """# Bottie Trading Bot Configuration for Render
# IMPORTANT: Replace placeholder values with your actual API keys

# === REQUIRED API KEYS ===
# Get from: https://www.binance.com/en/my/settings/api-management
BINANCE_API_KEY=your_actual_binance_api_key_here
BINANCE_API_SECRET=your_actual_binance_secret_here

# Get from: https://finnhub.io/register  
FINNHUB_API_KEY=your_actual_finnhub_key_here

# === TRADING CONFIGURATION ===
TRADE_ENABLED=1
DEMO_MODE=0
EXECUTION_INTERVAL_S=20
TRADE_QUOTE_PER_ORDER=100
MAX_SPEND_PER_SYMBOL=1000
SELL_FRACTION=0.5
MAX_OPEN_POSITIONS=10

# === SENTIMENT ANALYSIS ===
SENTIMENT_ENABLED=1
SENTIMENT_WINDOW_S=900
SENTIMENT_ASSETS=BTC,ETH,BNB,SOL,ADA,XRP,DOGE,AVAX,DOT,MATIC

# === DASHBOARD & SECURITY ===
DASHBOARD_PASSWORD=bottie2024
JWT_SECRET_KEY=your_secure_random_jwt_secret_here
ACCESS_TOKEN_EXPIRE_MINUTES=60

# === LOGGING ===
LOG_LEVEL=INFO

# === RENDER DEPLOYMENT ===
PORT=8000
HOST=0.0.0.0
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("\n✅ Updated .env file with proper structure")

def test_api_connection():
    """Test API connection with current keys"""
    print("\n🔌 TESTING API CONNECTION")
    print("=" * 40)
    
    try:
        import ccxt
        
        api_key = os.getenv('BINANCE_API_KEY', '')
        api_secret = os.getenv('BINANCE_API_SECRET', '')
        
        if not api_key or 'your_' in api_key:
            print("❌ Cannot test - no valid API keys set")
            return False
        
        # Test connection
        exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
            'sandbox': False,
            'enableRateLimit': True,
        })
        
        # Try to get account info (minimal API call)
        try:
            balance = exchange.fetch_balance()
            print("✅ API Connection: SUCCESS")
            print(f"✅ Account Access: Working")
            return True
        except Exception as e:
            if "geographic" in str(e).lower() or "restricted location" in str(e).lower():
                print("⚠️ Geographic restriction detected")
                print("💡 This should work fine on Render (Frankfurt)")
                return "geographic"
            else:
                print(f"❌ API Error: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def generate_render_deployment_guide():
    """Generate deployment guide for Render"""
    print("\n🚀 RENDER DEPLOYMENT GUIDE")
    print("=" * 40)
    
    steps = [
        "1. 🔑 Get your API keys:",
        "   • Binance: https://www.binance.com/en/my/settings/api-management",
        "   • Finnhub: https://finnhub.io/register",
        "",
        "2. 🌐 In your Render dashboard:",
        "   • Go to your service settings",
        "   • Navigate to 'Environment' tab",
        "   • Add the environment variables shown above",
        "   • Replace placeholder values with real API keys",
        "",
        "3. 🔄 Deploy:",
        "   • Commit your code changes to GitHub",
        "   • Render will auto-deploy",
        "   • Check logs for successful startup",
        "",
        "4. ✅ Verify:",
        "   • Visit your-app.onrender.com/health", 
        "   • Check that all features show as enabled",
        "   • Monitor /status endpoint for live data",
        "",
        "5. 📊 Monitor:",
        "   • Dashboard: your-app.onrender.com",
        "   • API status: your-app.onrender.com/health",
        "   • Trading signals: your-app.onrender.com/signals"
    ]
    
    for step in steps:
        print(step)

def main():
    """Main setup function"""
    print("🤖 BOTTIE RENDER SETUP ASSISTANT")
    print("=" * 50)
    
    # Check current setup
    is_render, has_keys = check_current_setup()
    
    # Create proper .env file
    create_local_env_file()
    
    # Generate Render environment variables
    generate_render_env_vars()
    
    # Test connection if keys are available
    if has_keys:
        test_result = test_api_connection()
        if test_result == "geographic":
            print("\n💡 Geographic restriction is normal for this location.")
            print("   Your bot will work perfectly on Render (Frankfurt).")
    
    # Generate deployment guide
    generate_render_deployment_guide()
    
    print("\n" + "=" * 50)
    print("🎯 NEXT STEPS:")
    print("1. Add your real API keys to the .env file")
    print("2. Copy environment variables to Render dashboard")
    print("3. Deploy to Render")
    print("4. Your bot will be fully operational!")
    print("\n✅ Setup assistant complete!")

if __name__ == "__main__":
    main()