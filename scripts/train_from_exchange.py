# scripts/train_from_exchange.py
"""
Train a real ML classifier from live OHLCV pulled via CCXT (Binance by default).
Outputs: models/xgb_model.pkl (joblib), ready for api/app.py to load.

Environment variables (or CLI defaults):
  EXCHANGE_ID=binance
  TRAIN_SYMBOLS="BTC/USDT,ETH/USDT,BNB/USDT,ADA/USDT"
  TRAIN_TIMEFRAME=1h
  TRAIN_BARS=2000
  LABEL_HORIZON=12           # forward bars for label (e.g., 12 * 1h = 12 hours)
  LABEL_THRESHOLD_BP=15      # label=1 if forward return > +15 bps (0.15%)
  VAL_SPLIT=0.2              # last 20% time for validation
  MODEL_OUT=models/xgb_model.pkl
"""
import os
import time
import math
import joblib
import warnings
from typing import List, Dict, Any, Tuple

warnings.filterwarnings("ignore")

try:
    import ccxt
except Exception as e:
    raise RuntimeError(f"ccxt required: {e}")

import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.metrics import roc_auc_score, accuracy_score, precision_recall_fscore_support
from ml.feature_builder import build_window_features

# ----------------------------- Config ---------------------------------
EXCHANGE_ID         = os.getenv("EXCHANGE_ID", "binance").lower()
TRAIN_SYMBOLS_ENV   = os.getenv("TRAIN_SYMBOLS", os.getenv("TRADE_SYMBOLS", "BTC/USDT,ETH/USDT"))
TRAIN_SYMBOLS       = [s.strip().upper() for s in TRAIN_SYMBOLS_ENV.split(",") if s.strip()]
TRAIN_TIMEFRAME     = os.getenv("TRAIN_TIMEFRAME", "1h")
TRAIN_BARS          = int(os.getenv("TRAIN_BARS", "2000"))
LABEL_HORIZON       = int(os.getenv("LABEL_HORIZON", "12"))
LABEL_THRESHOLD_BP  = float(os.getenv("LABEL_THRESHOLD_BP", "15.0")) / 10000.0  # bps → fraction
VAL_SPLIT           = float(os.getenv("VAL_SPLIT", "0.2"))
MODEL_OUT           = os.getenv("MODEL_OUT", "models/xgb_model.pkl")

RATE_LIMIT_SLEEP    = float(os.getenv("RATE_LIMIT_SLEEP", "0.8"))  # seconds between symbol pulls

os.makedirs("models", exist_ok=True)

# ----------------------------- Helpers --------------------------------
def fetch_ohlcv_safe(ex, symbol: str, timeframe: str, limit: int) -> List[List[float]]:
    for _ in range(3):
        try:
            return ex.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit) or []
        except Exception as e:
            time.sleep(1.0)
    print(f"[WARN] fetch_ohlcv failed: {symbol} {timeframe}")
    return []

def build_dataset_for_symbol(ohlcv: List[List[float]], horizon: int, thr: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    Build features/labels for a single symbol.
    Label: 1 if forward return over `horizon` bars > thr, else 0.
    """
    if not ohlcv or len(ohlcv) < 60 + horizon + 1:
        return np.empty((0, 5)), np.empty((0, ))

    closes = [row[4] for row in ohlcv]
    X, y = [], []
    # we compute features at t, and label using closes[t+h] vs closes[t]
    last_idx = len(closes) - horizon - 1
    for t in range(60, last_idx):
        feats = build_window_features(closes, t)
        if feats is None:
            continue
        fwd = (closes[t + horizon] / closes[t]) - 1.0
        lab = 1 if fwd > thr else 0
        X.append(feats)
        y.append(lab)
    if not X:
        return np.empty((0, 5)), np.empty((0, ))
    return np.array(X, dtype=float), np.array(y, dtype=int)

# ----------------------------- Main -----------------------------------
def main():
    if EXCHANGE_ID not in ccxt.exchanges:
        raise RuntimeError(f"Exchange '{EXCHANGE_ID}' not supported in CCXT.")

    ex = getattr(ccxt, EXCHANGE_ID)({"enableRateLimit": True})
    ex.load_markets()
    print(f"[INFO] Loaded {len(ex.markets)} markets from {EXCHANGE_ID}")
    symbols = [s for s in TRAIN_SYMBOLS if s in ex.markets]
    if not symbols:
        raise RuntimeError("No valid TRAIN_SYMBOLS found on the exchange.")

    all_X, all_y = [], []

    for sym in symbols:
        print(f"[INFO] Pulling {sym} {TRAIN_TIMEFRAME} {TRAIN_BARS} bars …")
        data = fetch_ohlcv_safe(ex, sym, TRAIN_TIMEFRAME, TRAIN_BARS)
        if not data:
            continue
        X, y = build_dataset_for_symbol(data, LABEL_HORIZON, LABEL_THRESHOLD_BP)
        print(f"[INFO] {sym}: {X.shape[0]} samples")
        if X.shape[0] > 0:
            all_X.append(X)
            all_y.append(y)
        time.sleep(RATE_LIMIT_SLEEP)

    if not all_X:
        raise RuntimeError("No training samples built; check symbols/timeframe/bars.")

    X = np.vstack(all_X)
    y = np.concatenate(all_y)
    print(f"[INFO] Dataset: X={X.shape} y={y.shape} | pos_rate={y.mean():.3f}")

    # Time-based split: last VAL_SPLIT fraction for validation
    n = X.shape[0]
    split = int(n * (1.0 - VAL_SPLIT))
    X_tr, y_tr = X[:split], y[:split]
    X_va, y_va = X[split:], y[split:]

    # Model — compact, fast; early stopping on logloss
    clf = XGBClassifier(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        eval_metric="logloss",
        tree_method="hist",
        random_state=42,
        n_jobs=2,
    )
    clf.fit(
        X_tr, y_tr,
        eval_set=[(X_va, y_va)],
        verbose=False,
        early_stopping_rounds=30
    )

    # Metrics
    def metrics(Xm, ym, tag: str):
        p = clf.predict_proba(Xm)[:, 1]
        pred = (p >= 0.5).astype(int)
        auc = roc_auc_score(ym, p)
        acc = accuracy_score(ym, pred)
        pr, rc, f1, _ = precision_recall_fscore_support(ym, pred, average="binary", zero_division=0)
        print(f"[METRICS] {tag}: AUC={auc:.3f} ACC={acc:.3f} P={pr:.3f} R={rc:.3f} F1={f1:.3f}")

    metrics(X_tr, y_tr, "train")
    metrics(X_va, y_va, "valid")

    joblib.dump(clf, MODEL_OUT)
    print(f"[OK] Saved model → {MODEL_OUT}")

if __name__ == "__main__":
    main()