# scripts/train_from_exchange.py
"""
Train a real classifier from Binance OHLCV and save:
  - models/xgb_model.pkl      (joblib)
  - models/xgb_meta.json      (threshold, metrics, config)

ENV (override as needed):
  EXCHANGE_ID=binance
  TRAIN_SYMBOLS="BTC/USDT,ETH/USDT,BNB/USDT,ADA/USDT"
  TRAIN_TIMEFRAME=1h
  TRAIN_BARS=2000
  LABEL_HORIZON=12
  LABEL_THRESHOLD_BP=15
  VAL_SPLIT=0.2
  RATE_LIMIT_SLEEP=0.8
  MODEL_OUT=models/xgb_model.pkl
  MODEL_META=models/xgb_meta.json
  THRESH_TARGET=f1           # or 'youden' (tpr-fpr) or 'precision@recall>=X' (e.g. precision@recall>=0.60)
"""
import os, time, json, warnings
from typing import List, Tuple
warnings.filterwarnings("ignore")

import numpy as np
from xgboost import XGBClassifier
from sklearn.metrics import (
    roc_auc_score, accuracy_score, precision_recall_fscore_support,
    precision_recall_curve, roc_curve
)

try:
    import ccxt
except Exception as e:
    raise RuntimeError(f"ccxt required: {e}")

from ml.feature_builder import build_window_features
import joblib

# ------------------ config ------------------
EXCHANGE_ID         = os.getenv("EXCHANGE_ID", "binance").lower()
TRAIN_SYMBOLS_ENV   = os.getenv("TRAIN_SYMBOLS", os.getenv("TRADE_SYMBOLS", "BTC/USDT,ETH/USDT"))
TRAIN_SYMBOLS       = [s.strip().upper() for s in TRAIN_SYMBOLS_ENV.split(",") if s.strip()]
TRAIN_TIMEFRAME     = os.getenv("TRAIN_TIMEFRAME", "1h")
TRAIN_BARS          = int(os.getenv("TRAIN_BARS", "2000"))
LABEL_HORIZON       = int(os.getenv("LABEL_HORIZON", "12"))
LABEL_THRESHOLD_BP  = float(os.getenv("LABEL_THRESHOLD_BP", "15.0")) / 10000.0
VAL_SPLIT           = float(os.getenv("VAL_SPLIT", "0.2"))
RATE_LIMIT_SLEEP    = float(os.getenv("RATE_LIMIT_SLEEP", "0.8"))
MODEL_OUT           = os.getenv("MODEL_OUT", "models/xgb_model.pkl")
MODEL_META          = os.getenv("MODEL_META", "models/xgb_meta.json")
THRESH_TARGET       = os.getenv("THRESH_TARGET", "f1").strip().lower()

os.makedirs("models", exist_ok=True)

# ------------------ data helpers ------------------
def fetch_ohlcv_safe(ex, symbol: str, timeframe: str, limit: int):
    for _ in range(3):
        try:
            data = ex.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
            return data or []
        except Exception:
            time.sleep(1.0)
    print(f"[WARN] fetch_ohlcv failed: {symbol} {timeframe}")
    return []

def build_dataset_for_symbol(ohlcv: List[List[float]], horizon: int, thr: float) -> Tuple[np.ndarray, np.ndarray]:
    if not ohlcv or len(ohlcv) < 60 + horizon + 1:
        return np.empty((0, 5)), np.empty((0,))
    closes = [row[4] for row in ohlcv]
    X, y = [], []
    last_idx = len(closes) - horizon - 1
    for t in range(60, last_idx):
        feats = build_window_features(closes, t)
        if feats is None:
            continue
        fwd = (closes[t + horizon] / closes[t]) - 1.0
        lab = 1 if fwd > thr else 0
        X.append(feats); y.append(lab)
    if not X:
        return np.empty((0, 5)), np.empty((0,))
    return np.array(X, float), np.array(y, int)

