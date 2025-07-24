import os
import argparse
from dotenv import load_dotenv
from diagnostic_tools import run_diagnostic
from relaxed_strategy import enhanced_strategy_check
from advanced_portfolio_manager import AdvancedPortfolioManager, Position
from datetime import datetime

# Import Advanced Market Intelligence
from advanced_market_intelligence import AdvancedMarketIntelligence

# Import SimplifiedMLStrategy for ML-enhanced strategy
from simplified_ml_strategy import SimplifiedMLStrategy

import json

# Load environment variables
load_dotenv()


def main():
    parser = argparse.ArgumentParser(description="Crypto Bot Diagnostic CLI")
    parser.add_argument("--diagnostic", action="store_true", help="Run full diagnostic")
    parser.add_argument(
        "--symbol", type=str, default="BTCUSDT", help="Symbol to analyze"
    )
    parser.add_argument(
        "--strategy",
        type=str,
        default="relaxed_strategy",
        help="Strategy module to use",
    )
    parser.add_argument(
        "--threshold", type=float, default=2.0, help="Breakout threshold for diagnostic"
    )
    parser.add_argument(
        "--portfolio", action="store_true", help="Show portfolio summary"
    )
    parser.add_argument(
        "--open-position", action="store_true", help="Open a new position"
    )
    parser.add_argument(
        "--close-position", type=str, help="Close a position by symbol_strategy"
    )

    # Advanced Market Intelligence options
    parser.add_argument(
        "--market-summary",
        action="store_true",
        help="Show advanced market intelligence summary",
    )
    parser.add_argument(
        "--save-market-analysis",
        action="store_true",
        help="Save advanced market analysis to file",
    )
    # ML-enhanced strategy option
    parser.add_argument(
        "--ml-strategy",
        action="store_true",
        help="Use ML-enhanced strategy for analysis",
    )
    args = parser.parse_args()

    # Portfolio manager instance (for demo, use 10000 capital)
    portfolio = AdvancedPortfolioManager(total_capital=10000)

    # Dummy Binance client for demonstration (replace with real client in production)
    class DummyBinanceClient:
        def get_klines(self, symbol, interval, limit=100):
            # Return dummy klines: [timestamp, open, high, low, close, volume, ...]
            return [
                [0, "65000", "65100", "64900", "65000", "500", 0, 0, 0, 0, 0, 0]
                for _ in range(limit)
            ]

    binance_client = DummyBinanceClient()
    market_intel = AdvancedMarketIntelligence(binance_client)

    # Initialize ML strategy
    ml_strategy = SimplifiedMLStrategy()

    if args.diagnostic:
        print("Running full diagnostic...")
        run_diagnostic(threshold=args.threshold)
    elif args.portfolio:
        print("Portfolio summary:")
        summary = portfolio.get_portfolio_summary()
        print(summary)
    elif args.open_position:
        # Example: open a position with dummy values
        print("Opening a new position...")
        symbol = args.symbol
        strategy = "ML_Enhanced"
        entry_price = 65000
        quantity = 0.01
        confidence = 0.8
        stop_loss = 64000
        take_profit = 67000
        portfolio.open_position(
            symbol, strategy, entry_price, quantity, confidence, stop_loss, take_profit
        )
        print("Position opened.")
    elif args.close_position:
        pos_key = args.close_position
        if pos_key in portfolio.positions:
            position = portfolio.positions[pos_key]
            exit_price = 66000
            reason = "Manual Close"
            result = portfolio.close_position(position, exit_price, reason)
            print(f"Closed: {result}")
        else:
            print(f"No such position: {pos_key}")
    elif args.market_summary:
        print("\n=== Advanced Market Intelligence Summary ===")
        summary = market_intel.get_market_summary()
        print(json.dumps(summary, indent=2, default=str))
    elif args.save_market_analysis:
        print("Saving advanced market analysis to file...")
        filename = market_intel.save_analysis()
        print(f"Market analysis saved to logs/{filename}")
    else:
        print(f"Running strategy check for {args.symbol} using {args.strategy}...")
        # Simulate klines for demonstration
        klines = [[0, "65000", "65100", "64900", "65000", "500"] for _ in range(120)]
        if args.ml_strategy:
            # Use ML-enhanced strategy
            ml_signal, ml_confidence, ml_probabilities = (
                ml_strategy.predict_market_direction(klines)
            )
            print(
                f"ML Strategy result: Signal={ml_signal}, Confidence={ml_confidence:.2%}, Probabilities={ml_probabilities}"
            )
        else:
            result = enhanced_strategy_check(klines)
            print(f"Strategy result: {result}")


if __name__ == "__main__":
    main()
