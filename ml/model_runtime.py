# ml/model_runtime.py
import json
import joblib
from typing import Optional, Tuple, List

class ModelRuntime:
    """
    Loads a trained classifier and its optimal decision threshold.
    Exposes predict_proba() and predict_binary() for a single feature vector.
    """
    def __init__(self, model_path: str, meta_path: Optional[str] = None):
        self.model_path = model_path
        self.meta_path = meta_path
        self.model = None
        self.threshold = 0.5  # default if meta missing
        self.feature_count = None

    def load(self):
        self.model = joblib.load(self.model_path)
        if self.meta_path:
            try:
                with open(self.meta_path, "r") as f:
                    meta = json.load(f)
                thr = float(meta.get("optimal_threshold", 0.5))
                self.threshold = max(0.0, min(1.0, thr))
                self.feature_count = int(meta.get("feature_count") or 5)
            except Exception:
                # meta optional
                pass
        return self

    def predict_proba(self, feats: List[float]) -> float:
        if self.model is None:
            raise RuntimeError("ModelRuntime not loaded. Call load().")
        # XGBoost scikit wrapper expects 2D
        import numpy as np
        X = np.array(feats, dtype=float).reshape(1, -1)
        p = self.model.predict_proba(X)[0, 1]
        return float(p)

    def predict_binary(self, feats: List[float]) -> int:
        p = self.predict_proba(feats)
        return 1 if p >= self.threshold else 0