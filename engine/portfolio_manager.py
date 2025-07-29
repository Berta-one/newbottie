# engine/portfolio_manager.py

import numpy as np
import logging

class ClassicalPortfolioOptimizer:
    def __init__(self, capital=10000):
        self.capital = capital
        self.positions = {}
        self.logger = logging.getLogger(__name__)

    def rebalance(self, signals, prices):
        """
        signals: dict of asset -> signal ("buy"/"sell"/"hold")
        prices: dict of asset -> price
        """
        new_positions = {}
        num_buys = sum(1 for s in signals.values() if s == "buy")
        if num_buys == 0:
            return self.positions

        allocation = self.capital / num_buys

        for asset, signal in signals.items():
            if signal == "buy" and asset in prices:
                quantity = allocation / prices[asset]
                new_positions[asset] = quantity
                self.logger.info(f"Buying {asset} @ {prices[asset]:.2f} qty: {quantity:.4f}")
            elif signal == "hold":
                new_positions[asset] = self.positions.get(asset, 0)
            elif signal == "sell":
                self.logger.info(f"Selling {asset}")
            else:
                self.logger.warning(f"Unknown signal for {asset}: {signal}")

        self.positions = new_positions
        return self.positions
