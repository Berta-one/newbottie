# ml/ensemble_model.py
from typing import Optional, List
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