import matplotlib.pyplot as plt
import pandas as pd


def plot_backtest(results_df: pd.DataFrame):
    plt.figure(figsize=(12, 6))
    plt.plot(results_df["timestamp"], results_df["capital"], label="Capital Over Time")

    buy_signals = results_df[results_df["signal"] == "BUY"]
    sell_signals = results_df[results_df["signal"] == "SELL"]

    plt.scatter(buy_signals["timestamp"], buy_signals["capital"], color="green", label="BUY", marker="^")
    plt.scatter(sell_signals["timestamp"], sell_signals["capital"], color="red", label="SELL", marker="v")

    plt.title("Quantum/Hybrid Strategy Backtest")
    plt.xlabel("Date")
    plt.ylabel("Portfolio Capital")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()