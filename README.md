# 🤖 Bottie - Autonomous Crypto Trading Bot

**Advanced AI-powered cryptocurrency trading system with adaptive machine learning, quantum-inspired algorithms, and real-time sentiment analysis.**

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

## Quick Start

Launch the application using the `render_api.py` script:

```bash
python render_api.py
```

`render_api.py` is the official entry point for the Bottie system.

## 🚀 **Key Features**

### 🧠 **Adaptive Machine Learning**
- **Per-pair learning**: Individual ML models for each trading pair
- **Dynamic thresholds**: Automatically adjusts buy/sell thresholds based on performance
- **Confidence-based trading**: Only executes trades when confidence is high enough
- **Autonomous decision making**: No human intervention required once trained

### 💰 **Fee-Inclusive P&L Calculations**
- **True profitability**: All P&L calculations include trading fees
- **Fee transparency**: Complete breakdown of fees paid per pair
- **Historical fee tracking**: Cumulative fee analysis across all trades
- **Risk-adjusted returns**: Real performance metrics after all costs

### 📊 **Real-Time Data Integration**
- **Binance WebSocket streams**: Live account updates and price feeds
- **Sentiment analysis**: Real news sentiment from Finnhub API
- **Technical indicators**: Advanced price momentum and volume analysis
- **Quantum-inspired algorithms**: Portfolio optimization using quantum concepts

### 🎯 **Professional Analytics**
- **Risk metrics**: Sharpe ratio, Sortino ratio, VaR, max drawdown
- **Portfolio optimization**: Quantum-inspired rebalancing recommendations
- **Cross-pair arbitrage**: Grid matrix for trading opportunities
- **Performance tracking**: Complete trade history with ML insights

## 🏗️ **System Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Data Sources  │
│   (Netlify)     │◄───┤   (Render)      │◄───┤   (Live Feeds)  │
│                 │    │                 │    │                 │
│ • Dashboard     │    │ • FastAPI       │    │ • Binance API   │
│ • Analytics     │    │ • WebSocket     │    │ • WebSocket     │
│ • ML Insights   │    │ • Adaptive ML   │    │ • Finnhub API   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🛠️ **Installation & Setup**

### **Prerequisites**
- Python 3.8+
- Binance account with API access
- Finnhub API key (for sentiment analysis)

### **Local Development**
```bash
# Clone repository
git clone <repository-url>
cd bottie-trading-bot

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export BINANCE_API_KEY="your_binance_api_key"
export BINANCE_API_SECRET="your_binance_secret"
export FINNHUB_API_KEY="your_finnhub_key"

# Run locally
python render_api.py
```

### **Render Deployment**
1. Connect GitHub repository to Render
2. Set environment variables in Render dashboard:
   - `BINANCE_API_KEY`
   - `BINANCE_API_SECRET` 
   - `FINNHUB_API_KEY`
3. Deploy using `render.yaml` configuration

## 📡 **API Endpoints**

### **Core Trading**
- `GET /status` - Main dashboard with fee-inclusive P&L
- `GET /positions` - All positions with net profitability
- `GET /trades` - Complete trade history (hundreds of trades)
- `GET /signals` - Adaptive ML trading signals

### **Machine Learning**
- `GET /ml/status` - Real ML performance metrics
- `GET /ml/pair-analysis/{symbol}` - Detailed per-pair analysis
- `GET /ml/learning-summary` - System-wide learning status
- `GET /ml/brier-score` - Prediction accuracy metrics

### **Advanced Analytics**
- `GET /analytics/advanced` - Professional risk metrics
- `GET /quantum/analysis` - Quantum-inspired portfolio optimization
- `GET /grid/matrix` - Cross-pair arbitrage opportunities
- `GET /sentiment` - Real-time news sentiment analysis

## 🧠 **Adaptive ML System**

### **How It Works**
1. **Individual Pair Learning**: Each trading pair (BTC/USDT, ETH/USDT, etc.) has its own ML model
2. **Performance Tracking**: Win rate, P&L, and confidence calculated per pair
3. **Dynamic Thresholds**: Buy/sell thresholds adjust based on historical performance
4. **Autonomous Execution**: System decides when to trade based on confidence levels

### **Threshold Adaptation**
```python
# High confidence pairs (>80% confidence, >70% win rate)
buy_threshold = 0.55   # More aggressive
sell_threshold = 0.45

# Medium confidence pairs
buy_threshold = 0.65   # Balanced
sell_threshold = 0.35

# Low confidence pairs (<50% confidence)
buy_threshold = 0.80   # Very conservative  
sell_threshold = 0.20
```

### **Autonomous Readiness**
- **Per-pair ready**: Confidence > 0.7 + minimum 20 trades
- **System ready**: >80% of pairs meet readiness criteria
- **Full autonomy**: No human intervention needed

## 💰 **Fee Management**

### **Comprehensive Fee Tracking**
- **Trading fees**: 0.1% standard Binance rate
- **Round-trip estimates**: 0.2% for position calculations
- **Historical tracking**: All fees paid per trading pair
- **Impact analysis**: How fees affect profitability

### **Fee-Inclusive Calculations**
```json
{
  "equity": {
    "gross": 1500.00,      // Raw balance
    "net": 1485.50,        // After fees
    "display_value": 1485.50  // What users see
  },
  "positions": {
    "BTC/USDT": {
      "gross_pnl": 150.00,
      "net_pnl": 147.50,     // After fees
      "estimated_fees": 2.50,
      "total_fees_impact": 7.70
    }
  }
}
```

