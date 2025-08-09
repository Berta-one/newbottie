# engine/classical_optimizer.py
from __future__ import annotations

import logging
from typing import Dict, Tuple

logger = logging.getLogger("ClassicalOptimizer")


class ClassicalPortfolioOptimizer:
    """
    Simple mapping from signals to target weights, confidence‑scaled and normalized.
    BUY -> +conf
    SELL -> -conf
    HOLD ->  0
    Then L1‑normalize if needed to keep total exposure <= 1.0.
    """

    def __init__(self, num_assets: int, initial_capital: float = 10_000.0):
        self.num_assets = num_assets
        self.initial_capital = initial_capital

    def optimize(self, signals: Dict[str, Tuple[str, float]]) -> Dict[str, float]:
        raw: Dict[str, float] = {}
        for sym, (sig, conf) in signals.items():
            sig = (sig or "HOLD").upper()
            c = float(conf)
            if sig == "BUY":
                raw[sym] = +c
            elif sig == "SELL":
                raw[sym] = -c
            else:
                raw[sym] = 0.0

        # L1 normalization: keep total absolute exposure <= 1.0
        l1 = sum(abs(v) for v in raw.values())
        if l1 > 1.0:
            raw = {k: v / l1 for k, v in raw.items()}
        return raw