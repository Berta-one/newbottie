
from strategy.ema_crossover import EMACrossoverStrategy

class DecisionEngine:
    def __init__(self):
        self.strategy = EMACrossoverStrategy()

    def evaluate(self, market_data):
        return self.strategy.generate_signal(market_data)
