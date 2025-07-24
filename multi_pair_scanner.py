#!/usr/bin/env python3
"""
Complete Multi-Pair Cryptocurrency Scanner - multi_pair_scanner.py
================================================================

Comprehensive multi-pair scanning engine as specified in GitHub Copilot instructions.

Features:
- Scan ALL USDT pairs with minimum volume filtering
- Maintain curated list of quality crypto pairs across categories
- Accept custom symbol lists from environment variables
- Analyze multiple pairs concurrently using ThreadPoolExecutor
- Rank opportunities by combined score (confidence + volume + category)
- Filter trading signals based on minimum confidence and volume thresholds
- Display formatted results in tables with comprehensive data
- Save scan results to timestamped JSON files
"""

import os
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics

try:
    from binance.client import Client
    from binance.exceptions import BinanceAPIException

    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False
    Client = None

from strategy import check_breakout_enhanced, get_strategy_confidence
from logger import log_scan


class CryptoPairScanner:
    """
    Comprehensive multi-pair cryptocurrency scanner with advanced filtering and ranking
    """

    def __init__(self, binance_client: Optional[Client] = None):
        self.client = binance_client
        self.scan_results_dir = "logs"
        self.ensure_logs_directory()

        # Quality pairs with risk multipliers by category
        self.QUALITY_PAIRS = {
            "MAJOR": [
                {"symbol": "BTCUSDT", "base_qty": 0.001, "risk_multiplier": 1.0},
                {"symbol": "ETHUSDT", "base_qty": 0.01, "risk_multiplier": 1.0},
                {"symbol": "BNBUSDT", "base_qty": 0.1, "risk_multiplier": 1.0},
            ],
            "LARGE_CAP": [
                {"symbol": "ADAUSDT", "base_qty": 10, "risk_multiplier": 0.8},
                {"symbol": "SOLUSDT", "base_qty": 0.1, "risk_multiplier": 0.8},
                {"symbol": "XRPUSDT", "base_qty": 10, "risk_multiplier": 0.8},
                {"symbol": "DOTUSDT", "base_qty": 1, "risk_multiplier": 0.8},
                {"symbol": "AVAXUSDT", "base_qty": 0.5, "risk_multiplier": 0.8},
                {"symbol": "MATICUSDT", "base_qty": 10, "risk_multiplier": 0.8},
            ],
            "MID_CAP": [
                {"symbol": "LINKUSDT", "base_qty": 1, "risk_multiplier": 0.7},
                {"symbol": "UNIUSDT", "base_qty": 1, "risk_multiplier": 0.7},
                {"symbol": "LTCUSDT", "base_qty": 0.1, "risk_multiplier": 0.7},
                {"symbol": "ATOMUSDT", "base_qty": 1, "risk_multiplier": 0.7},
                {"symbol": "NEARUSDT", "base_qty": 1, "risk_multiplier": 0.7},
            ],
            "DEFI": [
                {"symbol": "AAVEUSDT", "base_qty": 0.1, "risk_multiplier": 0.6},
                {"symbol": "COMPUSDT", "base_qty": 0.1, "risk_multiplier": 0.6},
                {"symbol": "MKRUSDT", "base_qty": 0.01, "risk_multiplier": 0.6},
            ],
            "GAMING": [
                {"symbol": "SANDUSDT", "base_qty": 10, "risk_multiplier": 0.5},
                {"symbol": "MANAUSDT", "base_qty": 10, "risk_multiplier": 0.5},
            ],
            "MEME": [
                {"symbol": "DOGEUSDT", "base_qty": 100, "risk_multiplier": 0.4},
                {"symbol": "SHIBUSDT", "base_qty": 1000000, "risk_multiplier": 0.4},
            ],
        }

        # Exclude leveraged tokens and other problematic pairs
        self.EXCLUDED_PATTERNS = [
            "UP",
            "DOWN",
            "BEAR",
            "BULL",
            "2L",
            "3L",
            "2S",
            "3S",
            "BUSD",
            "TUSD",
            "PAX",
            "USDC",  # Stablecoins
        ]

    def ensure_logs_directory(self):
        """Ensure logs directory exists"""
        os.makedirs(self.scan_results_dir, exist_ok=True)

    def get_all_usdt_pairs(
        self, min_volume_24h: float = 1000000, exclude_leveraged: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get all USDT trading pairs with volume filtering

        Args:
            min_volume_24h: Minimum 24h volume in USDT
            exclude_leveraged: Whether to exclude leveraged tokens

        Returns:
            List of trading pair dictionaries
        """
        if not self.client:
            print("⚠️ Binance client not available, using mock data")
            return self._get_mock_pairs()

        try:
            print("📡 Fetching all USDT pairs from Binance...")

            # Get exchange info
            exchange_info = self.client.get_exchange_info()
            active_symbols = [
                s["symbol"]
                for s in exchange_info["symbols"]
                if s["status"] == "TRADING" and s["symbol"].endswith("USDT")
            ]

            # Get 24h ticker data
            tickers = self.client.get_ticker()
            ticker_dict = {t["symbol"]: t for t in tickers}

            pairs = []
            for symbol in active_symbols:
                ticker = ticker_dict.get(symbol)
                if not ticker:
                    continue

                # Volume filtering
                volume_24h = float(ticker["quoteVolume"])
                if volume_24h < min_volume_24h:
                    continue

                # Exclude leveraged tokens if requested
                if exclude_leveraged:
                    base_asset = symbol.replace("USDT", "")
                    if any(pattern in base_asset for pattern in self.EXCLUDED_PATTERNS):
                        continue

                # Estimate base quantity (target ~$35 position)
                price = float(ticker["lastPrice"])
                base_qty = 35 / price if price > 0 else 0.001

                pair_info = {
                    "symbol": symbol,
                    "base_qty": base_qty,
                    "risk_multiplier": 0.6,  # Default for unknown pairs
                    "category": "OTHER",
                    "price": price,
                    "volume_24h": volume_24h,
                    "change_24h": float(ticker["priceChangePercent"]),
                }

                pairs.append(pair_info)

            print(f"✅ Found {len(pairs)} eligible USDT pairs")
            return sorted(pairs, key=lambda x: x["volume_24h"], reverse=True)

        except Exception as e:
            print(f"❌ Error fetching USDT pairs: {e}")
            return self._get_mock_pairs()

    def get_selected_pairs(self) -> List[Dict[str, Any]]:
        """
        Get curated list of quality cryptocurrency pairs

        Returns:
            List of selected trading pairs with categories
        """
        pairs = []

        for category, category_pairs in self.QUALITY_PAIRS.items():
            for pair in category_pairs:
                pair_info = pair.copy()
                pair_info["category"] = category

                # Get current price and volume if client available
                if self.client:
                    try:
                        ticker = self.client.get_ticker(symbol=pair["symbol"])
                        pair_info["price"] = float(ticker["lastPrice"])
                        pair_info["volume_24h"] = float(ticker["quoteVolume"])
                        pair_info["change_24h"] = float(ticker["priceChangePercent"])
                    except Exception as e:
                        print(f"⚠️ Error getting data for {pair['symbol']}: {e}")
                        pair_info.update(
                            {
                                "price": 50000 if "BTC" in pair["symbol"] else 100,
                                "volume_24h": 10000000,
                                "change_24h": 0.0,
                            }
                        )
                else:
                    # Mock data for testing
                    pair_info.update(
                        {
                            "price": 50000 if "BTC" in pair["symbol"] else 100,
                            "volume_24h": 10000000,
                            "change_24h": 0.0,
                        }
                    )

                pairs.append(pair_info)

        return pairs

    def get_custom_pairs(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """
        Get custom symbol list from environment variables or input

        Args:
            symbols: List of symbol strings

        Returns:
            List of custom trading pairs
        """
        pairs = []

        for symbol in symbols:
            symbol = symbol.strip().upper()
            if not symbol.endswith("USDT"):
                symbol += "USDT"

            # Default pair structure
            pair_info = {
                "symbol": symbol,
                "base_qty": 0.001,
                "risk_multiplier": 0.7,
                "category": "CUSTOM",
            }

            # Get live data if client available
            if self.client:
                try:
                    ticker = self.client.get_ticker(symbol=symbol)
                    price = float(ticker["lastPrice"])
                    pair_info.update(
                        {
                            "price": price,
                            "volume_24h": float(ticker["quoteVolume"]),
                            "change_24h": float(ticker["priceChangePercent"]),
                            "base_qty": 35 / price if price > 0 else 0.001,
                        }
                    )
                except Exception as e:
                    print(f"⚠️ Error getting data for {symbol}: {e}")
                    pair_info.update(
                        {"price": 100, "volume_24h": 1000000, "change_24h": 0.0}
                    )
            else:
                pair_info.update(
                    {"price": 100, "volume_24h": 1000000, "change_24h": 0.0}
                )

            pairs.append(pair_info)

        return pairs

    def analyze_single_pair(self, pair_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a single trading pair for breakout opportunities

        Args:
            pair_info: Trading pair information dictionary

        Returns:
            Analysis result dictionary
        """
        symbol = pair_info["symbol"]

        try:
            # Get klines data (120 1-minute candles for 2 hours)
            if self.client:
                klines = self.client.get_klines(
                    symbol=symbol, interval=Client.KLINE_INTERVAL_1MINUTE, limit=120
                )
            else:
                # Generate mock klines for testing
                klines = self._generate_mock_klines(pair_info["price"])

            if len(klines) < 120:
                return {
                    "symbol": symbol,
                    "signal": "HOLD",
                    "confidence": 0.0,
                    "error": "Insufficient data",
                }

            # Run enhanced breakout strategy
            signal = check_breakout_enhanced(klines)
            confidence = get_strategy_confidence(klines)

            # Calculate additional metrics
            prices = [float(k[4]) for k in klines]
            volumes = [float(k[5]) for k in klines]

            # Volume analysis
            avg_volume = statistics.mean(volumes[:-10])
            recent_volume = statistics.mean(volumes[-10:])
            volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1.0

            # Price change analysis
            price_change_2h = ((prices[-1] - prices[0]) / prices[0]) * 100

            # Volatility calculation
            returns = [
                (prices[i] - prices[i - 1]) / prices[i - 1] * 100
                for i in range(1, len(prices))
            ]
            volatility = statistics.stdev(returns) if len(returns) > 1 else 0.0

            # Combined score calculation
            category_score = pair_info.get("risk_multiplier", 0.5)
            volume_score = min(volume_ratio / 2.0, 1.0)
            confidence_score = confidence

            combined_score = (
                confidence_score * 0.4 + volume_score * 0.3 + category_score * 0.3
            )

            result = {
                "symbol": symbol,
                "signal": signal,
                "confidence": confidence,
                "price": pair_info.get("price", prices[-1]),
                "change_24h": pair_info.get("change_24h", 0.0),
                "change_2h": price_change_2h,
                "volume_24h": pair_info.get("volume_24h", 0),
                "volume_ratio": volume_ratio,
                "volatility": volatility,
                "category": pair_info.get("category", "UNKNOWN"),
                "risk_multiplier": pair_info.get("risk_multiplier", 0.5),
                "base_qty": pair_info.get("base_qty", 0.001),
                "combined_score": combined_score,
                "analysis_time": datetime.now().isoformat(),
            }

            return result

        except Exception as e:
            print(f"❌ Error analyzing {symbol}: {e}")
            return {
                "symbol": symbol,
                "signal": "HOLD",
                "confidence": 0.0,
                "error": str(e),
            }

    def scan_multiple_pairs(
        self, pairs_list: List[Dict[str, Any]], max_workers: int = 8
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple pairs concurrently using ThreadPoolExecutor

        Args:
            pairs_list: List of trading pairs to analyze
            max_workers: Maximum number of concurrent workers

        Returns:
            List of analysis results
        """
        print(f"🔍 Scanning {len(pairs_list)} pairs with {max_workers} workers...")

        results = []
        completed_count = 0

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all analysis tasks
            future_to_pair = {
                executor.submit(self.analyze_single_pair, pair): pair
                for pair in pairs_list
            }

            # Collect results as they complete
            for future in as_completed(future_to_pair):
                pair = future_to_pair[future]

                try:
                    result = future.result(timeout=30)  # 30 second timeout per pair
                    results.append(result)
                    completed_count += 1

                    # Progress indicator
                    if completed_count % 10 == 0 or completed_count == len(pairs_list):
                        print(
                            f"📊 Progress: {completed_count}/{len(pairs_list)} pairs analyzed"
                        )

                except Exception as e:
                    print(f"⚠️ Error analyzing {pair.get('symbol', 'unknown')}: {e}")
                    results.append(
                        {
                            "symbol": pair.get("symbol", "unknown"),
                            "signal": "HOLD",
                            "confidence": 0.0,
                            "error": str(e),
                        }
                    )

        print(f"✅ Scan completed: {len(results)} pairs analyzed")
        return results

    def filter_opportunities(
        self,
        opportunities: List[Dict[str, Any]],
        min_confidence: float = 0.6,
        max_positions: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Filter and rank trading opportunities

        Args:
            opportunities: List of analysis results
            min_confidence: Minimum confidence threshold
            max_positions: Maximum number of positions to return

        Returns:
            Filtered and ranked opportunities
        """
        # Filter by confidence and valid signals
        valid_opportunities = [
            opp
            for opp in opportunities
            if (
                opp.get("confidence", 0) >= min_confidence
                and opp.get("signal", "HOLD") != "HOLD"
                and "error" not in opp
            )
        ]

        # Sort by combined score
        ranked_opportunities = sorted(
            valid_opportunities, key=lambda x: x.get("combined_score", 0), reverse=True
        )

        # Limit to max positions
        return ranked_opportunities[:max_positions]

    def display_scan_results(
        self,
        opportunities: List[Dict[str, Any]],
        show_all: bool = False,
        top_n: int = 10,
    ) -> None:
        """
        Display formatted scan results in tables

        Args:
            opportunities: List of trading opportunities
            show_all: Whether to show all results or just opportunities
            top_n: Number of top results to display
        """
        if not opportunities:
            print("📭 No opportunities found in scan")
            return

        # Filter opportunities vs all results
        if not show_all:
            display_ops = [
                op for op in opportunities if op.get("signal", "HOLD") != "HOLD"
            ]
        else:
            display_ops = opportunities

        if not display_ops:
            print("📭 No trading opportunities found")
            return

        # Limit results
        display_ops = display_ops[:top_n]

        print(f"\n🎯 Trading Opportunities Found: {len(display_ops)}")
        print("=" * 120)

        # Table header
        header = f"{'Symbol':<12} {'Signal':<10} {'Confidence':<11} {'Price':<12} {'24h %':<8} {'2h %':<8} {'Vol Ratio':<10} {'Category':<10} {'Score':<8}"
        print(header)
        print("-" * 120)

        # Display each opportunity
        for opp in display_ops:
            symbol = opp.get("symbol", "N/A")[:11]
            signal = opp.get("signal", "HOLD")[:9]
            confidence = f"{opp.get('confidence', 0):.1%}"
            price = f"${opp.get('price', 0):.6f}"[:11]
            change_24h = f"{opp.get('change_24h', 0):+.1f}%"
            change_2h = f"{opp.get('change_2h', 0):+.1f}%"
            volume_ratio = f"{opp.get('volume_ratio', 1):.1f}x"
            category = opp.get("category", "N/A")[:9]
            score = f"{opp.get('combined_score', 0):.2f}"

            row = f"{symbol:<12} {signal:<10} {confidence:<11} {price:<12} {change_24h:<8} {change_2h:<8} {volume_ratio:<10} {category:<10} {score:<8}"
            print(row)

        print("=" * 120)

    def save_scan_results(
        self, opportunities: List[Dict[str, Any]], filename: Optional[str] = None
    ) -> str:
        """
        Save scan results to timestamped JSON file

        Args:
            opportunities: List of analysis results
            filename: Optional custom filename

        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"scan_results_{timestamp}.json"

        filepath = os.path.join(self.scan_results_dir, filename)

        # Prepare data for saving
        scan_data = {
            "scan_time": datetime.now().isoformat(),
            "total_pairs_scanned": len(opportunities),
            "opportunities_found": len(
                [op for op in opportunities if op.get("signal", "HOLD") != "HOLD"]
            ),
            "scan_summary": {
                "avg_confidence": statistics.mean(
                    [op.get("confidence", 0) for op in opportunities]
                ),
                "max_confidence": (
                    max([op.get("confidence", 0) for op in opportunities])
                    if opportunities
                    else 0
                ),
                "signals_by_type": self._count_signals(opportunities),
            },
            "opportunities": opportunities,
        }

        try:
            with open(filepath, "w") as f:
                json.dump(scan_data, f, indent=2, default=str)

            # Also save as latest scan for dashboard
            latest_filepath = os.path.join(self.scan_results_dir, "latest_scan.json")
            with open(latest_filepath, "w") as f:
                json.dump(scan_data, f, indent=2, default=str)

            print(f"💾 Scan results saved: {filepath}")

            # Log scan to logger
            log_scan(scan_data)

            return filepath

        except Exception as e:
            print(f"❌ Error saving scan results: {e}")
            return ""

    def _count_signals(self, opportunities: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count signals by type"""
        signal_counts = {"BUY_LONG": 0, "BUY_SHORT": 0, "HOLD": 0}

        for opp in opportunities:
            signal = opp.get("signal", "HOLD")
            if signal in signal_counts:
                signal_counts[signal] += 1

        return signal_counts

    def _get_mock_pairs(self) -> List[Dict[str, Any]]:
        """Generate mock pairs for testing when Binance client unavailable"""
        import random

        mock_symbols = [
            "BTCUSDT",
            "ETHUSDT",
            "BNBUSDT",
            "ADAUSDT",
            "SOLUSDT",
            "XRPUSDT",
            "DOTUSDT",
            "AVAXUSDT",
            "MATICUSDT",
            "LINKUSDT",
        ]

        pairs = []
        for symbol in mock_symbols:
            base_price = random.uniform(0.1, 50000)
            pairs.append(
                {
                    "symbol": symbol,
                    "base_qty": 35 / base_price,
                    "risk_multiplier": 0.7,
                    "category": "MOCK",
                    "price": base_price,
                    "volume_24h": random.uniform(1000000, 100000000),
                    "change_24h": random.uniform(-10, 10),
                }
            )

        return pairs

    def _generate_mock_klines(self, base_price: float) -> List[List]:
        """Generate mock klines data for testing"""
        import random

        klines = []
        current_price = base_price

        for i in range(120):
            # Simulate price movement
            change = random.uniform(-0.01, 0.01)
            current_price *= 1 + change

            # Simulate volume
            volume = random.uniform(100, 1000)

            # Kline format: [open_time, open, high, low, close, volume, ...]
            kline = [
                int(time.time() * 1000) - (120 - i) * 60000,  # timestamp
                str(current_price),  # open
                str(current_price * 1.002),  # high
                str(current_price * 0.998),  # low
                str(current_price),  # close
                str(volume),  # volume
                0,
                0,
                0,
                0,
                0,
                0,  # other fields
            ]

            klines.append(kline)

        return klines


# Convenience functions for different scan modes
def scan_all_pairs(
    scanner: CryptoPairScanner,
    min_volume: float = 1000000,
    min_confidence: float = 0.6,
    max_workers: int = 8,
) -> List[Dict[str, Any]]:
    """Scan all USDT pairs"""
    pairs = scanner.get_all_usdt_pairs(min_volume_24h=min_volume)
    opportunities = scanner.scan_multiple_pairs(pairs, max_workers=max_workers)
    return scanner.filter_opportunities(opportunities, min_confidence=min_confidence)


def scan_selected_pairs(
    scanner: CryptoPairScanner, min_confidence: float = 0.6, max_workers: int = 8
) -> List[Dict[str, Any]]:
    """Scan curated quality pairs"""
    pairs = scanner.get_selected_pairs()
    opportunities = scanner.scan_multiple_pairs(pairs, max_workers=max_workers)
    return scanner.filter_opportunities(opportunities, min_confidence=min_confidence)


def scan_custom_pairs(
    scanner: CryptoPairScanner,
    symbols: List[str],
    min_confidence: float = 0.6,
    max_workers: int = 8,
) -> List[Dict[str, Any]]:
    """Scan custom symbol list"""
    pairs = scanner.get_custom_pairs(symbols)
    opportunities = scanner.scan_multiple_pairs(pairs, max_workers=max_workers)
    return scanner.filter_opportunities(opportunities, min_confidence=min_confidence)


# Main execution function
def main():
    """Main scanner execution for testing"""
    print("🚀 Multi-Pair Cryptocurrency Scanner")
    print("=" * 50)

    # Initialize scanner
    try:
        if BINANCE_AVAILABLE:
            from binance.client import Client

            api_key = os.getenv("BINANCE_API_KEY")
            api_secret = os.getenv("BINANCE_API_SECRET")

            if api_key and api_secret:
                client = Client(api_key, api_secret)
                if os.getenv("USE_TESTNET", "false").lower() == "true":
                    client.API_URL = "https://testnet.binance.vision/api"
                scanner = CryptoPairScanner(client)
                print("✅ Connected to Binance API")
            else:
                scanner = CryptoPairScanner()
                print("⚠️ No API credentials, using mock data")
        else:
            scanner = CryptoPairScanner()
            print("⚠️ Binance library not available, using mock data")

    except Exception as e:
        scanner = CryptoPairScanner()
        print(f"⚠️ Error initializing Binance client: {e}")

    # Get scan mode from environment
    scan_mode = os.getenv("SCAN_MODE", "SELECTED").upper()
    min_confidence = float(os.getenv("MIN_CONFIDENCE", 0.65))
    max_workers = int(os.getenv("MAX_WORKERS", 8))

    print(f"🎯 Scan Mode: {scan_mode}")
    print(f"📊 Min Confidence: {min_confidence:.1%}")
    print(f"🔄 Max Workers: {max_workers}")
    print()

    # Execute scan based on mode
    start_time = time.time()

    if scan_mode == "ALL":
        opportunities = scan_all_pairs(
            scanner, min_confidence=min_confidence, max_workers=max_workers
        )
    elif scan_mode == "CUSTOM":
        custom_symbols = os.getenv("CUSTOM_SYMBOLS", "BTCUSDT,ETHUSDT,ADAUSDT").split(
            ","
        )
        opportunities = scan_custom_pairs(
            scanner,
            custom_symbols,
            min_confidence=min_confidence,
            max_workers=max_workers,
        )
    else:  # SELECTED
        opportunities = scan_selected_pairs(
            scanner, min_confidence=min_confidence, max_workers=max_workers
        )

    scan_time = time.time() - start_time

    # Display results
    print(f"⏱️ Scan completed in {scan_time:.2f} seconds")
    scanner.display_scan_results(opportunities, show_all=False, top_n=10)

    # Save results
    if opportunities:
        saved_file = scanner.save_scan_results(opportunities)
        print(f"💾 Results saved to: {saved_file}")

    return opportunities


if __name__ == "__main__":
    main()
