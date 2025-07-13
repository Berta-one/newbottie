# Bottie - Multi-Pair Crypto Trading Bot

A sophisticated cryptocurrency trading bot that can scan and trade multiple pairs simultaneously.

## 🚀 Features

- **Multi-Pair Trading**: Scan ALL, SELECTED, or CUSTOM crypto pairs
- **Enhanced Strategy**: 5% breakout with volume, time, and volatility filters
- **Smart Risk Management**: Dynamic position sizing based on confidence
- **Real-time Dashboard**: Streamlit-based monitoring and analytics
- **Comprehensive Logging**: CSV and JSON trade tracking

## 📦 Quick Setup

1. Install dependencies:

pip install -r requirements.txt

2. Configure your API keys in `.env`:
BINANCE_API_KEY=your_key_here
BINANCE_API_SECRET=your_secret_here

3. Run the bot:
Single-pair trading
python main.py
Multi-pair scanning
python scanner_main.py
Dashboard
streamlit run dashboard.py
## ⚠️ Important Notes

- Always test on testnet first (`USE_TESTNET=True`)
- Start with small amounts
- This is for educational purposes - trade at your own risk

## 📊 Trading Modes

- **SELECTED**: Curated list of quality crypto pairs (recommended)
- **ALL**: Scan top crypto pairs by volume
- **CUSTOM**: Your own symbol list

## 🛡️ Risk Management

- Maximum 1.5% account risk per trade
- Dynamic stop/take levels based on confidence
- Trailing stops and time-based exits
- Emergency exits on extreme moves

## 📈 Performance Tracking

- Real-time P&L monitoring
- Win rate by category
- Comprehensive trade logging
- Performance analytics

---

**Disclaimer**: Cryptocurrency trading involves substantial risk. This bot is provided as-is for educational purposes.
