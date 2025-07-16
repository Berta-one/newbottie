import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import classification_report
import joblib
import talib
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class AdvancedMLStrategy:
    def __init__(self):
        self.models = {
            'short_term': None,
            'medium_term': None,
            'long_term': None
        }
        self.scalers = {
            'short_term': RobustScaler(),
            'medium_term': RobustScaler(),
            'long_term': RobustScaler()
        }
        self.feature_names = []
        self.is_trained = False
    # ...existing code for all feature extraction and ML logic...
    # (Paste the full class code you provided here)

class EnsembleModel:
    def __init__(self, models):
        self.models = models
    def predict_proba(self, X):
        predictions = np.array([model.predict_proba(X) for model in self.models])
        return np.mean(predictions, axis=0)
    def get_feature_importance(self):
        importances = [model.feature_importances_ for model in self.models if hasattr(model, 'feature_importances_')]
        if importances:
            return np.mean(importances, axis=0)
        return np.zeros(len(self.models[0].feature_importances_))

def get_ml_enhanced_signal(klines, timeframe='short_term'):
    global ml_strategy
    if 'ml_strategy' not in globals():
        ml_strategy = AdvancedMLStrategy()
    return ml_strategy.predict_market_direction(klines, timeframe)
