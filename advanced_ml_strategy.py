 -*- coding: utf-8 -*-
"""
advanced_ml_strategy.py
=======================
Implements hybrid strategy combining Machine Learning with Technical Analysis.
Replaces TA-Lib with pandas-based indicators for Railway compatibility.
"""

from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Dict, Any
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler


class AdvancedMLStrategy:
    """Hybrid ML + Technical Analysis trading strategy."""

    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.trained = False

    # -------------------------------
    # Technical Indicator Calculations
    # -------------------------------
    def calculate_rsi(self, close: pd.Series, period: int = 14) -> pd.Series:
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def calculate_macd(
        self, close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> pd.DataFrame:
        ema_fast = close.ewm(span=fast, adjust=False).mean()
        ema_slow = close.ewm(span=slow, adjust=False).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        return pd.DataFrame({"MACD": macd, "Signal": signal_line})

    def calculate_moving_average(self, close: pd.Series, period: int = 20) -> pd.Series:
        return close.rolling(window=period).mean()

    # -------------------------------
    # Feature Engineering
    # -------------------------------
    def generate_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df["RSI"] = self.calculate_rsi(df["close"])
        macd = self.calculate_macd(df["close"])
        df["MACD"] = macd["MACD"]
        df["Signal"] = macd["Signal"]
        df["MA20"] = self.calculate_moving_average(df["close"], 20)
        df["MA50"] = self.calculate_moving_average(df["close"], 50)
        df.dropna(inplace=True)
        return df

    # -------------------------------
    # ML Training
    # -------------------------------
    def train(self, df: pd.DataFrame):
        df = self.generate_features(df)
        X = df[["RSI", "MACD", "Signal", "MA20", "MA50"]].values
        y = np.where(df["close"].shift(-1) > df["close"], 1, 0)  # 1 = BUY, 0 = SELL
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        self.trained = True

    # -------------------------------
    # Prediction
    # -------------------------------
    def predict_signal(self, latest_data: Dict[str, Any]) -> str:
        if not self.trained:
            return "HOLD"
        features = np.array(
            [
                latest_data["RSI"],
                latest_data["MACD"],
                latest_data["Signal"],
                latest_data["MA20"],
                latest_data["MA50"],
            ]
        ).reshape(1, -1)
        features_scaled = self.scaler.transform(features)
        prediction = self.model.predict(features_scaled)[0]
        return "BUY" if prediction == 1 else "SELL"

