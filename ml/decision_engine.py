# ml/decision_engine.py

import numpy as np
import logging

class DecisionEngine:
    def __init__(self, lstm_model, xgb_model, sentiment_model=None, threshold_buy=0.6, threshold_sell=0.4):
        self.lstm_model = lstm_model
        self.xgb_model = xgb_model
        self.sentiment_model = sentiment_model
        self.threshold_buy = threshold_buy
        self.threshold_sell = threshold_sell
        self.logger = logging.getLogger(__name__)

    def get_sentiment_score(self, market_context):
        if self.sentiment_model is None:
            return 0.0
        try:
            return self.sentiment_model.score(market_context)
        except Exception as e:
            self.logger.warning(f"Sentiment scoring failed: {e}")
            return 0.0

    def generate_signal(self, market_data, market_context=None):
        # Predict with LSTM
        try:
            lstm_input = market_data[-50:].reshape(1, 50, -1)
            lstm_score = float(self.lstm_model.predict(lstm_input)[0][0])
        except Exception as e:
            self.logger.error(f"LSTM prediction failed: {e}")
            lstm_score = 0.5

        # Predict with XGBoost
        try:
            xgb_input = market_data[-1].reshape(1, -1)
            xgb_score = float(self.xgb_model.predict_proba(xgb_input)[0][1])
        except Exception as e:
            self.logger.error(f"XGBoost prediction failed: {e}")
            xgb_score = 0.5

        # Sentiment Score
        sentiment_score = self.get_sentiment_score(market_context)

        # Weighted decision
        combined_score = 0.4 * lstm_score + 0.4 * xgb_score + 0.2 * (sentiment_score + 1) / 2  # Normalize to [0,1]

        self.logger.info(f"LSTM: {lstm_score:.2f}, XGB: {xgb_score:.2f}, Sentiment: {sentiment_score:.2f}, Combined: {combined_score:.2f}")

        if combined_score >= self.threshold_buy:
            return "buy"
        elif combined_score <= self.threshold_sell:
            return "sell"
        else:
            return "hold"