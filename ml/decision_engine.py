# ml/decision_engine.py

import numpy as np

class DecisionEngine:
    """
    Combines ML model outputs and rule-based logic to make final trading decisions.
    """

    def __init__(self, ensemble_model=None, risk_threshold=0.3):
        self.ensemble_model = ensemble_model
        self.risk_threshold = risk_threshold

    def decide(self, features):
        """
        Make a decision based on input features.
        
        Parameters:
            features (dict): Dictionary with all necessary features (volatility, RSI, sentiment, etc.)

        Returns:
            str: One of ['buy', 'sell', 'hold']
            dict: Metadata explaining the decision
        """

        # Extract basic indicators
        rsi = features.get("rsi", 50)
        sentiment = features.get("sentiment_score", 0)
        model_probs = features.get("model_outputs", {})

        # Rule: Avoid trading in high risk conditions
        if features.get("volatility", 0) > self.risk_threshold:
            return "hold", {"reason": "Volatility too high"}

        # Combine model outputs
        buy_votes = 0
        sell_votes = 0

        for name, prob in model_probs.items():
            if prob > 0.6:
                buy_votes += 1
            elif prob < 0.4:
                sell_votes += 1

        vote_result = "hold"
        if buy_votes > sell_votes:
            vote_result = "buy"
        elif sell_votes > buy_votes:
            vote_result = "sell"

        # Combine with technical indicators
        if rsi > 70:
            vote_result = "sell"
        elif rsi < 30:
            vote_result = "buy"

        explanation = {
            "model_votes": model_probs,
            "rsi": rsi,
            "sentiment": sentiment,
            "final_decision": vote_result,
        }

        return vote_result, explanation