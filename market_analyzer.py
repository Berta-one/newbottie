 -*- coding: utf-8 -*-
"""
market_analyzer.py - Enhanced Market Analysis
============================================
Add these methods to your existing MarketAnalyzer class or replace the entire class.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any
import requests
from datetime import datetime, timedelta


class MarketAnalyzer:
    """Enhanced Market Analysis with all required methods"""

    def __init__(self, client=None):
        self.client = client
        self.cache = {}
        self.cache_duration = 60  # seconds

    def get_klines(self, symbol: str, interval: str = "1h", limit: int = 100) -> List:
        """Get klines data from Binance"""
        try:
            if self.client:
                return self.client.get_klines(
                    symbol=symbol, interval=interval, limit=limit
                )
            else:
                # Fallback to public API
                url = f"https://api.binance.com/api/v3/klines"
                params = {"symbol": symbol, "interval": interval, "limit": limit}
                response = requests.get(url, params=params)
                return response.json()
        except Exception as e:
            print(f"Error getting klines for {symbol}: {e}")
            return []

    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI indicator"""
        if len(prices) < period + 1:
            return 50.0  # Default neutral RSI

        prices = np.array(prices)
        deltas = np.diff(prices)

        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return float(rsi)

    def get_latest_rsi(self, symbol: str, period: int = 14) -> float:
        """Get latest RSI for a symbol"""
        try:
            klines = self.get_klines(symbol, "1h", period + 20)
            if not klines:
                return 50.0

            closes = [float(k[4]) for k in klines]  # Close prices
            return self.calculate_rsi(closes, period)

        except Exception as e:
            print(f"Error calculating RSI for {symbol}: {e}")
            return 50.0

    def get_latest_momentum(self, symbol: str, period: int = 10) -> float:
        """Get latest momentum for a symbol"""
        try:
            klines = self.get_klines(symbol, "1h", period + 5)
            if len(klines) < period:
                return 0.0

            closes = [float(k[4]) for k in klines]
            momentum = (closes[-1] - closes[-period]) / closes[-period] * 100
            return float(momentum)

        except Exception as e:
            print(f"Error calculating momentum for {symbol}: {e}")
            return 0.0

    def get_volatility(self, symbol: str, period: int = 20) -> float:
        """Get volatility for a symbol"""
        try:
            klines = self.get_klines(symbol, "1h", period + 5)
            if len(klines) < period:
                return 0.05

            closes = [float(k[4]) for k in klines]
            returns = np.diff(np.log(closes))
            volatility = np.std(returns) * np.sqrt(24)  # 24 hours
            return float(volatility)

        except Exception as e:
            print(f"Error calculating volatility for {symbol}: {e}")
            return 0.05

    def get_price(self, symbol: str) -> float:
        """Get current price for a symbol"""
        try:
            if self.client:
                ticker = self.client.get_symbol_ticker(symbol=symbol)
                return float(ticker["price"])
            else:
                # Fallback to public API
                url = f"https://api.binance.com/api/v3/ticker/price"
                params = {"symbol": symbol}
                response = requests.get(url, params=params)
                data = response.json()
                return float(data["price"])

        except Exception as e:
            print(f"Error getting price for {symbol}: {e}")
            return 0.0

    def get_trading_pairs(self) -> List[str]:
        """Get list of available trading pairs"""
        try:
            if self.client:
                exchange_info = self.client.get_exchange_info()
                symbols = [
                    s["symbol"]
                    for s in exchange_info["symbols"]
                    if s["symbol"].endswith("USDT") and s["status"] == "TRADING"
                ]
                return symbols[:50]  # Limit to 50 pairs
            else:
                # Return common pairs
                return [
                    "BTCUSDT",
                    "ETHUSDT",
                    "BNBUSDT",
                    "XRPUSDT",
                    "ADAUSDT",
                    "SOLUSDT",
                    "DOTUSDT",
                    "LINKUSDT",
                    "LTCUSDT",
                    "BCHUSDT",
                ]

        except Exception as e:
            print(f"Error getting trading pairs: {e}")
            return ["BTCUSDT", "ETHUSDT", "BNBUSDT"]

    def get_atr(self, symbol: str, period: int = 14) -> float:
        """Get Average True Range for a symbol"""
        try:
            klines = self.get_klines(symbol, "1h", period + 5)
            if len(klines) < period:
                return 0.02  # Default 2% ATR

            highs = [float(k[2]) for k in klines]
            lows = [float(k[3]) for k in klines]
            closes = [float(k[4]) for k in klines]

            tr_list = []
            for i in range(1, len(klines)):
                tr1 = highs[i] - lows[i]
                tr2 = abs(highs[i] - closes[i - 1])
                tr3 = abs(lows[i] - closes[i - 1])
                tr = max(tr1, tr2, tr3)
                tr_list.append(tr)

            atr = np.mean(tr_list[-period:])
            return float(atr / closes[-1])  # ATR as percentage

        except Exception as e:
            print(f"Error calculating ATR for {symbol}: {e}")
            return 0.02

    def analyze_market_signals(self, symbols: List[str]) -> Dict[str, Any]:
        """Analyze market signals for multiple symbols"""
        signals = {}

        for symbol in symbols:
            try:
                rsi = self.get_latest_rsi(symbol)
                momentum = self.get_latest_momentum(symbol)
                volatility = self.get_volatility(symbol)
                price = self.get_price(symbol)

                # Simple signal logic
                signal = "HOLD"
                confidence = 0.5

                if rsi < 30 and momentum > 2:
                    signal = "BUY"
                    confidence = 0.7
                elif rsi > 70 and momentum < -2:
                    signal = "SELL"
                    confidence = 0.7
                elif abs(momentum) > 5:
                    signal = "BUY" if momentum > 0 else "SELL"
                    confidence = 0.6

                signals[symbol] = {
                    "signal": signal,
                    "confidence": confidence,
                    "rsi": rsi,
                    "momentum": momentum,
                    "volatility": volatility,
                    "price": price,
                }

            except Exception as e:
                print(f"Error analyzing {symbol}: {e}")
                signals[symbol] = {"signal": "HOLD", "confidence": 0.0, "error": str(e)}

        return signals

    def get_market_overview(self) -> Dict[str, Any]:
        """Get overall market overview"""
        try:
            symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
            signals = self.analyze_market_signals(symbols)

            total_signals = len(signals)
            buy_signals = sum(1 for s in signals.values() if s.get("signal") == "BUY")
            sell_signals = sum(1 for s in signals.values() if s.get("signal") == "SELL")

            return {
                "total_pairs": total_signals,
                "buy_signals": buy_signals,
                "sell_signals": sell_signals,
                "neutral_signals": total_signals - buy_signals - sell_signals,
                "market_sentiment": (
                    "BULLISH"
                    if buy_signals > sell_signals
                    else "BEARISH" if sell_signals > buy_signals else "NEUTRAL"
                ),
            }

        except Exception as e:
            print(f"Error getting market overview: {e}")
            return {
                "total_pairs": 0,
                "buy_signals": 0,
                "sell_signals": 0,
                "neutral_signals": 0,
                "market_sentiment": "NEUTRAL",
            }

