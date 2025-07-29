import pandas as pd
from sklearn.ensemble import RandomForestClassifier

class WalkForwardTester:
    def __init__(self, strategies, data, n_splits=3):
        self.strategies = strategies
        self.data = data
        self.n_splits = n_splits

    def split_data(self):
        split_size = len(self.data) // self.n_splits
        for i in range(self.n_splits):
            start = i * split_size
            end = start + split_size
            yield self.data[start:end]

    def retrain_model(self, data):
        X = data[['rsi', 'macd']]
        y = data['label']
        model = RandomForestClassifier()
        model.fit(X, y)
        return model
