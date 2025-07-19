# 🤖 Advanced Multi-Pair Crypto Trading Bot

> **Professional-grade cryptocurrency trading system with quantum analytics, adaptive risk management, and multi-pair scanning capabilities.**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app-url.streamlit.app)

## 🎯 **Project Overview**

This sophisticated cryptocurrency trading bot system combines classical technical analysis with quantum computing principles to deliver institutional-grade trading capabilities. The system features modular architecture, comprehensive risk management, and both manual and autonomous trading modes.

### **🌟 Key Features**

- **🔄 Multi-Pair Trading**: Scan and trade ALL crypto pairs, SELECTED quality pairs, or CUSTOM pairs
- **🧠 Enhanced Breakout Strategy**: 5% price moves with volume confirmation, time filtering, and RSI analysis
- **⚛️ Quantum Analytics**: Quantum-inspired algorithms for market analysis and signal generation
- **🛡️ Adaptive Risk Management**: Dynamic position sizing with confidence-based adjustments
- **📊 Real-time Dashboard**: Comprehensive Streamlit interface with live monitoring
- **✋ Manual Trading**: Full interface for any crypto pair with custom position sizing
- **🤖 Autonomous Trading**: Hands-off trading with sophisticated scanning and execution
- **📈 Performance Tracking**: Detailed analytics with P&L, win rates, and risk metrics

## 📁 **Project Structure**

```
crypto-bot/
├── 🎯 CORE SYSTEM
│   ├── hybrid_bot.py              # Main Streamlit dashboard
│   ├── main.py                    # Single-pair trading bot
│   ├── scanner_main.py            # Multi-pair scanner bot
│   └── setup.py                   # Quick installation script
│
├── 📈 TRADING MODULES
│   ├── strategy.py                # Enhanced breakout strategy
│   ├── trader.py                  # Position management
│   ├── trade_executor.py          # Trade execution interface
│   └── multi_pair_scanner.py      # Multi-pair scanning engine
│
├── 🧠 ANALYTICS & RISK
│   ├── quantum_engine.py          # Quantum trading algorithms
│   ├── risk_manager.py            # Risk monitoring system
│   ├── portfolio_manager.py       # Portfolio tracking
│   ├── market_analyzer.py         # Technical analysis
│   └── position_monitor.py        # Position tracking
│
├── 📊 MONITORING & LOGS
│   ├── logger.py                  # Comprehensive logging
│   ├── dashboard.py               # Advanced analytics dashboard
│   └── logs/                      # Auto-created log directory
│
└── ⚙️ CONFIGURATION
    ├── requirements.txt           # Python dependencies
    ├── .env.example               # Environment template
    ├── .gitignore                 # Security configurations
    └── railway.toml               # Deployment configuration
```

## 🚀 **Quick Start**

### **Option 1: Automated Setup (Recommended)**

```bash
# Clone the repository
git clone <your-repo-url>
cd crypto-bot

# Run automated setup
python setup.py

# Configure your API keys
nano .env  # Add your Binance API credentials

# Launch the dashboard
streamlit run hybrid_bot.py
```

### **Option 2: Manual Setup**

```bash
# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env

# Edit with your API keys
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
USE_TESTNET=True  # Start with testnet for safety

# Create logs directory
mkdir logs

# Run the bot
python hybrid_bot.py
```

## 🔧 **Configuration Guide**

### **Environment Variables**

```env
# 🔐 API CREDENTIALS
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_secret_key

# 🌐 API ENDPOINTS
BINANCE_TESTNET_URL=https://testnet.binance.vision/api
BINANCE_LIVE_URL=https://api.binance.com/api

# 🤖 BOT SETTINGS
USE_TESTNET=True                    # Safety first - always test!
SCAN_MODE=SELECTED                  # Options: ALL, SELECTED, CUSTOM
MIN_CONFIDENCE=0.65                 # Minimum confidence threshold
MAX_POSITIONS=3                     # Maximum simultaneous positions
SCAN_INTERVAL=300                   # Seconds between scans
RISK_PERCENTAGE=0.015               # Risk per trade (1.5%)

# 📊 CUSTOM PAIRS (when SCAN_MODE=CUSTOM)
CUSTOM_SYMBOLS=BTCUSDT,ETHUSDT,ADAUSDT,SOLUSDT,BNBUSDT
```

