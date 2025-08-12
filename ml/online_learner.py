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

DEFAULT_FEATURES = ["close","rsi14","ret1","ema_fast","ema_slow","vol","quantum_prob"]

class OnlineLearner:
    """
    Online binary classifier P(up next bar) using SGDClassifier.partial_fit.
    Now includes quantum probability as a feature for enhanced learning.
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
        include_quantum: bool = None,
    ):
        self.model_path = model_path
        self.meta_path  = meta_path
        
        # Check if quantum features should be included
        if include_quantum is None:
            include_quantum = os.getenv("QUANTUM_AS_ML_FEATURE", "1").lower() in ("1", "true", "yes")
        self.include_quantum = include_quantum
        
        # Set features based on quantum inclusion
        if features is None:
            if self.include_quantum:
                features = ["close", "rsi14", "ret1", "ema_fast", "ema_slow", "vol", "quantum_prob"]
            else:
                features = ["close", "rsi14", "ret1", "ema_fast", "ema_slow", "vol"]
        
        self.features = features
        self.classes_ = np.array([0, 1], dtype=int)
        self.model: Optional[SGDClassifier] = None
        self.last_save = 0.0
        self._init_or_load(learning_rate, alpha, random_state)

    def _init_or_load(self, eta0, alpha, seed):
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                log.info(f"OnlineLearner loaded: {self.model_path} (quantum_features={self.include_quantum})")
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
            dummy_features = np.zeros((1, len(self.features)))
            self.model.partial_fit(dummy_features, np.array([0]), classes=self.classes_)
            log.info(f"OnlineLearner initialized cold (quantum_features={self.include_quantum}).")

        # Save/update metadata
        meta = {
            "features": self.features,
            "include_quantum": self.include_quantum,
            "feature_count": len(self.features),
            "created_at": time.time()
        }
        try:
            with open(self.meta_path, "w") as f:
                json.dump(meta, f, indent=2)
        except Exception:
            pass

    def feature_names(self):
        return self.features

    def vectorize(self, feats: Dict[str, Any]) -> np.ndarray:
        """
        Convert feature dictionary to numpy array.
        Now includes quantum probability as a feature when enabled.
        """
        # Base features (always included)
        feature_vector = [
            float(feats["close"][-1]),
            float(50.0 if np.isnan(feats["rsi14"][-1]) else feats["rsi14"][-1]),
            float(feats["ret1"][-1]),
            float(feats["ema_fast"][-1]),
            float(feats["ema_slow"][-1]),
            float(feats["vol"][-1]),
        ]
        
        # Add quantum probability if enabled
        if self.include_quantum:
            # Get quantum probability from features, default to neutral 0.5
            q_prob = feats.get("quantum_prob", 0.5)
            if q_prob is None:
                q_prob = 0.5
            feature_vector.append(float(q_prob))
        
        return np.array([feature_vector], dtype=float)

    def predict_proba(self, X: np.ndarray) -> float:
        """
        Predict probability of upward price movement.
        Now enhanced with quantum-aware features.
        """
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
        Now learns from quantum-enhanced feature vectors.
        """
        try:
            self.model.partial_fit(X, y, classes=self.classes_)
            
            # Log learning progress occasionally
            if len(y) >= 10:  # Only log for meaningful batches
                accuracy = self.model.score(X, y)
                log.info(f"OnlineLearner batch update: size={len(y)}, accuracy={accuracy:.3f}, features={len(self.features)}")
                
        except Exception as e:
            log.error(f"OnlineLearner update failed: {e}")
        finally:
            now = time.time()
            # persist at most every ~30s to avoid I/O thrash
            if now - self.last_save > 30.0:
                try:
                    joblib.dump(self.model, self.model_path)
                    self.last_save = now
                    log.debug(f"OnlineLearner saved to {self.model_path}")
                except Exception as e:
                    log.warning(f"OnlineLearner save failed: {e}")

    def get_feature_importance(self) -> Dict[str, float]:
        """
        Get feature importance scores from the trained model.
        Useful for understanding which features (including quantum) are most predictive.
        """
        if self.model is None or not hasattr(self.model, 'coef_'):
            return {}
        
        try:
            # Get coefficients (feature weights)
            coefs = self.model.coef_[0] if len(self.model.coef_.shape) > 1 else self.model.coef_
            
            # Create feature importance dict
            importance = {}
            for i, feature_name in enumerate(self.features):
                if i < len(coefs):
                    importance[feature_name] = float(abs(coefs[i]))
            
            return importance
        except Exception as e:
            log.error(f"Error getting feature importance: {e}")
            return {}

    def get_model_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive model statistics for monitoring.
        """
        stats = {
            "features": self.features,
            "feature_count": len(self.features),
            "include_quantum": self.include_quantum,
            "model_path": self.model_path,
            "last_save": self.last_save,
        }
        
        # Add feature importance if available
        importance = self.get_feature_importance()
        if importance:
            stats["feature_importance"] = importance
            
            # Highlight quantum importance if included
            if self.include_quantum and "quantum_prob" in importance:
                stats["quantum_importance"] = importance["quantum_prob"]
                
                # Rank quantum among all features
                sorted_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)
                quantum_rank = next((i+1 for i, (name, _) in enumerate(sorted_features) 
                                   if name == "quantum_prob"), None)
                stats["quantum_feature_rank"] = quantum_rank
        
        return stats