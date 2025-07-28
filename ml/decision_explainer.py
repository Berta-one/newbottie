
def explain_decision(lstm_score, xgb_score, sentiment_score, final_signal):
    reasons = []

    if lstm_score > 0.6:
        reasons.append(f"LSTM predicts trend with confidence {lstm_score:.2f}")
    if xgb_score > 0.6:
        reasons.append(f"XGBoost suggests breakout (score: {xgb_score:.2f})")
    if sentiment_score > 0.2:
        reasons.append(f"News sentiment is positive ({sentiment_score:.2f})")
    elif sentiment_score < -0.2:
        reasons.append(f"News sentiment is negative ({sentiment_score:.2f})")

    reasons.append(f"Final signal: {final_signal.upper()}")
    return reasons
