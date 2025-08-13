# 🧠 Bottie ML Learning Monitor

Advanced machine learning monitoring system for your Bottie cryptocurrency trading bot. Get real-time insights into ML performance, feature importance, and quantum learning impact.

## ✨ Features

- **Real-time ML Health Monitoring**: Track Brier scores, accuracy, and sample counts
- **Quantum Analysis**: Monitor quantum feature importance and ranking
- **Feature Importance Tracking**: See which features (EMA, ML, Quantum, Sentiment) are most predictive
- **Interactive Dashboard**: Rich terminal-based live dashboard
- **Detailed Reports**: Generate comprehensive learning analysis reports
- **Trend Visualization**: Plot ML performance trends over time

## 🚀 Quick Start

### 1. Installation (Windows)
```powershell
# Run the PowerShell setup script
.\setup_ml_monitor.ps1
```

### 2. Installation (Linux/Mac)
```bash
# Run the bash setup script
chmod +x setup_ml_monitor.sh
./setup_ml_monitor.sh
```

### 3. Test Backend Endpoints
```bash
# Verify ML endpoints are working
python test_ml_endpoints.py
```

### 4. Start Monitoring
```bash
# Live dashboard (recommended)
python ml_monitor.py --continuous

# Single check
python ml_monitor.py

# Generate report
python ml_monitor.py --report

# Plot trends
python ml_monitor.py --plot --save-plot trends.png
```

## 📊 Dashboard Interpretation

### Learning Health Status
- **🎉 Excellent** (Brier < 0.18): High-quality predictions, excellent learning
- **✅ Good** (Brier < 0.22): Solid performance, beating random significantly  
- **⚠️ Moderate** (Brier < 0.25): Learning slowly, consider data diversity
- **❌ Poor** (Brier > 0.25): Struggling to find patterns, check data quality

### Quantum Impact Analysis
- **Critical**: Quantum is #1 feature - heavily relied upon for predictions
- **High**: Quantum ranks #2-3 - highly valuable for predictions
- **Moderate**: Quantum ranks #4-5 - provides moderate value
- **Low**: Quantum ranks #6+ - other features more predictive

### Feature Importance
- Shows which prediction components are most valuable
- Quantum features highlighted in green when significant
- Rankings help prioritize which systems to optimize

## 🔧 Backend Integration

The monitor expects these API endpoints (already added to your `api/app.py`):

### `/ml/status` (Primary endpoint)
Returns current ML learning metrics:
```json
{
  "accuracy": 0.67,
  "brier_score": 0.21,
  "sample_count": 1250,
  "quantum_importance": 0.34,
  "quantum_feature_rank": 2,
  "feature_importance": {
    "ema_prob": 0.28,
    "quantum_prob": 0.34,
    "ml_prob": 0.25,
    "sentiment_prob": 0.13
  },
  "quantum_mode": "live"
}
```

### `/metrics/components` (Optional)
Advanced component performance metrics:
```json
{
  "performance": {
    "brier_loss": {
      "ml": 0.21,
      "q": 0.19
    },
    "sample_counts": {
      "ml": 1250
    }
  },
  "weights": {
    "current": {
      "q": 0.25
    }
  },
  "quantum_mode": "live"
}
```

## 📈 Understanding Metrics

### Brier Score
- **Range**: 0.0 (perfect) to 1.0 (worst possible)
- **Random Guessing**: ~0.25 for binary predictions
- **Good Performance**: < 0.22
- **Excellent Performance**: < 0.18

### Sample Count
- **Minimum for Meaningful Analysis**: 50-100 samples
- **Good Training Set**: 500+ samples
- **Robust Learning**: 1000+ samples

### Feature Importance
- **Sum to 1.0**: All feature importances are normalized
- **Higher = More Predictive**: Features with higher scores are more valuable
- **Dynamic**: Changes as the model learns new patterns

## 🛠️ Configuration

### API URL
Edit the scripts in `monitoring/` folder to change the API URL:
```bash
# Default: http://localhost:8000
# Change in: start_monitor.bat, generate_report.bat, plot_trends.bat
```

### Environment Variables
The monitor reads these from your trading bot:
- `QUANTUM_MODE`: "live", "shadow", or "off"
- ML learning parameters from your online learner

### Refresh Rate
```bash
# Change refresh interval (default: 30 seconds)
python ml_monitor.py --continuous --interval 60
```

## 📋 Usage Examples

### Continuous Monitoring
```bash
# Live dashboard with 30-second refresh
python ml_monitor.py --continuous

# Custom refresh rate (60 seconds)
python ml_monitor.py --continuous --interval 60

# Custom API URL
python ml_monitor.py --continuous --api-url http://127.0.0.1:9000
```

### Report Generation
```bash
# Generate and display report
python ml_monitor.py --report

# Report is automatically saved to ml_learning_report.txt
```

### Trend Analysis
```bash
# Show plots in window
python ml_monitor.py --plot

# Save plots to file
python ml_monitor.py --plot --save-plot analysis.png
```

## 🎯 Interpreting Results

### When to Act on Recommendations

**"Consider enabling quantum for live trading"**
- Quantum is performing well in shadow mode
- High feature rank (#1-3) indicates strong predictive power
- Switch `QUANTUM_MODE=live` if comfortable with quantum predictions

**"Check data quality and feature engineering"**
- High Brier scores (>0.25) indicate poor learning
- May need more diverse training data
- Consider adjusting learning parameters

**"Quantum may not be adding much value"**
- Quantum ranks low (#6+) consistently
- Classical features outperforming significantly
- Consider optimizing quantum circuit or disabling

### Performance Trends
- **Improving Brier Scores**: Learning is working, model getting better
- **Stable Scores**: Model has reached equilibrium for current data
- **Degrading Scores**: May indicate overfitting or data quality issues

## 🔍 Troubleshooting

### "Connection Failed"
- Ensure your Bottie API is running on the expected port
- Check API URL in monitor scripts
- Verify `/ml/status` endpoint is accessible

### "No ML Performance Data"
- ML online learner may not have enough samples yet
- Wait for trading signals to accumulate training data
- Check if online learning is enabled in your bot

### "Insufficient Data"
- Need at least 50-100 trading samples for meaningful analysis
- Let the bot trade and accumulate more signals
- Consider paper trading to generate more samples faster

### Import Errors
```bash
# Install missing packages
pip install rich matplotlib requests numpy pandas
```

## 📝 Files Created

After running setup:
```
ml_monitor.py              # Main monitoring script
test_ml_endpoints.py       # Endpoint testing utility
setup_ml_monitor.ps1       # Windows PowerShell installer
setup_ml_monitor.sh        # Linux/Mac bash installer
monitoring/                # Generated by setup
  ├── start_monitor.bat    # Windows: Start live dashboard  
  ├── generate_report.bat  # Windows: Generate report
  ├── plot_trends.bat      # Windows: Create trend plots
  ├── start_monitor.ps1    # PowerShell: Start live dashboard
  ├── generate_report.ps1  # PowerShell: Generate report
  └── plot_trends.ps1      # PowerShell: Create trend plots
```

## 🤝 Integration Notes

- **Non-blocking**: Monitor runs independently of your trading bot
- **Read-only**: Only reads data, doesn't affect trading decisions
- **Lightweight**: Minimal performance impact on your API
- **Extensible**: Easy to add custom metrics and analysis

The ML monitor is designed to give you deep insights into how well your trading bot is learning and adapting to market conditions. Use it to optimize your ML parameters, understand feature performance, and make informed decisions about quantum computing integration.

Happy monitoring! 🚀
