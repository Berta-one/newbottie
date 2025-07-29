# ml/lstm_model.py

import numpy as np
from keras.models import load_model

class LSTMWrapper:
    def __init__(self, model_path="models/lstm_model.h5"):
        self.model = load_model(model_path)

    def predict(self, features: np.ndarray) -> float:
        features = features.reshape((features.shape[0], 1, features.shape[1]))  # [batch, timesteps, features]
        prob = self.model.predict(features)[0][0]
        return prob

def load_lstm_model():
    return LSTMWrapper()