### **Trading Modes**

| Mode | Description | Risk Level | Recommended For |
|------|-------------|------------|-----------------|
| **CONSERVATIVE** | High confidence trades only | Low | Beginners |
| **BALANCED** | Standard institutional approach | Medium | Most users |
| **AGGRESSIVE** | High volatility trading | High | Experienced traders |
| **SCALPING** | Quick profits, minimal risk | Low | Active traders |
| **SWING** | Multi-day position holding | Medium | Patient traders |

## 📈 **Trading Strategy**

### **Enhanced Breakout Strategy**

Our core strategy detects significant price movements with multiple confirmation filters:

#### **🎯 Entry Conditions**
- **Price Movement**: ±5% change over 2 hours (120 1-minute candles)
- **Volume Confirmation**: Current volume ≥ 1.5x average volume
- **Time Filtering**: Avoid low-liquidity hours (0-6 UTC, 22-23 UTC)
- **Market Structure**: Confirm trend direction using higher highs/lows
- **Volatility Adjustment**: Increase threshold during high volatility (>5%)
- **RSI Filtering**: Avoid overbought (>80) and oversold (<20) conditions

#### **🛡️ Risk Management**
- **Dynamic Position Sizing**: 0.3x to 2.0x base quantity based on confidence
- **Take Profit**: 8-15% based on confidence level
- **Stop Loss**: 8-12% based on confidence level
- **Trailing Stops**: 3-4% trail when position is profitable
- **Time Limits**: Maximum 4-hour hold time
- **Emergency Exits**: >15% moves in either direction

#### **🔢 Confidence Scoring**
Our proprietary confidence algorithm combines multiple factors:
- **Time Factor**: Higher confidence during optimal trading hours
- **Volume Factor**: Scaled by volume ratio vs. average
- **Movement Strength**: Based on price change magnitude
- **Market Structure**: Higher score for clear trends
- **RSI Position**: Optimal range scoring (30-70)

**Final Score**: 0.0 to 1.0 (higher = more confident)

## 🎮 **Usage Examples**

### **1. Single-Pair Trading**
```bash
# Configure for Bitcoin trading
export TRADE_SYMBOL=BTCUSDT
export BASE_TRADE_QTY=0.001
export RISK_PERCENTAGE=0.015

# Run single-pair bot
python main.py
```

### **2. Multi-Pair Scanning**
```bash
# Scan all USDT pairs
export SCAN_MODE=ALL
export MIN_CONFIDENCE=0.7
export MAX_POSITIONS=5

# Run scanner bot
python scanner_main.py
```

### **3. Custom Pair Selection**
```bash
# Trade specific pairs only
export SCAN_MODE=CUSTOM
export CUSTOM_SYMBOLS=BTCUSDT,ETHUSDT,SOLUSDT

# Run with custom configuration
python scanner_main.py
```

### **4. Dashboard Monitoring**
```bash
# Launch comprehensive dashboard
streamlit run hybrid_bot.py

# Or advanced analytics dashboard
streamlit run dashboard.py
```

## 🖥️ **Dashboard Interface**

### **📊 Main Dashboard Tabs**

#### **1. Portfolio Overview**
- Real-time account balance and P&L metrics
- Asset allocation visualization
- Performance summaries with delta indicators

#### **2. Manual Trading Interface**
- **Any Crypto Pair**: Select from 1000+ available pairs
- **Position Calculator**: USD amount, custom quantity, or risk percentage
- **Risk Management**: Automatic stop-loss and take-profit settings
- **One-Click Trading**: Execute trades from scanner results
- **Emergency Controls**: Instant position closure capabilities

#### **3. Market Scanner**
- **Live Opportunities**: Real-time breakout detection
- **Confidence Scoring**: AI-powered signal strength analysis
- **Quick Trade**: One-click execution from scan results
- **Multi-Timeframe**: Analysis across different time horizons

#### **4. Auto-Trader Control**
- **Start/Stop**: Full autonomous trading control
- **Position Monitoring**: Real-time P&L tracking
- **Risk Limits**: Dynamic position sizing management
- **Performance Metrics**: Live trade statistics

