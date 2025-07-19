#!/usr/bin/env python3
"""
trade_executor.py
Handles:
- Risk-based position sizing
- ATR-based SL/TP
- OCO order placement
- Real-time WebSocket order updates
"""

import math
from datetime import datetime
from typing import Dict, Any
import numpy as np
from binance.client import Client
from binance.enums import *
from binance.websockets import BinanceSocketManager


class TradeExecutor:
    def __init__(self, client: Client, risk_mgr, log_callback=None):
        self.client = client
        self.risk_mgr = risk_mgr
        self.log_callback = log_callback or print
        self.active_orders = {}
        self.socket_manager = BinanceSocketManager(client)
        self.ws_conn_key = None

    # ------------------------
    # Main Trade Execution
    # ------------------------
    def manual_trade(self, symbol: str, qty: float, sl_mult: float = 1.5, tp_mult: float = 3.0) -> str:
        return self._execute_trade(symbol, qty, sl_mult, tp_mult)

    def auto_execute(self, signal: Dict[str, Any], total_balance_usd: float, open_positions: int,
                     sl_mult: float = 1.5, tp_mult: float = 3.0) -> str:
        try:
            symbol = signal["symbol"]
            price = self._get_market_price(symbol)
            qty = self._calculate_qty(symbol, price, total_balance_usd)

            if qty <= 0:
                return f"❌ Position size too small for {symbol}"

            validation = self.risk_mgr.validate_trade(symbol, qty, price, total_balance_usd, open_positions)
            if not validation["status"]:
                return f"❌ Risk Check Failed: {validation['reason']}"

            return self._execute_trade(symbol, qty, sl_mult, tp_mult)
        except Exception as e:
            return f"❌ Auto trade error: {e}"

    # ------------------------
    # Internal Execution
    # ------------------------
    def _execute_trade(self, symbol: str, qty: float, sl_mult: float, tp_mult: float) -> str:
        try:
            order = self.client.order_market_buy(symbol=symbol, quantity=qty)
            buy_price = float(order["fills"][0]["price"])
            self._log(f"✅ Bought {qty} {symbol} @ {buy_price}")

            atr = self._calculate_atr(symbol)
            sl_price = round(buy_price - (atr * sl_mult), 2)
            tp_price = round(buy_price + (atr * tp_mult), 2)

            self._log(f"📌 SL: {sl_price}, TP: {tp_price} (ATR={atr:.2f})")

            oco_order = self.client.create_oco_order(
                symbol=symbol,
                side=SIDE_SELL,
                quantity=qty,
                price=f"{tp_price:.2f}",
                stopPrice=f"{sl_price * 1.001:.2f}",
                stopLimitPrice=f"{sl_price:.2f}",
                stopLimitTimeInForce="GTC"
            )

            self.active_orders[symbol] = {
                "entry_price": buy_price,
                "sl_price": sl_price,
                "tp_price": tp_price,
                "oco_order": oco_order
            }

            if not self.ws_conn_key:
                self._start_websocket_listener()

            return f"✅ Trade executed: {symbol} qty={qty}, SL={sl_price}, TP={tp_price}"
        except Exception as e:
            return f"❌ Execution failed: {e}"

    # ------------------------
    # Risk & ATR Calculations
    # ------------------------
    def _calculate_qty(self, symbol: str, price: float, total_balance_usd: float) -> float:
        max_risk = total_balance_usd * self.risk_mgr.max_risk_percent
        qty = max_risk / price
        return float(f"{qty:.6f}")

    def _calculate_atr(self, symbol: str, period: int = 14) -> float:
        klines = self.client.get_klines(symbol=symbol, interval=KLINE_INTERVAL_1HOUR, limit=period+1)
        highs = [float(k[2]) for k in klines]
        lows = [float(k[3]) for k in klines]
        closes = [float(k[4]) for k in klines]

        trs = [max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
               for i in range(1, len(klines))]
        return np.mean(trs)

    def _get_market_price(self, symbol: str) -> float:
        return float(self.client.get_symbol_ticker(symbol=symbol)["price"])

    def _log(self, msg: str):
        self.log_callback(f"[TRADE] {datetime.now().isoformat()} {msg}")

    # ------------------------
    # WebSocket Monitoring
    # ------------------------
    def _start_websocket_listener(self):
        def handle_msg(msg):
            if msg.get("e") == "executionReport":
                symbol = msg["s"]
                status = msg["X"]
                self._log(f"📡 {symbol} update: {status}")
                if status in ["FILLED", "CANCELED"]:
                    self.active_orders.pop(symbol, None)

        self.ws_conn_key = self.socket_manager.start_user_socket(handle_msg)
        self.socket_manager.start()