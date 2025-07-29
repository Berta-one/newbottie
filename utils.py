
import pandas as pd

def load_csv(filepath):
    return pd.read_csv(filepath)

def save_model(model, path):
    import joblib
    joblib.dump(model, path)
# quantum/metrics_logger.py

import json
from datetime import datetime

def log_metrics(metrics_dict, log_file="logs/metrics.jsonl"):
    with open(log_file, "a") as f:
        metrics_dict["timestamp"] = datetime.utcnow().isoformat()
        f.write(json.dumps(metrics_dict) + "\n")