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