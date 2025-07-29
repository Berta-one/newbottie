
import pandas as pd

def load_csv(filepath):
    return pd.read_csv(filepath)

def save_model(model, path):
    import joblib
    joblib.dump(model, path)
