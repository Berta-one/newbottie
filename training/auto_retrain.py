import time
import os
from training.train_lstm import train_lstm
from training.train_xgb import train_xgb

INTERVAL_HOURS = 24

def retrain_all_models():
    print("[Auto Retrain] Starting LSTM retraining...")
    train_lstm()
    print("[Auto Retrain] LSTM done.")

    print("[Auto Retrain] Starting XGBoost retraining...")
    train_xgb()
    print("[Auto Retrain] XGBoost done.")

if __name__ == "__main__":
    while True:
        retrain_all_models()
        print(f"[Auto Retrain] Sleeping for {INTERVAL_HOURS} hours...")
        time.sleep(INTERVAL_HOURS * 3600)
