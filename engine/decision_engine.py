# engine/decision_engine.py

from ml.decision_engine import load_model_and_predict
from strategy.ema_crossover import EMACrossoverStrategy

class DecisionEngine:
    def __init__(self):
        self.strategy = EMACrossoverStrategy()

    def generate_signal(self, market_data: dict) -> str:
        # Traditional strategy logic
        strat_signal = self.strategy.generate_signal(market_data)
        ml_signal = load_model_and_predict(market_data)

        # Basic ensemble vote logic
        if strat_signal == ml_signal:
            return strat_signal
        else:
            return "hold"