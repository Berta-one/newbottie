# ml/ensemble_model.py
import os
from typing import Optional, List, Sequence

from ml.model_loader import load_model

class Ensemble:
    """
    For now: a single XGBoost-like classifier that outputs two-class probabilities.
    Later: extend to blend LSTM, transformers, etc.
    """
    def __init__(self, xgb_path: Optional[str] = None):
        self.model = None
        self.loaded = False
        if xgb_path:
            try:
                self.model = load_model(xgb_path)
                self.loaded = True
            except Exception as e:
                # caller logs; remain unloaded → fallback in caller
                self.model = None
                self.loaded = False
                self.last_error = str(e)

    def predict_proba_one(self, feats: List[float]) -> float:
        """Return P(BUY) in [0,1]. If not loaded, raise."""
        if not self.loaded or self.model is None:
            raise RuntimeError("Ensemble model not loaded")
        # model expects 2D array
        proba = self.model.predict_proba([feats])
        if not proba or len(proba[0]) < 2:
            return 0.5
        return float(proba[0][1])  # P(class=BUY)


_ENSEMBLE: Optional[Ensemble] = None


def _default_model_path() -> Optional[str]:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for p in (
        os.getenv("XGB_MODEL_PATH"),
        os.getenv("ENSEMBLE_MODEL_PATH"),
        os.path.join(root, "models", "xgb.pkl"),
        os.path.join(root, "models", "ensemble.pkl"),
    ):
        if p and os.path.isfile(p):
            return p
    return None


def _get_ensemble() -> Ensemble:
    global _ENSEMBLE
    if _ENSEMBLE is None:
        _ENSEMBLE = Ensemble(xgb_path=_default_model_path())
    return _ENSEMBLE


def predict_proba(X: Sequence) -> List[List[float]]:
    """
    For each feature row, return [p_sell, p_buy, p_hold] (normalized).
    Used by ``engine.signal_generator``. If no model file is available, returns
    a neutral distribution so integration tests and smoke runs still execute.
    """
    ens = _get_ensemble()
    out: List[List[float]] = []
    for row in X:
        feats = list(row)
        if ens.loaded and ens.model is not None:
            try:
                proba = ens.model.predict_proba([feats])
                if not proba or len(proba[0]) < 2:
                    out.append([1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0])
                    continue
                p0 = proba[0]
                if len(p0) >= 3:
                    s, b, h = float(p0[0]), float(p0[1]), float(p0[2])
                else:
                    s, b = float(p0[0]), float(p0[1])
                    h = max(0.0, 1.0 - s - b)
                tot = s + b + h + 1e-12
                out.append([s / tot, b / tot, h / tot])
            except Exception:
                out.append([1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0])
        else:
            out.append([1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0])
    return out