# 🤖 Headless AI Trading Bot

A production-ready, headless cryptocurrency trading bot powered by AI/ML models with quantum computing capabilities and automated email reporting.

## ✨ Features

- **🧠 Hybrid AI Models**: LSTM + XGBoost + Quantum ML ensemble
- **⚡ Real-time Trading**: Live market data processing via CCXT/Binance
- **🔮 Quantum Computing**: Self-learning quantum circuits with IBM Quantum integration
- **🧬 Adaptive AI**: Multi-agent reinforcement learning with quantum coordination
- **📊 Quantum Advantage**: Real quantum hardware access with classical fallback
- **📊 Comprehensive Logging**: CSV-based trade and signal tracking
- **🐳 Containerized**: Docker deployment ready
- **⚙️ Paper/Live Trading**: Switch between simulation and real trading

## 🚀 Quick Start

### 1. Clone and Setup
```bash
git clone https://github.com/luigipascal/Bottie.git
cd Bottie

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
# Copy and edit configuration
cp .env.example .env
# Edit .env with your API keys and email settings
```

### 3. Run the Bot
```bash
# Start headless trading bot
python headless_bot.py

# Or run with Docker
docker build -t trading-bot .
docker run -d --name bot --env-file .env trading-bot
```

## 📁 Project Structure

```
├── headless_bot.py          # 🎯 Main entry point
├── engine/                  # ⚙️ Core trading logic
│   ├── trading_core.py      #    Market data & execution
│   ├── decision_engine.py   #    AI signal generation
│   ├── portfolio_manager.py #    Position management
│   └── risk_manager.py      #    Risk controls
├── ml/                      # 🧠 Machine learning models
│   ├── lstm_model.py        #    LSTM price predictor
│   ├── xgb_model.py         #    XGBoost classifier
│   └── decision_engine.py   #    Ensemble logic
├── quantum/                 # 🔮 IBM Quantum computing
│   ├── hybrid_models.py     #    Self-learning quantum ensemble
│   ├── qml_models.py        #    Variational quantum circuits
│   ├── portfolio_optimizer.py # QAOA portfolio optimization
│   ├── quantum_features.py #    Quantum feature encoding  
│   ├── backends.py          #    IBM Quantum backend management
│   └── healthcheck.py       #    Quantum system monitoring
├── agent_core/              # 🤖 Multi-agent architecture
│   ├── memory.py            #    Persistent learning memory
│   ├── planner.py           #    Strategic decision planning
│   └── reflector.py         #    Performance self-analysis
├── sentiment/               # 📰 News sentiment analysis
├── reporting/               # 📧 Email reports & logging
│   ├── email_reporter.py    #    HTML email generation
│   └── metrics_logger.py    #    CSV data logging
├── models/                  # 💾 Trained model files
├── training/                # 🎓 Model training scripts
└── logs/                    # 📋 Trading logs (auto-created)
```

## ⚙️ Configuration

### Required Environment Variables (.env)
```bash
# Trading Configuration
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET_KEY=your_binance_secret
MODE=paper  # or 'live' for real trading

# Email Reporting
BOT_EMAIL=your.bot.email@gmail.com
BOT_EMAIL_PASSWORD=your_app_password
REPORT_RECIPIENT_EMAIL=alerts@yourdomain.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# Trading Parameters
INITIAL_CAPITAL=10000
RISK_PER_TRADE=0.02
MAX_POSITIONS=3
```