# ------------------ threshold selection ------------------
def select_threshold(y_true: np.ndarray, y_prob: np.ndarray, target: str) -> float:
    target = target.lower()
    if target.startswith("precision@"):
        # precision@recall>=X (e.g. precision@recall>=0.60)
        try:
            want = float(target.split(">=")[1])
        except Exception:
            want = 0.6
        prec, rec, thr = precision_recall_curve(y_true, y_prob)
        best_thr = 0.5
        best_p = 0.0
        for p, r, t in zip(prec[:-1], rec[:-1], thr):
            if r >= want and p > best_p:
                best_p, best_thr = p, float(t)
        return best_thr
    elif target == "youden":
        # maximize TPR - FPR
        fpr, tpr, thr = roc_curve(y_true, y_prob)
        j = tpr - fpr
        idx = int(np.argmax(j))
        return float(thr[idx])
    else:
        # default: maximize F1 on discrete thresholds grid
        grid = np.linspace(0.1, 0.9, 17)
        best_thr, best_f1 = 0.5, -1.0
        for t in grid:
            pred = (y_prob >= t).astype(int)
            p, r, f1, _ = precision_recall_fscore_support(y_true, pred, average="binary", zero_division=0)
            if f1 > best_f1:
                best_f1, best_thr = f1, float(t)
        return best_thr

# ------------------ main ------------------
def main():
    if EXCHANGE_ID not in ccxt.exchanges:
        raise RuntimeError(f"Exchange '{EXCHANGE_ID}' not found in CCXT")
    ex = getattr(ccxt, EXCHANGE_ID)({"enableRateLimit": True})
    ex.load_markets()
    symbols = [s for s in TRAIN_SYMBOLS if s in ex.markets]
    if not symbols:
        raise RuntimeError("No valid TRAIN_SYMBOLS found on exchange")

    import numpy as np
    allX, ally = [], []
    for sym in symbols:
        print(f"[INFO] Pulling {sym} {TRAIN_TIMEFRAME} x {TRAIN_BARS}")
        data = fetch_ohlcv_safe(ex, sym, TRAIN_TIMEFRAME, TRAIN_BARS)
        X, y = build_dataset_for_symbol(data, LABEL_HORIZON, LABEL_THRESHOLD_BP)
        print(f"[INFO] {sym}: samples={X.shape[0]}")
        if X.shape[0] > 0:
            allX.append(X); ally.append(y)
        time.sleep(RATE_LIMIT_SLEEP)

    if not allX:
        raise RuntimeError("No training samples built")

    X = np.vstack(allX); y = np.concatenate(ally)
    n = X.shape[0]; split = int(n * (1.0 - VAL_SPLIT))
    Xtr, ytr = X[:split], y[:split]; Xva, yva = X[split:], y[split:]

    # class weights to handle imbalance
    pos = ytr.mean()
    scale_pos_weight = (1.0 - pos) / max(pos, 1e-6)

    clf = XGBClassifier(
        n_estimators=500,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        eval_metric="logloss",
        tree_method="hist",
        random_state=42,
        n_jobs=2,
        scale_pos_weight=scale_pos_weight
    )
    clf.fit(Xtr, ytr, eval_set=[(Xva, yva)], verbose=False, early_stopping_rounds=50)

    def report(Xm, ym, tag):
        p = clf.predict_proba(Xm)[:, 1]
        pred = (p >= 0.5).astype(int)
        auc = roc_auc_score(ym, p)
        from sklearn.metrics import accuracy_score, precision_recall_fscore_support
        acc = accuracy_score(ym, pred)
        pr, rc, f1, _ = precision_recall_fscore_support(ym, pred, average="binary", zero_division=0)
        print(f"[METRICS] {tag}: AUC={auc:.3f} ACC={acc:.3f} P={pr:.3f} R={rc:.3f} F1={f1:.3f}")
        return p

    p_tr = report(Xtr, ytr, "train")
    p_va = report(Xva, yva, "valid")

    # optimal threshold on validation
    thr = select_threshold(yva, p_va, THRESH_TARGET)
    print(f"[OK] Selected optimal threshold={thr:.3f} using target='{THRESH_TARGET}'")

    joblib.dump(clf, MODEL_OUT)
    meta = {
        "trained_on_symbols": symbols,
        "timeframe": TRAIN_TIMEFRAME,
        "bars": TRAIN_BARS,
        "label_horizon": LABEL_HORIZON,
        "label_threshold_bps": int(LABEL_THRESHOLD_BP * 10000),
        "val_split": VAL_SPLIT,
        "optimal_threshold": thr,
        "feature_count": X.shape[1],
        "threshold_rule": THRESH_TARGET
    }
    with open(MODEL_META, "w") as f:
        json.dump(meta, f, indent=2)

    print(f"[OK] Saved model → {MODEL_OUT}")
    print(f"[OK] Saved meta  → {MODEL_META}")

if __name__ == "__main__":
    main()