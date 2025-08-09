# scripts/make_stub_models.py
"""
Create loadable stub models so the bot starts without trained artifacts.

Run:
  python scripts/make_stub_models.py

Outputs:
  models/lstm_model.pkl
  models/xgboost_model.pkl
"""
from __future__ import annotations

import os
from pathlib import Path

import joblib


class StubModel:
    """
    Minimal model with predict()/predict_proba() so pipelines don’t break.
    """
    def predict(self, X):
        # Always "BUY" to keep demo deterministic
        n = len(X)
        return ["BUY"] * n

    def predict_proba(self, X):
        # 3-class probs [SELL, BUY, HOLD]
        n = len(X)
        return [[0.15, 0.7, 0.15] for _ in range(n)]


def main() -> None:
    Path("models").mkdir(parents=True, exist_ok=True)
    m = StubModel()
    joblib.dump(m, "models/lstm_model.pkl")
    joblib.dump(m, "models/xgboost_model.pkl")
    print("Wrote models/lstm_model.pkl and models/xgboost_model.pkl")


if __name__ == "__main__":
    main()