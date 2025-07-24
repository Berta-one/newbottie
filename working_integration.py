#!/usr/bin/env python3
# working_integration.py - Working example of ML integration

import sys
import os
import random
from datetime import datetime
import logging

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def create_realistic_klines():
    """Create realistic sample klines data"""
    klines = []
    base_price = 45000

    for i in range(120):
        # Add some trend and volatility
        trend = 0.001 * i  # Slight upward trend
        volatility = random.uniform(0.98, 1.02)

        open_price = base_price * volatility
        high_price = open_price * random.uniform(1.0, 1.005)
        low_price = open_price * random.uniform(0.995, 1.0)
        close_price = open_price * random.uniform(0.998, 1.002) * (1 + trend)
        volume = random.uniform(100, 1000)

        # Format as strings (like real Binance data)
        kline = [
            i * 60000,  # timestamp
            f"{open_price:.2f}",
            f"{high_price:.2f}",
            f"{low_price:.2f}",
            f"{close_price:.2f}",
            f"{volume:.2f}",
            (i + 1) * 60000,  # close_time
            f"{volume * close_price:.2f}",  # quote_volume
            random.randint(50, 200),  # trades
            f"{volume * 0.6:.2f}",  # taker_buy_base
            f"{volume * 0.6 * close_price:.2f}",  # taker_buy_quote
            "0",  # ignore
        ]
        klines.append(kline)
        base_price = close_price

    return klines


class EnhancedTradingBot:
    """Enhanced trading bot with ML integration"""

    def __init__(self):
        self.MIN_CONFIDENCE = 0.65
        self.ml_strategy = None
        self.initialize_ml()

    def initialize_ml(self):
        """Initialize ML strategy"""
        try:
            from simplified_ml_strategy import SimplifiedMLStrategy

            self.ml_strategy = SimplifiedMLStrategy()
            logging.info("✅ ML Strategy initialized successfully")
        except ImportError as e:
            logging.error(f"❌ Failed to import ML strategy: {e}")
            logging.info(
                "💡 Make sure simplified_ml_strategy.py is in the same directory"
            )
            self.ml_strategy = None
        except Exception as e:
            logging.error(f"❌ Failed to initialize ML strategy: {e}")
            self.ml_strategy = None

    def basic_strategy(self, klines):
        """Simulate your existing basic strategy"""
        # This is a simplified version of your existing strategy
        # Replace with your actual strategy logic

        if len(klines) < 20:
            return "HOLD", 0.5

        # Convert to floats for analysis
        closes = [float(k[4]) for k in klines]
        volumes = [float(k[5]) for k in klines]

        # Simple momentum check
        current_price = closes[-1]
        price_20_ago = closes[-20]
        price_change = (current_price - price_20_ago) / price_20_ago

        # Simple volume check
        current_volume = volumes[-1]
        avg_volume = sum(volumes[-20:]) / 20
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1

        # Determine signal
        if price_change > 0.05 and volume_ratio > 1.5:  # 5% price move with volume
            return "BUY_LONG", 0.7
        elif price_change < -0.05 and volume_ratio > 1.5:  # 5% price drop with volume
            return "BUY_SHORT", 0.7
        else:
            return "HOLD", 0.5

    def analyze_opportunity(self, symbol, klines):
        """Analyze trading opportunity using ML + basic strategy"""

        # Get basic strategy signal
        basic_signal, basic_confidence = self.basic_strategy(klines)

        # Get ML signal if available
        ml_signal, ml_confidence, ml_probabilities = (
            "HOLD",
            0.5,
            {"buy": 0.33, "sell": 0.33, "hold": 0.34},
        )

        if self.ml_strategy:
            try:
                ml_signal, ml_confidence, ml_probabilities = (
                    self.ml_strategy.predict_market_direction(klines)
                )
            except Exception as e:
                logging.warning(f"ML prediction failed for {symbol}: {e}")

        # Combine signals
        final_signal, final_confidence = self.combine_signals(
            ml_signal, ml_confidence, basic_signal, basic_confidence
        )

        return {
            "symbol": symbol,
            "final_signal": final_signal,
            "final_confidence": final_confidence,
            "ml_signal": ml_signal,
            "ml_confidence": ml_confidence,
            "basic_signal": basic_signal,
            "basic_confidence": basic_confidence,
            "ml_probabilities": ml_probabilities,
            "timestamp": datetime.now(),
            "meets_threshold": final_confidence > self.MIN_CONFIDENCE,
        }

    def combine_signals(self, ml_signal, ml_confidence, basic_signal, basic_confidence):
        """Combine ML and basic signals using weighted ensemble"""

        # Convert signals to numeric scores
        signal_scores = {"BUY_LONG": 1, "BUY_SHORT": -1, "HOLD": 0}

        ml_score = signal_scores.get(ml_signal, 0)
        basic_score = signal_scores.get(basic_signal, 0)

        # Weighted combination
        # If ML is available, weight it more heavily
        if self.ml_strategy:
            ml_weight = 0.7
            basic_weight = 0.3
        else:
            ml_weight = 0.0
            basic_weight = 1.0

        combined_score = (ml_score * ml_confidence * ml_weight) + (
            basic_score * basic_confidence * basic_weight
        )
        combined_confidence = (ml_confidence * ml_weight) + (
            basic_confidence * basic_weight
        )

        # Determine final signal
        if combined_score > 0.3:
            return "BUY_LONG", combined_confidence
        elif combined_score < -0.3:
            return "BUY_SHORT", combined_confidence
        else:
            return "HOLD", combined_confidence

    def scan_opportunities(self, symbols):
        """Scan multiple symbols for trading opportunities"""
        opportunities = []

        for symbol in symbols:
            try:
                # Generate sample klines (replace with actual API call)
                klines = create_realistic_klines()

                # Analyze opportunity
                opportunity = self.analyze_opportunity(symbol, klines)

                if opportunity["meets_threshold"]:
                    opportunities.append(opportunity)
                    logging.info(
                        f"✅ Opportunity found: {symbol} - {opportunity['final_signal']} ({opportunity['final_confidence']:.2%})"
                    )
                else:
                    logging.info(
                        f"⚠️  Below threshold: {symbol} - {opportunity['final_signal']} ({opportunity['final_confidence']:.2%})"
                    )

            except Exception as e:
                logging.error(f"❌ Error analyzing {symbol}: {e}")

        return opportunities

    def display_results(self, opportunities):
        """Display scan results"""
        print("\n" + "=" * 80)
        print("📊 TRADING OPPORTUNITIES FOUND")
        print("=" * 80)

        if not opportunities:
            print("❌ No opportunities found meeting confidence threshold")
            return

        print(f"✅ Found {len(opportunities)} opportunities:")
        print()

        for i, opp in enumerate(opportunities, 1):
            print(f"🎯 Opportunity #{i}:")
            print(f"   Symbol: {opp['symbol']}")
            print(f"   Final Signal: {opp['final_signal']}")
            print(f"   Final Confidence: {opp['final_confidence']:.2%}")
            print(
                f"   ML Signal: {opp['ml_signal']} (Conf: {opp['ml_confidence']:.2%})"
            )
            print(
                f"   Basic Signal: {opp['basic_signal']} (Conf: {opp['basic_confidence']:.2%})"
            )
            print(
                f"   ML Probabilities: Buy: {opp['ml_probabilities']['buy']:.2%}, "
                f"Sell: {opp['ml_probabilities']['sell']:.2%}, Hold: {opp['ml_probabilities']['hold']:.2%}"
            )
            print()

        print("=" * 80)


