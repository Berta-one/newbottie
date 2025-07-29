from quantum.hybrid_models import HybridQuantumEnsemble
from engine.execution_manager import ExecutionManager
from engine.portfolio_manager import HybridPortfolioManager
from feature_engineer import extract_features


class TradingCore:
    """Live trading core using the Hybrid Quantum Ensemble for signal generation."""

    def __init__(self):
        self.model = HybridQuantumEnsemble()
        self.executor = ExecutionManager(num_assets=1)  # adapt as needed
        self.portfolio = HybridPortfolioManager(num_assets=1)

    def process_market_data(self, market_data):
        """Process a single incoming market data tick/bar."""
        features = extract_features(market_data).reshape(1, -1)
        signal, conf = self.model.predict(features)

        action = "BUY" if signal.lower() == "buy" else "SELL" if signal.lower() == "sell" else "HOLD"
        price = market_data["close"]

        # Only rebalance/execute on actionable signals
        if action != "HOLD":
            self.portfolio.rebalance(action, market_data)
            self.executor.execute(action, price)

        return {
            "signal": action,
            "confidence": conf,
            "price": price,
        }
