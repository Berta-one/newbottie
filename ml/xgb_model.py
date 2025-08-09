# ml/xgb_model.py
from __future__ import annotations

import os
import logging
from typing import Sequence, List

import numpy as np

from ml.model_loader import load_xgb

logger = logging.getLogger("XGBModel")

# Bottie-wide convention for 3-class classification ordering:
# index 0 -> SELL, index 1 -> BUY, index 2 -> HOLD
CLASS_ORDER = ["SELL", "BUY", "HOLD"]


def _to_2d(X: Sequence) -> np.ndarray:
    """Ensure X is a 2D numpy array."""
    arr = np.asarray(X)
    if arr.ndim == 1:
        arr = arr.reshape(1, -1)
    return arr


class XGBModel:
    """
    Thin wrapper around the loaded XGBoost model (or stub) that:
      - normalizes input shape
      - exposes predict_proba() with shape (n_samples, 3)
      - exposes predict() -> list of labels following CLASS_ORDER
    """

    def __init__(self) -> None:
        self._loaded = load_xgb()  # LoadedModel wrapper
        logger.info("XGBModel loaded from %s (kind=%s)", self._loaded.path, self._loaded.kind)

    def predict_proba(self, X: Sequence) -> List[List[float]]:
        X2 = _to_2d(X)
        proba = self._loaded.predict_proba(X2)

        # Convert to numpy array to validate/reshape
        P = np.asarray(proba, dtype=float)

        # If model returns binary probs, expand to 3-class
        if P.ndim == 1:
            P = P.reshape(-1, 1)
        if P.shape[1] == 1:
            # assume column is P(BUY); map to [SELL, BUY, HOLD] with a small HOLD mass
            buy = np.clip(P[:, 0], 0.0, 1.0)
            sell = 1.0 - buy
            hold = np.full_like(buy, 0.0)
            P = np.stack([sell, buy, hold], axis=1)
        elif P.shape[1] == 2:
            # assume [P(SELL), P(BUY)] → add HOLD as small residual (clipped to >= 0)
            sell = np.clip(P[:, 0], 0.0, 1.0)
            buy = np.clip(P[:, 1], 0.0, 1.