def main():
    """Main test function"""
    print("🚀 Testing Enhanced Trading Bot with ML Integration")
    print("=" * 80)

    # Initialize bot
    bot = EnhancedTradingBot()

    # Test symbols
    test_symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "SOLUSDT", "BNBUSDT"]

    print(f"🔍 Scanning {len(test_symbols)} symbols...")
    print(f"📊 Minimum confidence threshold: {bot.MIN_CONFIDENCE:.0%}")

    # Scan for opportunities
    opportunities = bot.scan_opportunities(test_symbols)

    # Display results
    bot.display_results(opportunities)

    # Show ML performance if available
    if bot.ml_strategy:
        print("\n🧠 ML PERFORMANCE METRICS:")
        print("=" * 40)
        metrics = bot.ml_strategy.get_performance_metrics()
        print(f"Total Predictions: {metrics['total_predictions']}")
        print(f"Correct Predictions: {metrics['correct_predictions']}")
        print(f"Accuracy: {metrics['accuracy']:.2%}")

        print("\n🔍 ML FEATURE IMPORTANCE:")
        print("=" * 40)
        importance = bot.ml_strategy.get_feature_importance()
        for feature, weight in importance[:5]:  # Top 5 features
            print(f"{feature}: {weight:.3f}")

    print("\n✅ Test completed successfully!")
    print("🎯 You can now integrate this enhanced system with your actual bot!")


if __name__ == "__main__":
    main()