#### **5. Quantum Analytics**
- **Quantum Signals**: Advanced algorithmic analysis
- **Entanglement Metrics**: Market correlation analysis
- **Superposition States**: Multi-scenario modeling
- **Uncertainty Principles**: Risk-adjusted predictions

#### **6. Performance Analytics**
- **Trade History**: Filterable trade logs with detailed metrics
- **Risk Analysis**: Drawdown charts and volatility tracking
- **Advanced Analytics**: Hourly performance, confidence correlation
- **Data Export**: CSV download for external analysis

## ⚛️ **Quantum Features**

Our quantum engine applies quantum computing principles to traditional trading:

### **🌀 Quantum Concepts**
- **Superposition**: Multiple market scenarios simultaneously
- **Entanglement**: Cross-asset correlation analysis
- **Uncertainty Principle**: Risk-adjusted position sizing
- **Quantum Tunneling**: Breakthrough resistance/support detection

### **📊 Quantum Metrics**
- **Quantum Confidence**: Probability-weighted signal strength
- **Entanglement Score**: Asset correlation coefficient
- **Superposition Index**: Multi-state market analysis
- **Quantum Momentum**: Phase-space velocity calculations

## 🛡️ **Security & Safety**

### **🔐 API Security**
- **Environment Variables**: Never hardcode API keys
- **IP Whitelisting**: Recommended for production use
- **Read-Only Keys**: For monitoring-only applications
- **Testnet First**: Always test before going live

### **💰 Risk Controls**
- **Position Limits**: Maximum exposure per trade and total
- **Account Protection**: Balance validation before trades
- **Emergency Stops**: Instant position closure capabilities
- **Risk Budgets**: Daily/weekly loss limits

### **⚠️ Safety Guidelines**

1. **Always start with Testnet** (`USE_TESTNET=True`)
2. **Begin with small amounts** when switching to live trading
3. **Monitor positions actively** during initial operation
4. **Set conservative risk limits** (1-2% per trade maximum)
5. **Keep API keys secure** and never share them
6. **Regular monitoring** of bot performance and positions

## 📊 **Performance Monitoring**

### **📈 Key Metrics Tracked**
- **Total Trades**: Number of completed trades
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Total gains / total losses ratio
- **Sharpe Ratio**: Risk-adjusted return metric
- **Maximum Drawdown**: Peak-to-trough decline
- **Average Hold Time**: Mean position duration
- **Volume Analysis**: Trade execution efficiency

### **📁 Logging System**
- **CSV Trade Logs**: Detailed trade-by-trade records
- **JSON Performance**: Calculated metrics and summaries
- **Scan Results**: Market opportunity logs with timing
- **Error Logs**: System errors and recovery actions

### **📊 Analytics Dashboard**
Access comprehensive analytics at `http://localhost:8501`:
- Interactive Plotly charts
- Filterable time periods
- Category performance breakdown
- Risk correlation analysis
- Exportable data formats

## 🐳 **Deployment**

### **Local Development**
```bash
# Standard Python environment
pip install -r requirements.txt
streamlit run hybrid_bot.py
```

### **Docker Deployment**
```bash
# Build container
docker build -t crypto-bot .

# Run with environment file
docker run --env-file .env -p 8501:8501 crypto-bot
```

### **Railway Deployment**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Deploy to Railway
railway login
railway init
railway up
```

### **Cloud Platforms**
- **Heroku**: Use `Procfile` for web dyno deployment
- **AWS ECS**: Container-based deployment with auto-scaling
- **Google Cloud Run**: Serverless container deployment
- **DigitalOcean**: Droplet or App Platform deployment

## 🔧 **Customization**

### **Adding New Strategies**
```python
# In strategy.py, add your custom strategy
def my_custom_strategy(klines):
    # Your strategy logic here
    return "BUY_LONG", "BUY_SHORT", or "HOLD"

