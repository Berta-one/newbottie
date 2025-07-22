
# Bottie Backtesting Engine (Real Integration)

## Features
- Tests your **ML + Quantum + Technical ensemble strategy** across multiple weight combinations.
- Runs on real historical OHLCV from Binance (via CCXT).
- Outputs ROI, Win Rate, Max Drawdown, and Trade Count.

## Installation
```bash
pip install ccxt pandas numpy
```

## Usage
```bash
python backtest_engine_real.py
```
Results will be saved in `backtest_output/backtest_results.csv`.

### Integration Notes
- Uncomment and link your ML & Quantum strategy imports:
  ```python
  from simplified_ml_strategy import SimplifiedMLStrategy
  from quantum_trading_integration import QuantumTrader
  from quantum_engine import QuantumAnalyzer
  ```
- Replace placeholders in `simulate_signals()` with actual strategy calls.
