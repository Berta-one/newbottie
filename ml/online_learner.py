# ml/online_learner.py
import os
import json
import time
import joblib
import logging
import numpy as np
from typing import Optional, Dict, Any
from sklearn.linear_model import SGDClassifier

log = logging.getLogger("OnlineLearner")

DEFAULT_FEATURES = ["close","rsi14","ret1","ema_fast","ema_slow","vol"]

class OnlineLearner:
    """
    Online binary classifier P(up next bar) using SGDClassifier.partial_fit.
    Starts cold if no model exists, then keeps adapting.
    """
    def __init__(
        self,
        model_path: str = "models/online_sgd.pkl",
        meta_path: str  = "models/online_sgd_meta.json",
        features: Optional[list] = None,
        learning_rate: float = 0.0005,
        alpha: float = 0.0001,
        random_state: int = 42,
    ):
        self.model_path = model_path
        self.meta_path  = meta_path
        self.features   = features or list(DEFAULT_FEATURES)
        self.classes_   = np.array([0, 1], dtype=int)
        self.model: Optional[SGDClassifier] = None
        self.last_save  = 0.0
        self._init_or_load(learning_rate, alpha, random_state)

    def _init_or_load(self, eta0, alpha, seed):
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                log.info(f"OnlineLearner loaded: {self.model_path}")
            except Exception as e:
                log.warning(f"OnlineLearner load failed; re-init: {e}")
                self.model = None
        if self.model is None:
            self.model = SGDClassifier(
                loss="log_loss",
                penalty="l2",
                alpha=alpha,
                learning_rate="constant",
                eta0=eta0,
                random_state=seed
            )
            # warm start with classes
            self.model.partial_fit(np.zeros((1, len(self.features))), np.array([0]), classes=self.classes_)
            log.info("OnlineLearner initialized cold.")

        meta = {"features": self.features, "created_at": time.time()}
        try:
            with open(self.meta_path, "w") as f:
                json.dump(meta, f, indent=2)
        except Exception:
            pass

    def feature_names(self):
        return self.features

    def vectorize(self, feats: Dict[str, Any]) -> np.ndarray:
        return np.array([[
            float(feats["close"][-1]),
            float(50.0 if np.isnan(feats["rsi14"][-1]) else feats["rsi14"][-1]),
            float(feats["ret1"][-1]),
            float(feats["ema_fast"][-1]),
            float(feats["ema_slow"][-1]),
            float(feats["vol"][-1]),
        ]], dtype=float)

    def predict_proba(self, X: np.ndarray) -> float:
        try:
            p = self.model.predict_proba(X)
            return float(p[0, 1])
        except Exception:
            # fallback via decision_function
            s = float(self.model.decision_function(X)[0])
            return 1.0 / (1.0 + np.exp(-s))

    def update(self, X: np.ndarray, y: np.ndarray):
        """
        Incremental learning on mini-batch. y ∈ {0,1}.
        """
        try:
            self.model.partial_fit(X, y, classes=self.classes_)
        finally:
            now = time.time()
            # persist at most every ~30s to avoid I/O thrash
            if now - self.last_save > 30.0:
                try:
                    joblib.dump(self.model, self.model_path)
                    self.last_save = now
                except Exception as e:
                    log.warning(f"OnlineLearner save failed: {e}")