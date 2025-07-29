
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

# 👇 Added utility for ML/Quantum training datasets

def load_training_data(normalize: bool = True, csv_path: str = "sample_data/historical_data.csv"):
    """Load historical OHLCV data and return (X, y) numpy arrays.

    Parameters
    ----------
    normalize : bool, optional
        If ``True`` the features will be scaled to \[0, 1] using ``MinMaxScaler``.
    csv_path : str, optional
        Path to the CSV containing historical price data. Defaults to the bundled
        ``sample_data/historical_data.csv``.

    Returns
    -------
    Tuple[np.ndarray, np.ndarray]
        Feature matrix ``X`` and target vector ``y`` ready for training.
    """
    import numpy as np
    import pandas as pd
    from sklearn.preprocessing import MinMaxScaler

    df = pd.read_csv(csv_path)

    features = ["open", "high", "low", "close", "volume"]
    target_col = "label"

    # Derive binary target if not present (next-period up-move indicator)
    if target_col not in df.columns:
        df[target_col] = (df["close"].shift(-1) > df["close"]).astype(int)

    X = df[features].values[:-1]  # drop last row due to shift
    y = df[target_col].values[:-1]

    if normalize:
        scaler = MinMaxScaler()
        X = scaler.fit_transform(X)

    return X.astype(np.float32), y.astype(np.int32)