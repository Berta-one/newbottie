import numpy as np

def sharpe_ratio(returns, risk_free=0.0):
    excess = np.array(returns) - risk_free
    return np.mean(excess) / (np.std(excess) + 1e-9)

def sortino_ratio(returns, target=0.0):
    downside = np.std([r for r in returns if r < target]) + 1e-9
    return (np.mean(returns) - target) / downside

def max_drawdown(equity_curve):
    peak = equity_curve[0]
    max_dd = 0
    for x in equity_curve:
        if x > peak:
            peak = x
        dd = (peak - x) / peak
        max_dd = max(max_dd, dd)
    return max_dd
