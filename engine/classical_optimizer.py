# engine/classical_optimizer.py
from __future__ import annotations

import logging
from typing import Dict, List

import numpy as np

logger = logging.getLogger("ClassicalOptimizer")


class ClassicalPortfolioOptimizer:
    """
    Map per-symbol confidence scores to target weights (long-only), capped and renormalized.
    Used when quantum optimization is unavailable or as fallback.
    """

    def __init__(self, max_pos_pct: float = 0.5):
        self.max_pos_pct = float(max_pos_pct)

    def target_weights(self, symbols: List[str], conf_map: Dict[str, float]) -> Dict[str, float]:
        if not symbols:
            return {}
        raw = np.array([max(0.0, float(conf_map.get(s, 0.0))) for s in symbols], dtype=float)
        tot = float(raw.sum())
        if tot <= 1e-12:
            return {s: 0.0 for s in symbols}
        w = raw / tot
        w = np.clip(w, 0.0, self.max_pos_pct)
        s2 = float(w.sum())
        if s2 > 1e-12:
            w = w / s2
        return {sym: float(wi) for sym, wi in zip(symbols, w)}