## 📊 **Data Sources**

### **Real-Time Feeds**
- **Binance WebSocket**: Account updates, trade executions, price feeds
- **Finnhub API**: News sentiment analysis for major cryptocurrencies
- **Technical Indicators**: Price momentum, volume analysis, volatility

### **Persistent Storage**
- `ml_pair_performance.json` - ML learning data
- `stored_trades.json` - Complete trade history
- `trades_cache.json` - Recent trade cache

## 🎯 **Performance Metrics**

### **Trading Performance**
- **Win Rate**: Percentage of profitable trades per pair
- **Profit Factor**: Ratio of winning to losing trades
- **Sharpe Ratio**: Risk-adjusted returns
- **Maximum Drawdown**: Largest loss from peak
- **Calmar Ratio**: Return vs. maximum drawdown

### **ML Performance**
- **Brier Score**: Prediction accuracy (0.0 = perfect, 1.0 = worst)
- **Confidence Evolution**: How confidence changes over time
- **Learning Progress**: Accuracy improvement trends
- **Feature Importance**: Which factors drive decisions

## 🚨 **Risk Management**

### **Position Limits**
- Maximum 30% portfolio exposure per position
- Fee-adjusted stop losses and take profits
- Confidence-based position sizing
- Cross-pair correlation analysis

### **Autonomous Safeguards**
- Only trades when ML confidence > 70%
- Minimum 20 trades required for autonomy
- Fee impact considered in all decisions
- Real-time risk monitoring

## 🔧 **Configuration**

### **Environment Variables**
```bash
# Required
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_secret_key
FINNHUB_API_KEY=your_finnhub_key

# Optional
SENTIMENT_ENABLED=1
SENTIMENT_WINDOW_S=900
SENTIMENT_ASSETS=BTC,ETH,BNB,SOL,ADA
```

### **ML Configuration**
- **Confidence Threshold**: 0.7 (70% confidence required)
- **Minimum Trades**: 20 trades per pair for autonomy
- **Learning Window**: Last 1000 predictions per pair
- **Fee Rate**: 0.1% standard, 0.2% round-trip estimate

## 📈 **Usage Examples**

### **Check System Status**
```bash
curl https://your-render-app.onrender.com/status
```

### **Get Trading Signals**
```bash
curl https://your-render-app.onrender.com/signals
```

### **Analyze Specific Pair**
```bash
curl https://your-render-app.onrender.com/ml/pair-analysis/BTC/USDT
```

### **View Advanced Analytics**
```bash
curl https://your-render-app.onrender.com/analytics/advanced
```

## 🔍 **Monitoring & Debugging**

### **Key Logs to Monitor**
- WebSocket connection status
- ML learning progress per pair
- Fee calculation accuracy
- Trade execution results

### **Health Checks**
- `/health` - System status
- `/debug/exchange` - Exchange connection
- `/debug/sentiment` - Sentiment service status

## 🚀 **Deployment Checklist**

### **Pre-Deployment**
- [ ] Set all environment variables in Render
- [ ] Verify Binance API permissions (trading enabled)
- [ ] Test Finnhub API key
- [ ] Review risk management settings

### **Post-Deployment**
- [ ] Verify WebSocket connections
- [ ] Check ML learning initialization
- [ ] Monitor first trades for fee calculations
- [ ] Validate sentiment data integration

## 📚 **Advanced Features**

### **Quantum-Inspired Algorithms**
- **Superposition**: Price probability distributions
- **Entanglement**: Asset correlation analysis  
- **Interference**: Market pattern detection
- **Portfolio Optimization**: Quantum-enhanced rebalancing

### **Sentiment Integration**
- **Real-time news**: Finnhub API integration
- **Multi-asset analysis**: BTC, ETH, SOL, ADA, etc.
- **Sentiment scoring**: VADER sentiment analysis
- **Market correlation**: Sentiment vs. performance

### **Grid Matrix Trading**
- **Cross-pair opportunities**: Find arbitrage between pairs
- **Atomic swaps**: Direct crypto-to-crypto trades
- **Risk scoring**: Confidence-based opportunity ranking
- **Execution recommendations**: When and how to trade

## 🤝 **Contributing**

### **Development Workflow**
1. Fork repository
2. Create feature branch
3. Implement changes with tests
4. Update documentation
5. Submit pull request

### **Code Standards**
- Fee-inclusive calculations required
- ML confidence tracking mandatory
- WebSocket error handling essential
- Comprehensive logging for debugging

## 📄 **License**

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ **Disclaimer**

**IMPORTANT**: This is an autonomous trading system that can execute real trades with real money. 

- **Use at your own risk**: Cryptocurrency trading involves substantial risk
- **Test thoroughly**: Use testnet/sandbox mode before live trading
- **Monitor actively**: Even autonomous systems need supervision
- **Understand fees**: All trading involves costs that affect profitability
- **Start small**: Begin with small amounts to verify system behavior

**Past performance does not guarantee future results. Only trade with money you can afford to lose.**

---

**🤖 Bottie - Where AI meets autonomous crypto trading** 

*Built with adaptive machine learning, quantum-inspired algorithms, and complete fee transparency.* 