# Register in strategy selector
STRATEGIES = {
    "breakout": check_breakout_enhanced,
    "my_strategy": my_custom_strategy
}
```

### **Custom Risk Profiles**
```python
# In risk_manager.py, add new profile
"MY_PROFILE": {
    "name": "My Custom Profile",
    "take_profit": 12.0,
    "stop_loss": 6.0,
    "trailing_stop": 3.0,
    "max_hold_hours": 2,
    "confidence_threshold": 0.8
}
```

### **New Trading Pairs**
```python
# Add to multi_pair_scanner.py
CUSTOM_PAIRS = [
    {'symbol': 'NEWUSDT', 'base_qty': 10, 'risk_multiplier': 0.7}
]
```

## 🐛 **Troubleshooting**

### **Common Issues**

#### **🔌 Connection Errors**
```bash
# Check internet connection
ping api.binance.com

# Verify API credentials
python -c "from binance.client import Client; print('API OK')"

# Check testnet connectivity
curl https://testnet.binance.vision/api/v3/ping
```

#### **📊 Dashboard Not Loading**
```bash
# Check Streamlit installation
streamlit --version

# Verify port availability
netstat -an | grep 8501

# Run with debug mode
streamlit run hybrid_bot.py --logger.level=debug
```

#### **💰 Trading Errors**
- **Insufficient Balance**: Check account funding
- **Invalid Symbol**: Verify pair exists and is active
- **API Rate Limits**: Reduce scan frequency
- **Order Rejection**: Check minimum order requirements

#### **📝 Log File Issues**
```bash
# Check log directory permissions
ls -la logs/

# Create missing directories
mkdir -p logs

# Check disk space
df -h
```

### **Debug Mode**
```bash
# Enable verbose logging
export DEBUG_MODE=True
export LOG_LEVEL=DEBUG

# Run with debugging
python hybrid_bot.py --debug
```

## 📚 **API Reference**

### **Core Modules**

#### **Strategy Module**
```python
from strategy import check_breakout_enhanced, get_strategy_confidence

# Get trading signal
signal = check_breakout_enhanced(klines)
confidence = get_strategy_confidence(klines)
```

#### **Risk Manager**
```python
from risk_manager import RiskManager

risk_mgr = RiskManager()
position_size = risk_mgr.calculate_position_size(balance, confidence)
```

#### **Trade Executor**
```python
from trade_executor import TradeExecutor

executor = TradeExecutor(client, risk_mgr)
result = executor.manual_trade(symbol, quantity, "BUY")
```

## 🤝 **Contributing**

We welcome contributions! Please follow these guidelines:

### **Development Setup**
```bash
# Fork and clone the repository
git clone https://github.com/your-username/crypto-bot.git

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/
```

### **Contribution Guidelines**
1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### **Code Standards**
- Follow PEP 8 style guidelines
- Add docstrings for all functions
- Include type hints where appropriate
- Write unit tests for new features
- Update documentation for changes

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 Crypto Trading Bot

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## ⚠️ **Disclaimer**

**IMPORTANT LEGAL NOTICE:**

- **Trading Risk**: Cryptocurrency trading involves substantial risk of loss and is not suitable for all investors.
- **No Guarantees**: Past performance does not guarantee future results.
- **Educational Purpose**: This software is for educational and research purposes.
- **Your Responsibility**: You are solely responsible for your trading decisions.
- **Compliance**: Ensure compliance with local regulations and exchange terms of service.
- **No Financial Advice**: This software does not provide financial or investment advice.

**USE AT YOUR OWN RISK**

## 🆘 **Support**

### **Community Support**
- **GitHub Issues**: [Report bugs and request features](https://github.com/your-username/crypto-bot/issues)
- **Discussions**: [Community forum for questions](https://github.com/your-username/crypto-bot/discussions)
- **Wiki**: [Comprehensive documentation](https://github.com/your-username/crypto-bot/wiki)

### **Commercial Support**
For enterprise deployments and custom development:
- Email: support@your-domain.com
- Website: https://your-website.com

## 🎉 **Acknowledgments**

- **Binance API**: For providing robust trading infrastructure
- **Streamlit**: For the excellent dashboard framework  
- **Python Community**: For the amazing ecosystem of trading libraries
- **Contributors**: All the developers who have contributed to this project

---

**🚀 Happy Trading! Remember to always trade responsibly and never risk more than you can afford to lose.**

---

*This README was generated for the Advanced Multi-Pair Crypto Trading Bot. For the latest updates and documentation, visit our [GitHub repository](https://github.com/your-username/crypto-bot).*