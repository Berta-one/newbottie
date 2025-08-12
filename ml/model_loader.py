# ml/model_loader.py
import os
import joblib

class SafeModel:
    """Wrapper that guarantees predict_proba; if missing, synthesizes it."""
    def __init__(self, model):
        self._m = model

    def predict_proba(self, X):
        m = self._m
        if hasattr(m, "predict_proba"):
            return m.predict_proba(X)
        # synthesize from predict() in [0,1] or {-1,0,1}
        y = m.predict(X)
        out = []
        for v in y:
            if isinstance(v, (list, tuple)) and len(v) == 2:
                # already proba-like
                out.append([float(v[0]), float(v[1])])
            else:
                # map scalar to [sell, buy] two-class
                try:
                    fv = float(v)
                except Exception:
                    fv = 0.0
                # clamp to [-1,1] then map to [0,1]
                fv = max(-1.0, min(1.0, fv))
                p_buy = (fv + 1.0) / 2.0
                out.append([1.0 - p_buy, p_buy])
        return out

def load_model(path: str):
    path = os.path.abspath(path)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model file not found: {path}")
    model = joblib.load(path)
    return SafeModel(model)