import pandas as pd
import numpy as np

def calculate_equity_curve(trades):
    trades['cumulative_pnl'] = trades['pnl'].cumsum()
    trades['equity'] = 100000 + trades['cumulative_pnl']
    return trades[['timestamp', 'equity']]

def calculate_drawdown(equity_series):
    peak = equity_series.cummax()
    drawdown = (equity_series - peak) / peak
    return drawdown.min()

def compute_metrics(trades):
    equity = trades['pnl'].cumsum() + 100000
    sharpe = trades['pnl'].mean() / trades['pnl'].std() * np.sqrt(252) if trades['pnl'].std() > 0 else 0
    drawdown = calculate_drawdown(equity)
    return {
        "Total Return": equity.iloc[-1] - 100000,
        "Max Drawdown": drawdown,
        "Sharpe Ratio": sharpe
    }
