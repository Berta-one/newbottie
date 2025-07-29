# monitoring/performance_metrics.py

import time
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

class PerformanceTracker:
    def __init__(self, model_name):
        self.model_name = model_name
        self.logs = []

    def track(self, y_true, y_pred, start_time, end_time):
        metrics = {
            "model": self.model_name,
            "accuracy": accuracy_score(y_true, y_pred),
            "precision": precision_score(y_true, y_pred, zero_division=0),
            "recall": recall_score(y_true, y_pred, zero_division=0),
            "f1": f1_score(y_true, y_pred, zero_division=0),
            "latency": round(end_time - start_time, 3)
        }
        self.logs.append(metrics)
        return metrics

    def summary(self):
        return self.logs