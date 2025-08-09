# ml/ensemble_model.py
from __future__ import annotations

import os
import logging
from typing import Sequence, List, Tuple

import numpy as np

from ml.model_loader import load_lstm, load_xgb

logger = logging.getLogger("EnsembleModel")

# Bottie-wide convention for 3-class classification ordering:
# index 0 -> SELL, index 1 -> BUY, index 2 -> HOLD
CLASS_ORDER = ["SELL", "BUY", "HOLD"]


def _to_2d(X: Sequence) -> np.ndarray:
    arr = np.asarray(X)
    if arr.ndim == 1:
        arr = arr.reshape(1, -1)
    return arr


def _safe_softmax(P: np.ndarray, temperature: float = 1.0) -> np.ndarray:
    """
    Temperature-scaled softmax applied row-wise; useful if a model returns logits.
    If P already looks like probabilities, renormalize.
    """
    P = np.asarray(P, dtype=float)
    if P.ndim == 1:
        P = P.reshape(1, -1)
    # Heuristic: if any row sums very close to 1, assume probs; else treat as logits
    row_sums = P.sum(axis=1, keepdims=True)
    if np.allclose(row_sums, 1.0, atol=1e-3):
        S = row_sums + 1e-12
        return P / S
    # logits path
    Z = P / max(temperature, 1e-6)
    Z = Z - Z.max(axis=1, keepdims=True)
    expZ = np.exp(Z)
    S = expZ.sum(axis=1, keepdims=True) + 1e-12
    return expZ / S


class EnsembleModel:
    """
    Hybrid ensemble combining LSTM + XGB probabilities with configurable weights.
    - Pulls artifacts via ml.model_loader (prefers .pkl/.joblib)
    - Produces (n, 3) probs in CLASS_ORDER and string labels via argmax
    """

    def __init__(self,
                 w_lstm: float | None = None,
                 w_xgb: float | None = None,
                 temp_lstm: float = 1.0,
                 temp_xgb: float = 1.0):
        # Allow override via env for quick experimentation
        self.w_lstm = float(os.getenv("ENSEMBLE_W_LSTM", w_lstm if w_lstm is not None else 0.5))
        self.w_xgb = float(os.getenv("ENSEMBLE_W_XGB", w_xgb if w_xgb is not None else 0.5))
        wsum = self.w_lstm + self.w_xgb
        if wsum <= 1e-12:
            logger.warning("Ensemble weights sum to zero; defaulting to equal weights.")
            self.w_lstm = self.w_xgb = 0.5
            wsum = 1.0
        self.w_lstm /= wsum
        self.w_xgb /= wsum

        self.temp_lstm = float(os.getenv("ENSEMBLE_TEMP_LSTM", temp_lstm))
        self.temp_xgb = float(os.getenv("ENSEMBLE_TEMP_XGB", temp_xgb))

        # Load models via the robust loader
        self._lstm = load_lstm()  # LoadedModel wrapper
        self._xgb = load_xgb()    # LoadedModel wrapper

        logger.info("EnsembleModel ready (w_lstm=%.3f, w_xgb=%.3f, temps=(%.2f, %.2f))",
                    self.w_lstm, self.w_xgb, self.temp_lstm, self.temp_xgb)

    def _proba_lstm(self, X: np.ndarray) -> np.ndarray:
        P = self._lstm.predict_proba(X)
        P = np.asarray(P, dtype=float)
        P = _safe_softmax(P, temperature=self.temp_lstm)
        # ensure 3 columns in CLASS_ORDER; if not, project/expand
        P = self._ensure_three_columns(P)
        return P

    def _proba_xgb(self, X: np.ndarray) -> np.ndarray:
        P = self._xgb.predict_proba(X)
        P = np.asarray(P, dtype=float)
        P = _safe_softmax(P, temperature=self.temp_xgb)
        P = self._ensure_three_columns(P)
        return P

    @staticmethod
    def _ensure_three_columns(P: np.ndarray) -> np.ndarray:
        if P.ndim == 1:
            P = P.reshape(1, -1)
        c = P.shape[1]
        if c == 3:
            # renormalize
            S = P.sum(axis=1, keepdims=True) + 1e-12
            return P / S
        if c == 2:
            # assume [SELL, BUY] -> add HOLD residual, renormalize
            sell = np.clip(P[:, 0], 0.0, 1.0)
            buy = np.clip(P[:, 1], 0.0, 1.0)
            hold = np.clip(1.0 - sell - buy, 0.0, 1.0)
            S = sell + buy + hold + 1e-12
            return np.stack([sell / S, buy / S, hold / S], axis=1)
        if c == 1:
            # single column -> treat as BUY prob
            buy = np.clip(P[:, 0], 0.0, 1.0)
            sell = 1.0 - buy
            hold = np.zeros_like(buy)
            S = sell + buy + hold + 1e-12
            return np.stack([sell / S, buy / S, hold / S], axis=1)
        # more than 3 columns: take first 3 and renormalize
        P = P[:, :3]
        S = P.sum(axis=1, keepdims=True) + 1e-12
        return P / S

    def predict_proba(self, X: Sequence) -> List[List[float]]:
        X2 = _to_2d(X)

        P_lstm = self._proba_lstm(X2)
        P_xgb = self._proba_xgb(X2)

        P = self.w_lstm * P_lstm + self.w_xgb * P_xgb
        # final renormalization (just in case)
        S = P.sum(axis=1, keepdims=True) + 1e-12
        P = P / S
        return P.tolist()

    def predict(self, X: Sequence) -> List[str]:
        P = np.asarray(self.predict_proba(X))
        idx = P.argmax(axis=1)
        return [CLASS_ORDER[i] for i in idx]


# Optional singleton for frictionless import
_model_singleton: EnsembleModel | None = None


def get_model() -> EnsembleModel:
    global _model_singleton
    if _model_singleton is None:
        _model_singleton = EnsembleModel()
    return _model_singleton


# Convenience functions matching previous imports
def predict_proba(X: Sequence) -> List[List[float]]:
    return get_model().predict_proba(X)


def predict(X: Sequence) -> List[str]:
    return get_model().predict(X)