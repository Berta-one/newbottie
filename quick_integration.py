 -*- coding: utf-8 -*-
# quick_integration.py - Integrate simplified ML with your existing bot

# 1. Add this to your existing scanner_main.py imports
from simplified_ml_strategy import SimplifiedMLStrategy


# 2. Initialize the ML strategy in your bot class
class MultiPairTradingBot:
    def __init__(self, client):
        self.client = client
        self.ml_strategy = SimplifiedMLStrategy()  # Add this line
        # ... rest of your existing init code

    def get_trading_opportunities(self):
        """Enhanced version of your existing method"""
        opportunities = []

        # Your existing scanning logic here...
        pairs_to_scan = self.get_pairs_based_on_mode()

        for pair_info in pairs_to_scan:
            try:
                symbol = pair_info["symbol"]

                # Get market data
                klines = self.client.get_klines(symbol, "1m", 120)

                # ENHANCEMENT: Use ML prediction instead of just basic strategy
                ml_signal, ml_confidence, ml_probabilities = (
                    self.ml_strategy.predict_market_direction(klines)
                )

                # Your existing strategy for comparison
                basic_signal = check_breakout_enhanced(klines)
                basic_confidence = get_strategy_confidence(klines)

                # Combine signals (ensemble approach)
                final_signal, final_confidence = self.combine_signals(
                    ml_signal, ml_confidence, basic_signal, basic_confidence
                )

                if final_signal != "HOLD" and final_confidence > MIN_CONFIDENCE:
                    opportunity = {
                        "symbol": symbol,
                        "decision": final_signal,
                        "confidence": final_confidence,
                        "ml_signal": ml_signal,
                        "ml_confidence": ml_confidence,
                        "basic_signal": basic_signal,
                        "basic_confidence": basic_confidence,
                        "ml_probabilities": ml_probabilities,
                        "timestamp": datetime.now(),
                    }
                    opportunities.append(opportunity)

            except Exception as e:
                logging.warning(f"Error analyzing {symbol}: {e}")
                continue

        return opportunities

    def combine_signals(self, ml_signal, ml_confidence, basic_signal, basic_confidence):
        """Combine ML and basic signals for better accuracy"""

        # Convert signals to numeric scores
        signal_scores = {"BUY_LONG": 1, "BUY_SHORT": -1, "HOLD": 0}

        ml_score = signal_scores.get(ml_signal, 0)
        basic_score = signal_scores.get(basic_signal, 0)

        # Weighted combination (60% ML, 40% basic)
        combined_score = (ml_score * ml_confidence * 0.6) + (
            basic_score * basic_confidence * 0.4
        )
        combined_confidence = (ml_confidence * 0.6) + (basic_confidence * 0.4)

        # Determine final signal
        if combined_score > 0.3:
            return "BUY_LONG", combined_confidence
        elif combined_score < -0.3:
            return "BUY_SHORT", combined_confidence
        else:
            return "HOLD", combined_confidence

    def log_ml_performance(self, symbol, predicted_signal, actual_result=None):
        """Log ML performance for continuous improvement"""
        if actual_result:
            self.ml_strategy.update_performance(actual_result, predicted_signal)

            # Log performance metrics periodically
            if self.ml_strategy.performance_metrics["total_predictions"] % 50 == 0:
                metrics = self.ml_strategy.get_performance_metrics()
                logging.info(
                    f"ðŸ§  ML Performance: Accuracy: {metrics['accuracy']:.2%}, "
                    f"Total Predictions: {metrics['total_predictions']}"
                )


# 3. Enhanced dashboard integration
def create_ml_dashboard():
    """Create a simple ML dashboard with existing dependencies"""
    import streamlit as st
    import pandas as pd
    import plotly.graph_objects as go

    st.title("ðŸ§  ML-Enhanced Trading Bot")

    # Initialize ML strategy
    if "ml_strategy" not in st.session_state:
        st.session_state.ml_strategy = SimplifiedMLStrategy()

    ml_strategy = st.session_state.ml_strategy

    # Performance metrics
    metrics = ml_strategy.get_performance_metrics()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("ðŸŽ¯ ML Accuracy", f"{metrics['accuracy']:.1%}")
    with col2:
        st.metric("ðŸ“Š Total Predictions", metrics["total_predictions"])
    with col3:
        st.metric("âœ… Correct Predictions", metrics["correct_predictions"])

    # Feature importance
    st.subheader("ðŸ” Feature Importance")
    importance_data = ml_strategy.get_feature_importance()

    features = [item[0] for item in importance_data]
    weights = [item[1] for item in importance_data]

    fig = go.Figure(data=[go.Bar(x=weights, y=features, orientation="h")])
    fig.update_layout(title="ML Feature Weights", height=400)
    st.plotly_chart(fig, use_container_width=True)

    # Recent predictions
    st.subheader("ðŸ”® Recent Predictions")
    if ml_strategy.prediction_history:
        recent_predictions = ml_strategy.prediction_history[-10:]  # Last 10

        pred_data = {
            "Time": [p["timestamp"].strftime("%H:%M:%S") for p in recent_predictions],
            "Signal": [p["signal"] for p in recent_predictions],
            "Confidence": [f"{p['confidence']:.2%}" for p in recent_predictions],
        }

        st.dataframe(pd.DataFrame(pred_data))
    else:
        st.info("No predictions yet. Start the bot to see ML predictions!")


# 4. Quick test function
def test_ml_integration():
    """Test the ML integration with sample data"""
    print("ðŸ§ª Testing ML Integration...")

    # Create sample klines data
    import random

    sample_klines = []
    base_price = 45000

    for i in range(120):
        # Generate realistic OHLCV data
        open_price = base_price + random.uniform(-100, 100)
        high_price = open_price + random.uniform(0, 200)
        low_price = open_price - random.uniform(0, 200)
        close_price = open_price + random.uniform(-150, 150)
        volume = random.uniform(100, 1000)

        kline = [
            i * 60000,  # timestamp
            open_price,
            high_price,
            low_price,
            close_price,
            volume,
            (i + 1) * 60000,
            volume * close_price,
            100,
            volume * 0.6,
            volume * 0.6 * close_price,
            0,
        ]
        sample_klines.append(kline)
        base_price = close_price

    # Test ML prediction
    ml_strategy = SimplifiedMLStrategy()
    signal, confidence, probabilities = ml_strategy.predict_market_direction(
        sample_klines
    )

    print(f"âœ… ML Signal: {signal}")
    print(f"âœ… Confidence: {confidence:.2%}")
    print(f"âœ… Probabilities: {probabilities}")
    print("âœ… ML Integration test passed!")

    return True


if __name__ == "__main__":
    test_ml_integration()

