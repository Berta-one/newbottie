# ml/ensemble_model.py

import numpy as np

class EnsembleModel:
    """
    Combines predictions from multiple ML models using weighted averaging.
    """

    def __init__(self, models=None, weights=None):
        """
        Parameters:
            models (dict): Dictionary of model_name -> model_object
            weights (dict): Dictionary of model_name -> float weight
        """
        self.models = models if models else {}
        self.weights = weights if weights else {name: 1.0 for name in self.models}

    def predict_proba(self, features):
        """
        Run predictions from all models and compute a weighted average.
        
        Returns:
            dict: {model_name: probability}
            float: final ensemble probability
        """
        predictions = {}
        total_weight = sum(self.weights.values())
        ensemble_prob = 0.0

        for name, model in self.models.items():
            try:
                proba = model.predict_proba([features])[0][1]  # Binary classification: proba of class 1
                weight = self.weights.get(name, 1.0)
                ensemble_prob += proba * weight
                predictions[name] = proba
            except Exception as e:
                predictions[name] = 0.5  # fallback neutral probability
                print(f"[Warning] Model {name} failed: {e}")

        ensemble_prob /= total_weight if total_weight > 0 else 1

        return predictions, ensemble_prob

    def add_model(self, name, model, weight=1.0):
        self.models[name] = model
        self.weights[name] = weight