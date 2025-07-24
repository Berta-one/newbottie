#!/usr/bin/env python3
"""
Unified Portfolio Value Calculator
Ensures consistent portfolio calculations across all tabs
"""

from datetime import datetime


class UnifiedPortfolioCalculator:
    """Single source of truth for portfolio value calculations"""

    def __init__(self):
        self._cached_portfolio = {}
        self._cached_total_usd = 0.0
        self._cached_total_gbp = 0.0
        self._cache_timestamp = None
        self._gbp_rate = 0.79  # Default fallback

    def get_gbp_exchange_rate(self):
        """Get current GBP exchange rate with caching"""
        try:
            import requests

            response = requests.get(
                "https://api.exchangerate-api.com/v4/latest/USD", timeout=5
            )
            self._gbp_rate = response.json()["rates"]["GBP"]
            return self._gbp_rate
        except:
            return self._gbp_rate  # Use cached/fallback rate

    def calculate_portfolio_totals(self, portfolio_data):
        """
        Calculate consistent portfolio totals

        Args:
            portfolio_data: Dictionary of portfolio assets

        Returns:
            tuple: (total_usd, total_gbp, gbp_rate)
        """
        if not portfolio_data:
            return 0.0, 0.0, self._gbp_rate

        # Calculate total USD value
        total_usd = 0.0

        for asset, data in portfolio_data.items():
            if isinstance(data, dict):
                # Handle different data structures
                if "usd_value" in data:
                    total_usd += float(data["usd_value"])
                elif "value" in data and "price" in data and "balance" in data:
                    total_usd += float(data["balance"]) * float(data["price"])
                elif "market_value" in data:
                    total_usd += float(data["market_value"])
                elif "Value (USD)" in data:
                    # Handle DataFrame-like structure
                    usd_str = str(data["Value (USD)"]).replace("$", "").replace(",", "")
                    try:
                        total_usd += float(usd_str)
                    except:
                        continue

        # Get current GBP rate and calculate GBP total
        gbp_rate = self.get_gbp_exchange_rate()
        total_gbp = total_usd * gbp_rate

        # Cache results
        self._cached_total_usd = total_usd
        self._cached_total_gbp = total_gbp
        self._cache_timestamp = datetime.now()

        return total_usd, total_gbp, gbp_rate

    def get_portfolio_metrics(self, portfolio_data):
        """Get comprehensive portfolio metrics"""
        total_usd, total_gbp, gbp_rate = self.calculate_portfolio_totals(portfolio_data)

        return {
            "total_usd": total_usd,
            "total_gbp": total_gbp,
            "gbp_rate": gbp_rate,
            "asset_count": len(portfolio_data) if portfolio_data else 0,
            "largest_holding_pct": self._get_largest_holding_percentage(
                portfolio_data, total_usd
            ),
            "formatted_usd": f"${total_usd:,.2f}",
            "formatted_gbp": f"£{total_gbp:,.2f}",
        }

    def _get_largest_holding_percentage(self, portfolio_data, total_usd):
        """Calculate largest holding percentage"""
        if not portfolio_data or total_usd == 0:
            return 0.0

        max_value = 0.0
        for asset, data in portfolio_data.items():
            if isinstance(data, dict):
                if "usd_value" in data:
                    asset_value = float(data["usd_value"])
                elif "market_value" in data:
                    asset_value = float(data["market_value"])
                else:
                    continue

                if asset_value > max_value:
                    max_value = asset_value

        return (max_value / total_usd * 100) if total_usd > 0 else 0.0

    def format_portfolio_for_display(self, portfolio_data):
        """Format portfolio data for consistent display"""
        if not portfolio_data:
            return []

        total_usd, total_gbp, gbp_rate = self.calculate_portfolio_totals(portfolio_data)
        formatted_data = []

        for asset, data in portfolio_data.items():
            if isinstance(data, dict):
                # Extract values safely
                balance = float(data.get("balance", 0))
                price_usd = float(data.get("price_usd", data.get("price", 0)))
                usd_value = float(data.get("usd_value", balance * price_usd))
                change_24h = float(data.get("change_24h", 0))

                formatted_data.append(
                    {
                        "Asset": asset,
                        "Balance": f"{balance:.8f}".rstrip("0").rstrip("."),
                        "Price (USD)": f"${price_usd:.4f}",
                        "Value (USD)": f"${usd_value:.2f}",
                        "Value (GBP)": f"£{usd_value * gbp_rate:.2f}",
                        "24h Change": f"{change_24h:.2f}%",
                        "Percentage": (
                            f"{(usd_value / total_usd * 100):.1f}%"
                            if total_usd > 0
                            else "0.0%"
                        ),
                    }
                )

        return formatted_data


# Global calculator instance
portfolio_calculator = UnifiedPortfolioCalculator()


# Convenience functions for easy import
def get_portfolio_totals(portfolio_data):
    """Get portfolio totals using unified calculator"""
    return portfolio_calculator.calculate_portfolio_totals(portfolio_data)


def get_portfolio_metrics(portfolio_data):
    """Get portfolio metrics using unified calculator"""
    return portfolio_calculator.get_portfolio_metrics(portfolio_data)


def format_portfolio_display(portfolio_data):
    """Format portfolio for display using unified calculator"""
    return portfolio_calculator.format_portfolio_for_display(portfolio_data)


def debug_portfolio_values(portfolio_data, location="unknown"):
    """Debug portfolio value calculations"""
    print(f"\n=== PORTFOLIO DEBUG [{location}] ===")

    if not portfolio_data:
        print("❌ Portfolio data is empty")
        return 0.0

    total_debug = 0.0
    for asset, data in portfolio_data.items():
        if isinstance(data, dict):
            usd_value = data.get("usd_value", 0)
            print(f"{asset}: ${usd_value:.2f}")
            total_debug += float(usd_value)

    print(f"🔢 Total calculated: ${total_debug:.2f}")
    print("=" * 40)

    return total_debug
