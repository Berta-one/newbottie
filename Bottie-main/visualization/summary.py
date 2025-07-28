
import matplotlib.pyplot as plt

def plot_results(data, trades):
    plt.figure(figsize=(12,6))
    plt.plot(data['close'], label='Price')
    for trade in trades:
        plt.axvline(x=trade['entry_index'], color='green' if trade['pnl'] > 0 else 'red', linestyle='--')
    plt.title('Trade Results')
    plt.legend()
    plt.show()
