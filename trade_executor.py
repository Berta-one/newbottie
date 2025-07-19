#!/usr/bin/env python3
"""
Trade Executor Module
========================
Handles:
- Market Buy Orders
- OCO Sell Orders (Stop Loss + Take Profit)
- ATR-based SL/TP Calculation
- Risk Management Integration
- PnL Tracking & Trade History
"""

import math
from datetime import datetime
from typing import Dict, Any, Optional, List
from binance.client import Client
from binance.enums import SIDE_BUY, SIDE_SELL
from binance.streams import BinanceSocketManager
import pandas as pd
import numpy as np


class TradeExecutor:
    def __init__(self, client: Client, risk_mgr, log_callback=None):
        self.client = client
        self.risk_mgr = risk_mgr
        self.log_callback = log_callback or print
        self.active_orders: Dict[str, Dict[str, Any]] = {}
        self.closed_trades: List[Dict[str, Any]] = []
        self.socket_manager = BinanceSocketManager(client)
        self.ws_conn_key = None

    # -----------------------------
    # Core Execution Logic
    # -----------------------------
    def manual_trade(self, symbol: str, qty: float, sl_mult: float, tp_mult: float, dynamic_sizing=False) -> str:
        return self._execute_trade(symbol, qty, sl_mult, tp_mult, dynamic_sizing)

    def auto_execute(self, signal: Dict, total_balance: float, open_positions: int,
                     sl_mult: float, tp_mult: float, dynamic_sizing=False) -> str:
        symbol = signal["symbol"]
        price = signal.get("price", self._get_market_price(symbol))
        qty = signal.get("qty", 0.001)

        # Risk validation
        validation = self.risk_mgr.validate_trade(symbol, qty, price, total_balance, open_positions)
        if not validation["status"]:
            self._log(f"❌ Risk check failed for {symbol}: {validation['reason']}")
            return validation["reason"]

        return self._execute_trade(symbol, qty, sl_mult, tp_mult, dynamic_sizing)

    # -----------------------------
    # Execute with SL & TP via OCO
    # -----------------------------
    def _execute_trade(self, symbol: str, qty: float, sl_mult: float, tp_mult: float, dynamic_sizing=False) -> str:
        try:
            price = self._get_market_price(symbol)
            atr = self._calculate_atr(symbol)

            if dynamic_sizing:
                max_risk = self.risk_mgr.max_risk_percent * 100  # example risk percent
                qty = round(max_risk / (atr * sl_mult), 6)

            # Place Market Buy
            order = self.client.order_market_buy(symbol=symbol, quantity=qty)
            buy_price = float(order["fills"][0]["price"])
            self._log(f"✅ Bought {qty} {symbol} @ {buy_price}")

            # Calculate SL & TP based on ATR
            sl_price = round(buy_price - (atr * sl_mult), 2)
            tp_price = round(buy_price + (atr * tp_mult), 2)

            # Place OCO Sell Order
            oco_order = self.client.create_oco_order(
                symbol=symbol,
                side=SIDE_SELL,
                quantity=qty,
                price=f"{tp_price:.2f}",
                stopPrice=f"{sl_price * 1.001:.2f}",  # Slight buffer
                stopLimitPrice=f"{sl_price:.2f}",
                stopLimitTimeInForce="GTC"
            )

            self.active_orders[symbol] = {
                "entry_price": buy_price,
                "sl_price": sl_price,
                "tp_price": tp_price,
                "qty": qty,
                "oco_order": oco_order,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            if not self.ws_conn_key:
                self._start_websocket_listener()

            return f"✅ Trade executed: {symbol}, SL={sl_price}, TP={tp_price}, Qty={qty}"
        except Exception as e:
            return f"❌ Execution failed: {e}"

    # -----------------------------
    # Market Data Helpers
    # -----------------------------
    def _get_market_price(self, symbol: str) -> float:
        ticker = self.client.get_symbol_ticker(symbol=symbol)
        return float(ticker["price"])

    def _calculate_atr(self, symbol: str, period: int = 14) -> float:
        klines = self.client.get_klines(symbol=symbol, interval="1h", limit=period + 1)
        highs = np.array([float(k[2]) for k in klines])
        lows = np.array([float(k[3]) for k in klines])
        closes = np.array([float(k[4]) for k in klines])

        trs = [max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1]))
               for i in range(1, len(highs))]
        return round(np.mean(trs), 2)

    # -----------------------------
    # WebSocket Listener for OCO
    # -----------------------------
    def _start_websocket_listener(self):
        def handle_msg(msg):
            if msg.get("e") == "executionReport":
                symbol = msg["s"]
                status = msg["X"]
                if status == "FILLED" and msg["x"] == "TRADE" and msg["S"] == "SELL":
                    entry_price = self.active_orders[symbol]["entry_price"]
                    exit_price = float(msg["L"])
                    qty = self.active_orders[symbol]["qty"]
                    pnl = (exit_price - entry_price) * qty
                    self.closed_trades.append({
                        "symbol": symbol,
                        "entry_price": entry_price,
                        "exit_price": exit_price,
                        "pnl": pnl,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    self._log(f"💰 Closed {symbol} @ {exit_price}, PnL: {pnl:.2f} USDT")
                    self.active_orders.pop(symbol, None)

        self.ws_conn_key = self.socket_manager.start_user_socket(handle_msg)
        self.socket_manager.start()

    # -----------------------------
    # Logging Helper
    # -----------------------------
    def _log(self, message: str):
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)