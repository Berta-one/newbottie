#!/usr/bin/env python3
"""
trade_executor.py
========================
Handles execution of trades with:
- Risk-based position sizing
- Dynamic SL/TP levels
- OCO order placement
- WebSocket monitoring for real-time updates
"""

import math
import threading
import json
from datetime import datetime
from typing import Dict, Any, Optional
from binance.client import Client
from binance.websockets import BinanceSocketManager
from binance.enums import *
import numpy as np

class TradeExecutor:
    def __init__(self, client: Client, risk_mgr, log_callback=None):
        """
        :param client: Binance client instance
        :param risk_mgr: RiskManager instance
        :param log_callback: Optional logging function for UI
        """
        self.client = client
        self.risk_mgr = risk_mgr
        self.log_callback = log_callback or print
        self.socket_manager = BinanceSocketManager(client)
        self.ws_conn_key = None
        self.active_orders = {}  # symbol -> order details

    # -------------------------------
    # Public Trade Functions
    # -------------------------------
    def manual_trade(self, symbol: str, qty: float, side: str) -> str:
        """Execute manual trade (only BUY allowed for now)."""
        if side.upper() != "BUY":
            return "❌ Short selling not supported."
        return self._execute_trade(symbol, qty)

    def auto_execute(self, signal: Dict[str, Any]) -> str:
        """Execute trade from signal (auto mode)."""
        symbol = signal["symbol"]
        price = float(signal.get("price", self._get_market_price(symbol)))
        total_balance_usd = signal.get("total_balance_usd", 1000)
        open_positions = signal.get("open_positions", 0)

        # Calculate qty based on risk manager
        qty = self._calculate_qty(symbol, price, total_balance_usd)
        if qty <= 0:
            return f"❌ Position size too small for {symbol}."

        validation = self.risk_mgr.validate_trade(symbol, qty, price, total_balance_usd, open_positions)
        if not validation["status"]:
            return f"❌ Risk Check Failed: {validation['reason']}"

        return self._execute_trade(symbol, qty)

    # -------------------------------
    # Core Execution Logic
    # -------------------------------
    def _execute_trade(self, symbol: str, qty: float) -> str:
        try:
            # 1. Place Market Buy Order
            order = self.client.order_market_buy(symbol=symbol, quantity=qty)
            buy_price = float(order["fills"][0]["price"])
            self._log(f"✅ Bought {qty} {symbol} @ {buy_price}")

            # 2. Compute SL/TP levels using ATR or percentage
            atr = self._calculate_atr(symbol)
            sl_price = buy_price - (atr * 1.5)  # SL at 1.5 ATR below
            tp_price = buy_price + (atr * 3)    # TP at 3 ATR above
            self._log(f"📌 SL: {sl_price:.2f}, TP: {tp_price:.2f}")

            # 3. Place OCO Sell Order
            oco_order = self.client.create_oco_order(
                symbol=symbol,
                side=SIDE_SELL,
                quantity=qty,
                price=f"{tp_price:.2f}",
                stopPrice=f"{sl_price * 1.001:.2f}",   # trigger slightly above SL
                stopLimitPrice=f"{sl_price:.2f}",
                stopLimitTimeInForce="GTC"
            )

            self.active_orders[symbol] = {
                "entry_price": buy_price,
                "sl_price": sl_price,
                "tp_price": tp_price,
                "oco_order": oco_order
            }
            self._log(f"✅ OCO placed for {symbol}. TP: {tp_price}, SL: {sl_price}")

            # 4. Start WebSocket Listener
            if not self.ws_conn_key:
                self._start_websocket_listener()

            return f"✅ Trade executed for {symbol} (qty={qty})"
        except Exception as e:
            return f"❌ Trade execution failed: {e}"

    # -------------------------------
    # Helper Functions
    # -------------------------------
    def _calculate_qty(self, symbol: str, price: float, total_balance_usd: float) -> float:
        max_risk = total_balance_usd * self.risk_mgr.max_risk_percent
        qty = max_risk / price
        return float(f"{qty:.6f}")  # Adjust precision

    def _calculate_atr(self, symbol: str, period: int = 14) -> float:
        """Compute ATR using recent klines."""
        try:
            klines = self.client.get_klines(symbol=symbol, interval=KLINE_INTERVAL_1HOUR, limit=period + 1)
            highs = [float(k[2]) for k in klines]
            lows = [float(k[3]) for k in klines]
            closes = [float(k[4]) for k in klines]

            trs = []
            for i in range(1, len(klines)):
                tr = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
                trs.append(tr)
            return np.mean(trs)
        except:
            return price * 0.02  # fallback to 2% of price

    def _get_market_price(self, symbol: str) -> float:
        ticker = self.client.get_symbol_ticker(symbol=symbol)
        return float(ticker["price"])

    def _log(self, message: str):
        if self.log_callback:
            self.log_callback(f"[TRADE] {datetime.now().isoformat()} {message}")
        else:
            print(message)

    # -------------------------------
    # WebSocket for Order Updates
    # -------------------------------
    def _start_websocket_listener(self):
        def handle_msg(msg):
            if msg.get("e") == "executionReport":
                symbol = msg["s"]
                status = msg["X"]
                self._log(f"📡 Update: {symbol} - {status}")
                if status in ["FILLED", "CANCELED"]:
                    self.active_orders.pop(symbol, None)

        self.ws_conn_key = self.socket_manager.start_user_socket(handle_msg)
        self.socket_manager.start()