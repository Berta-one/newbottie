from backtesting.quantum_backtester import QuantumBacktester
from visualization.backtest_plot import plot_backtest
import pandas as pd

if __name__ == "__main__":
    df = pd.read_csv("sample_data/historical_data.csv", index_col=0, parse_dates=True)
    tester = QuantumBacktester(mode="hybrid")
    report = tester.run_backtest(df)
    plot_backtest(report)