### Binance API Setup
1. Create API key at [Binance API Management](https://www.binance.com/en/my/settings/api-management)
2. Enable "Enable Trading" for live trading
3. Restrict to your server IP for security
4. **Disable withdrawal permissions**

### Email Setup (Gmail)
1. Enable 2FA on your Gmail account
2. Generate App Password: Account Settings → Security → App passwords
3. Use the app password (not your regular password) in `.env`

## 📊 Monitoring & Reports

### Daily Email Reports Include:
- 📈 Portfolio performance summary
- 💰 Daily P&L and win rate
- 🎯 Recent trading signals
- ⚠️ Error alerts and system status

### Log Files Generated:
- `logs/trades.csv` - Executed trades with P&L
- `logs/signals.csv` - All trading signals generated
- `logs/bot.log` - System logs and errors
- `logs/daily_metrics.jsonl` - Daily performance metrics

## 🧠 Advanced AI/Quantum Architecture

### 🎯 **Self-Learning Ensemble**:
1. **Quantum VQC** (30% weight) - Self-adapting quantum circuits with parameter evolution
2. **LSTM Model** (35% weight) - Deep learning with quantum-enhanced features  
3. **XGBoost Model** (35% weight) - Gradient boosting with quantum preprocessing

### 🔄 **Adaptive Learning Process**:
- **Real-time Model Updates**: Quantum parameters adjust based on trading performance
- **Multi-Agent Architecture**: Trend, mean-reversion, and risk agents with quantum coordination
- **Walk-Forward Optimization**: Continuous retraining with quantum-enhanced backtesting
- **Regime Detection**: Quantum classifiers identify market regime changes

### 🧬 **Quantum Signal Generation**:
- **BUY**: Quantum ensemble confidence > 60% with positive entanglement
- **SELL**: Quantum ensemble confidence < 40% with negative correlation patterns
- **HOLD**: Quantum uncertainty state (40-60% confidence)
- **QUANTUM BOOST**: Special high-confidence signals when quantum advantage is detected

### 📈 **Performance Tracking**:
```bash
# Monitor quantum vs classical performance
python quantum/healthcheck.py

# View quantum circuit evolution
python dashboard/pages/quantum_featuremap_viewer.py

# Compare model performance
tail -f logs/quantum_metrics.jsonl
```

## 🔮 Advanced Quantum Computing Features

This bot leverages **IBM Quantum's cutting-edge technology** for superior market prediction and portfolio optimization:

### 🧬 **Quantum Machine Learning**
- **Variational Quantum Classifiers (VQC)**: Self-learning quantum neural networks
- **Quantum Feature Maps**: ZZ, Pauli, and RealAmplitudes encodings for complex price patterns
- **Quantum Kernel Methods**: Advanced pattern recognition in high-dimensional market data
- **Hybrid Quantum-Classical Ensemble**: 30% quantum weight in decision making

### 🎯 **Quantum Portfolio Optimization**
- **QAOA Algorithm**: Quantum Approximate Optimization for asset selection
- **Quantum Annealing**: Optimal portfolio weights using quantum superposition
- **Risk-Return Optimization**: Quantum-enhanced Markowitz optimization
- **Dynamic Rebalancing**: Real-time quantum portfolio adjustments

### 🔄 **Self-Learning Quantum Systems**
- **Adaptive Circuit Depth**: Automatically adjusts quantum circuit complexity
- **Parameter Evolution**: Quantum weights evolve based on market performance
- **Quantum Memory**: Stores successful trading patterns in quantum states
- **Online Learning**: Continuous quantum model updates with new market data

### 🌐 **IBM Quantum Integration**
- **Real Quantum Hardware**: Access to IBM's quantum computers (when available)
- **Quantum Simulators**: High-fidelity quantum simulation fallback
- **Backend Selection**: Automatic selection of best available quantum backend
- **Error Mitigation**: Advanced quantum error correction techniques

### 📊 **Quantum Advantage Metrics**
- **Circuit Visualization**: Real-time quantum circuit inspection
- **Quantum Metrics Tracking**: Quantum vs classical performance comparison
- **Entanglement Analysis**: Quantum correlation measurements
- **Coherence Monitoring**: Quantum state quality assessment

### Quantum Dependencies & Setup:
```bash
# Install IBM Quantum libraries
pip install qiskit qiskit-machine-learning qiskit-optimization qiskit-ibm-provider

# Set up IBM Quantum credentials
export IBMQ_API_KEY="your_ibm_quantum_api_key"

# Test quantum backend access
python scripts/verify_ibmq.py
```

### Quantum Configuration:
```bash
# Add to .env file
IBMQ_API_KEY=your_ibm_quantum_api_key
QUANTUM_BACKEND=ibmq_qasm_simulator  # or real hardware
QUANTUM_SHOTS=1024
ENABLE_QUANTUM=true
```

## 🐳 Docker Deployment

### Build and Run:
```bash
# Build image
docker build -t headless-trading-bot .

# Run container
docker run -d \
  --name trading-bot \
  --env-file .env \
  --restart unless-stopped \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/models:/app/models \
  headless-trading-bot
```

### Monitor Container:
```bash
# View logs
docker logs -f trading-bot

# Check status
docker stats trading-bot

# Access container
docker exec -it trading-bot bash
```

## 🛡️ Security Best Practices

- ✅ Use paper trading mode initially
- ✅ Restrict Binance API to specific IPs
- ✅ Disable withdrawal permissions on API key
- ✅ Store API keys in environment variables only
- ✅ Regular monitoring of trading activity
- ✅ Set reasonable position sizing limits

## 📈 Performance Optimization

### Recommended VPS Specs:
- **CPU**: 2+ cores
- **RAM**: 4GB minimum (8GB recommended)
- **Storage**: 20GB SSD
- **Network**: Stable internet connection

### Monitoring Commands:
```bash
# Check bot status
ps aux | grep headless_bot

# Monitor resource usage
htop

# Check recent trades
tail -f logs/trades.csv

# View email reports
cat logs/daily_metrics.jsonl | tail -1 | jq
```

## 🔧 Troubleshooting

### Common Issues:

**Bot not starting:**
```bash
# Check Python path and dependencies
python --version
pip list | grep -E "(ccxt|pandas|tensorflow)"
```

**No email reports:**
```bash
# Test email configuration
python -c "from reporting.email_reporter import EmailReporter; EmailReporter().send_error_alert('Test')"
```

**Trading errors:**
```bash
# Check API connectivity
python -c "import ccxt; print(ccxt.binance({'apiKey': 'test'}).fetch_ticker('BTC/USDT'))"
```

### Log Locations:
- System logs: `logs/bot.log`
- Trading activity: `logs/trades.csv`
- Error details: Check email alerts

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push branch: `git push origin feature-name`
5. Submit pull request

## ⚠️ Disclaimer

This software is for educational and research purposes. Cryptocurrency trading involves substantial risk of loss. The authors are not responsible for any financial losses incurred through the use of this software.

**Always test thoroughly in paper trading mode before using real funds.**

## 📄 License

MIT License - see LICENSE file for details.

## 🌟 Support

- 📧 Email: support@rondaninipublishing.com
- 🐛 Issues: [GitHub Issues](https://github.com/luigipascal/Bottie/issues)
- 📖 Documentation: [Wiki](https://github.com/luigipascal/Bottie/wiki)

---

**Made with ❤️ by Rondanini Publishing Ltd** 
