# ml/xgb_model.py

import xgboost as xgb
import numpy as np

class XGBWrapper:
    def __init__(self, model_path="models/xgb_model.json"):
        self.model = xgb.Booster()
        self.model.load_model(model_path)

    def predict(self, features: np.ndarray) -> float:
        dmatrix = xgb.DMatrix(features)
        prob = self.model.predict(dmatrix)[0]
        return prob

def load_xgb_model():
    return XGBWrapper()