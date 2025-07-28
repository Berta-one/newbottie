
class EMACrossoverStrategy:
    def __init__(self, short_window=10, long_window=20):
        self.short_window = short_window
        self.long_window = long_window

    def generate_signal(self, data):
        short_ema = data['close'].ewm(span=self.short_window).mean()
        long_ema = data['close'].ewm(span=self.long_window).mean()
        if short_ema.iloc[-1] > long_ema.iloc[-1] and short_ema.iloc[-2] <= long_ema.iloc[-2]:
            return 'buy'
        elif short_ema.iloc[-1] < long_ema.iloc[-1] and short_ema.iloc[-2] >= long_ema.iloc[-2]:
            return 'sell'
        return 'hold'
