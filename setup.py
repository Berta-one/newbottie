#!/usr/bin/env python3
# setup.py - Quick Setup Script

import os
import subprocess
import sys


def install_requirements():
    """Install required packages"""
    print("📦 Installing requirements...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
        )
        print("✅ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing requirements: {e}")
        return False


def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    directories = ["logs"]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created {directory}/")


def create_env_template():
    """Create .env template if it doesn't exist"""
    if not os.path.exists(".env"):
        print("📄 Creating .env template...")
        env_template = """# Binance API Configuration
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_API_SECRET=your_binance_api_secret_here

# API URLs
BINANCE_TESTNET_URL=https://testnet.binance.vision/api
BINANCE_LIVE_URL=https://api.binance.com/api

# Bot Configuration
USE_TESTNET=True
SCAN_MODE=SELECTED
MIN_CONFIDENCE=0.65
MAX_POSITIONS=3
SCAN_INTERVAL=300
RISK_PERCENTAGE=0.015

# Custom Pairs (used when SCAN_MODE=CUSTOM)
CUSTOM_SYMBOLS=BTCUSDT,ETHUSDT,ADAUSDT,SOLUSDT,BNBUSDT
"""

        with open(".env", "w") as f:
            f.write(env_template)

        print("✅ Created .env template")
        print("⚠️  IMPORTANT: Edit .env file with your actual Binance API keys!")
    else:
        print("✅ .env file already exists")


def main():
    """Main setup function"""
    print("🚀 Crypto Trading Bot Setup")
    print("=" * 40)

    # Create directories
    create_directories()

    # Install requirements
    if not install_requirements():
        print("❌ Setup failed during package installation")
        return

    # Create .env template
    create_env_template()

    print("\n✅ Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit .env file with your Binance API credentials")
    print("2. Test with testnet: python main.py")
    print("3. Run multi-pair scanner: python scanner_main.py")
    print("4. Launch dashboard: streamlit run dashboard.py")

    print("\n⚠️  Remember:")
    print("- Always test on testnet first (USE_TESTNET=True)")
    print("- Start with small amounts when going live")
    print("- Monitor your bot regularly")


if __name__ == "__main__":
    main()
