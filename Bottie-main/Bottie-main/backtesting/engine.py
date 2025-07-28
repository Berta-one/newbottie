
import pandas as pd

class Backtester:
    def __init__(self, strategy, data):
        self.strategy = strategy
        self.data = data
        self.trades = []

    def run(self):
        position = None
        for i in range(1, len(self.data)):
            signal = self.strategy.generate_signal(self.data.iloc[:i])
            if signal == 'buy' and not position:
                position = {'entry_price': self.data['close'].iloc[i], 'entry_index': i}
            elif signal == 'sell' and position:
                exit_price = self.data['close'].iloc[i]
                pnl = exit_price - position['entry_price']
                self.trades.append(pnl)
                position = None

    def report(self):
        if not self.trades:
            return "No trades executed."
        total = sum(self.trades)
        return {
            'total_pnl': total,
            'avg_pnl': total / len(self.trades),
            'num_trades': len(self.trades),
            'win_rate': sum(1 for t in self.trades if t > 0) / len(self.trades)
        }
