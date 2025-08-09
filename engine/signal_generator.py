# engine/signal_generator.py
from __future__ import annotations

import os
import logging
from dataclasses import dataclass
from typing import Dict, Tuple, Sequence, List

import numpy as np

from ml.ensemble_model import predict_proba as ensemble_predict_proba

logger = logging.getLogger("SignalGenerator")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")

# Global, consistent class order across the project
CLASS_ORDER = ["SELL", "BUY", "HOLD"]  # indices: 0, 1, 2


def _to_feature_vector(bar: Dict) -> List[float]:
    """
    Very lightweight feature extractor (keep it minimal here).
    Replace/extend with your feature_engineer.extract_features if available.
    """
    # Expect close/high/low/volume; gracefully handle missing keys.
    close = float(bar.get("close", 0.0))
    high = float(bar.get("high", close))
    low = float(bar.get("low", close))
    vol = float(bar.get("volume", 0.0))

    # Simple features (examples):
    hl_range = (high - low) / max(abs(close), 1e-9)
    # You can add more (returns, rolling stats, indicators) elsewhere.
    return [close, high, low, vol, hl_range]


@dataclass
class SignalThresholds:
    buy_min: float
    sell_min: float
    hold_max: float
    min_conf_gap: float  # min margin between top1 and top2 class to accept


def _load_thresholds_from_env() -> SignalThresholds:
    """
    Pull thresholds from env (with safe defaults).
    """
    buy_min = float(os.getenv("SIG_BUY_MIN", "0.55"))       # require >= 55% buy prob
    sell_min = float(os.getenv("SIG_SELL_MIN", "0.55"))     # require >= 55% sell prob
    hold_max = float(os.getenv("SIG_HOLD_MAX", "0.50"))     # if max prob <= 50%, choose HOLD
    min_conf_gap = float(os.getenv("SIG_MIN_GAP", "0.05"))  # require top1 - top2 >= 5%

    return SignalThresholds(
        buy_min=buy_min,
        sell_min=sell_min,
        hold_max=hold_max,
        min_conf_gap=min_conf_gap,
    )


class SignalGenerator:
    """
    Converts ensemble probabilities into a discrete trading signal and confidence.

    Output:
      - signal: "BUY" | "SELL" | "HOLD"
      - confidence: float in [0, 1], derived from probability & margin
    """

    def __init__(self) -> None:
        self.thr = _load_thresholds_from_env()
        logger.info(
            "Signal thresholds: buy_min=%.2f, sell_min=%.2f, hold_max=%.2f, min_gap=%.2f",
            self.thr.buy_min, self.thr.sell_min, self.thr.hold_max, self.thr.min_conf_gap
        )

    @staticmethod
    def _confidence_from_probs(p_vec: Sequence[float]) -> float:
        """
        Confidence = top1 probability * margin(top1 - top2).
        """
        p = np.asarray(p_vec, dtype=float)
        if p.ndim != 1 or p.size < 2:
            return 0.0
        top2 = np.sort(p)[-2:]
        margin = float(top2[-1] - top2[-2])  # top1 - top2
        return float(top2[-1] * max(margin, 0.0))

    def _probs_to_signal(self, p_vec: Sequence[float]) -> Tuple[str, float]:
        p = np.asarray(p_vec, dtype=float)
        if p.size < 3:
            # Pad to [SELL, BUY, HOLD]
            if p.size == 2:
                sell, buy = float(p[0]), float(p[1])
                hold = max(0.0, 1.0 - sell - buy)
                p = np.array([sell, buy, hold], dtype=float)
            elif p.size == 1:
                buy = float(p[0])
                sell = 1.0 - buy
                hold = 0.0
                p = np.array([sell, buy, hold], dtype=float)
            else:
                p = np.array([1/3, 1/3, 1/3], dtype=float)

        # Normalize
        s = p.sum()
        if s <= 0:
            p = np.array([1/3, 1/3, 1/3], dtype=float)
        else:
            p = p / s

        sell_p, buy_p, hold_p = float(p[0]), float(p[1]), float(p[2])

        # Hard HOLD if confidence overall is low
        top_idx = int(np.argmax(p))
        top_p = float(p[top_idx])
        sorted_p = np.sort(p)
        margin = float(sorted_p[-1] - sorted_p[-2]) if sorted_p.size >= 2 else 0.0

        if top_p <= self.thr.hold_max or margin < self.thr.min_conf_gap:
            return "HOLD", self._confidence_from_probs(p)

        # Strong class thresholds
        if buy_p >= max(self.thr.buy_min, sell_p + self.thr.min_conf_gap, hold_p + self.thr.min_conf_gap):
            return "BUY", self._confidence_from_probs(p)

        if sell_p >= max(self.thr.sell_min, buy_p + self.thr.min_conf_gap, hold_p + self.thr.min_conf_gap):
            return "SELL", self._confidence_from_probs(p)

        # Else, ambiguous → HOLD
        return "HOLD", self._confidence_from_probs(p)

    def generate(self, bar: Dict) -> Tuple[str, float]:
        """
        Main entrypoint: pass a market bar dict, get (signal, confidence).
        """
        X = _to_feature_vector(bar)
        P = ensemble_predict_proba([X])  # returns [[p_sell, p_buy, p_hold]]
        if not P or not isinstance(P, list):
            logger.warning("Ensemble returned empty probabilities; HOLDing.")
            return "HOLD", 0.0

        p_vec = P[0]
        signal, conf = self._probs_to_signal(p_vec)
        logger.info(
            "Signal=%s conf=%.3f | P=[SELL=%.2f, BUY=%.2f, HOLD=%.2f] | %s",
            signal, conf, p_vec[0], p_vec[1], p_vec[2], bar.get("symbol", "?")
        )
        return signal, conf