# ml/decision_engine.py

from ml.ensemble_model import EnsembleModel
import numpy as np

model = EnsembleModel()

def load_model_and_predict(features_dict: dict) -> str:
    features = np.array([
        features_dict["return_1h"],
        features_dict["return_24h"],
        features_dict["volatility"],
        features_dict["rsi"],
        features_dict["sentiment"]
    ]).reshape(1, -1)

    pred = model.predict(features)
    return "buy" if pred == 1 else "sell"