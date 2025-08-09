# ml/xgb_model.py
from __future__ import annotations

import logging
from typing import Sequence, List

import numpy as np
from ml.model_loader import load_xgb

logger = logging.getLogger("XGBModel")
CLASS_ORDER = ["SELL", "BUY", "HOLD"]  # indices: 0,1,2


def _to_2d(X: Sequence) -> np.ndarray:
    arr = np.asarray(X)
    if arr.ndim == 1:
        arr = arr.reshape(1, -1)
    return arr


class XGBModel:
    """
    Wrapper that normalizes input and guarantees 3-class probabilities
    in the order [SELL, BUY, HOLD].
    """

    def __init__(self) -> None:
        self._loaded = load_xgb()
        logger.info("XGBModel loaded from %s (kind=%s)", self._loaded.path, self._loaded.kind)

    def predict_proba(self, X: Sequence) -> List[List[float]]:
        X2 = _to_2d(X)
        proba = self._loaded.predict_proba(X2)
        P = np.asarray(proba, dtype=float)

        if P.ndim == 1:
            P = P.reshape(-1, 1)

        if P.shape[1] == 1:  # single prob → treat as BUY
            buy = np.clip(P[:, 0], 0.0, 1.0)
            sell = 1.0 - buy
            hold = np.zeros_like(buy)
            P = np.stack([sell, buy, hold], axis=1)
        elif P.shape[1] == 2:  # [SELL, BUY] → add HOLD residual
            sell = np.clip(P[:, 0], 0.0, 1.0)
            buy = np.clip(P[:, 1], 0.0, 1.0)
            hold = np.clip(1.0 - sell - buy, 0.0, 1.0)
            S = sell + buy + hold + 1e-12
            P = np.stack([sell / S, buy / S, hold / S], axis=1)
        else:
            P = P[:, :3]
            S = P.sum(axis=1, keepdims=True) + 1e-12
            P = P / S

        return P.tolist()

    def predict(self, X: Sequence) -> List[str]:
        P = np.asarray(self.predict_proba(X))
        idx = P.argmax(axis=1)
        return [CLASS_ORDER[i] for i in idx]


_model_singleton: XGBModel | None = None


def get_model() -> XGBModel:
    global _model_singleton
    if _model_singleton is None:
        _model_singleton = XGBModel()
    return _model_singleton


def predict_proba(X: Sequence) -> List[List[float]]:
    return get_model().predict_proba(X)


def predict(X: Sequence) -> List[str]:
    return get_model().predict(X)