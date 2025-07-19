#!/usr/bin/env python3
"""
Trade Executor for Hybrid Quantum Trading Bot
=============================================
Features:
- Manual & Auto trade execution with OCO orders
- ATR-based SL & TP
- Real-time PnL tracking and equity curve
- Binance WebSocket integration for order status
"""

from __future__ import annotations
from typing import Dict, Any, Callable, List
from binance.client import Client
from binance.exceptions import BinanceAPIException
from binance import ThreadedWebsocketManager
import pandas as pd
import threading
import time
import logging

class TradeExecutor:
    def __init__(self, client: Client, risk_mgr, log_callback: Callable[[str], None] = None):
        self.client = client
        self.risk_mgr = risk_mgr
        self.log = log_callback or print
        self.active_orders: Dict[str, Dict[str, Any]] = {}
        self.trade_history: List[Dict[str, Any]] = []  # Store all trades for PnL
        self.twm = ThreadedWebsocketManager(api_key=client.API_KEY, api_secret=client.API_SECRET)
        self.twm.start()
        self.lock = threading.Lock()
        self.equity = 0  # Running equity in USD

    # -------------------------------
    # Manual Trade with OCO
    # -------------------------------
    def manual_trade(self, symbol: str, qty: float, sl_mult: float, tp_mult: float) -> str:
        try:
            price = float(self.client.get_symbol_ticker(symbol=symbol)["price"])
            atr = self._calculate_atr(symbol)
            sl_price = round(price - atr * sl_mult, 2)
            tp_price = round(price + atr * tp_mult, 2)

            self.log(f"[Manual] OCO for {symbol} Entry={price}, SL={sl_price}, TP={tp_price}")
            order = self._place_oco_order(symbol, qty, sl_price, tp_price)

            # Record trade in history
            self._record_trade(symbol, qty, price, sl_price, tp_price, "OPEN")

            return f"OCO Order Placed for {symbol} (Qty: {qty}, Entry: {price}, SL: {sl_price}, TP: {tp_price})"
        except Exception as e:
            self.log(f"[ERROR] Manual trade failed: {e}")
            return f"Error placing manual trade: {e}"

    # -------------------------------
    # Auto Trade
    # -------------------------------
    def auto_execute(self, signal: Dict[str, Any], total_balance_usd: float, open_positions: int, sl_mult: float, tp_mult: float):
        try:
            symbol = signal["symbol"]
            price = float(self.client.get_symbol_ticker(symbol=symbol)["price"])
            qty = self._calculate_position_size(price, total_balance_usd)

            validation = self.risk_mgr.validate_trade(symbol, qty, price, total_balance_usd, open_positions)
            if not validation["status"]:
                self.log(f"[AUTO] Trade Blocked: {validation['reason']}")
                return

            atr = self._calculate_atr(symbol)
            sl_price = round(price - atr * sl_mult, 2)
            tp_price = round(price + atr * tp_mult, 2)

            self.log(f"[AUTO] OCO for {symbol} Entry={price}, SL={sl_price}, TP={tp_price}")
            order = self._place_oco_order(symbol, qty, sl_price, tp_price)

            self._record_trade(symbol, qty, price, sl_price, tp_price, "OPEN")
        except Exception as e:
            self.log(f"[ERROR] Auto trade failed: {e}")

    # -------------------------------
    # Place OCO Order
    # -------------------------------
    def _place_oco_order(self, symbol: str, qty: float, sl_price: float, tp_price: float) -> Dict[str, Any]:
        try:
            order = self.client.create_oco_order(
                symbol=symbol,
                side="SELL",
                quantity=qty,
                price=f"{tp_price:.2f}",
                stopPrice=f"{sl_price:.2f}",
                stopLimitPrice=f"{sl_price:.2f}",
                stopLimitTimeInForce="GTC"
            )
            with self.lock:
                self.active_orders[symbol] = {
                    "entry_price": float(self.client.get_symbol_ticker(symbol=symbol)["price"]),
                    "qty": qty,
                    "sl_price": sl_price,
                    "tp_price": tp_price,
                    "order_data": order
                }
            self._track_order(symbol)
            return order
        except BinanceAPIException as e:
            raise Exception(f"Binance API Error: {e.message}")

    # -------------------------------
    # Track Orders & Update PnL
    # -------------------------------
    def _track_order(self, symbol: str):
        def callback(msg):
            if msg.get("e") == "executionReport" and msg.get("s") == symbol:
                status = msg.get("X", "")
                if status in ["FILLED", "CANCELED", "REJECTED"]:
                    with self.lock:
                        trade = self.active_orders.pop(symbol, None)
                    if trade and status == "FILLED":
                        exit_price = float(msg.get("L", trade["tp_price"]))
                        pnl = (exit_price - trade["entry_price"]) * trade["qty"]
                        self.equity += pnl
                        self._update_trade_history(symbol, exit_price, pnl, "CLOSED")
                        self.log(f"[ORDER FILLED] {symbol} | Exit={exit_price} | PnL=${pnl:.2f}")
        self.twm.start_user_socket(callback)

    # -------------------------------
    # Trade History Management
    # -------------------------------
    def _record_trade(self, symbol: str, qty: float, entry: float, sl: float, tp: float, status: str):
        self.trade_history.append({
            "symbol": symbol,
            "qty": qty,
            "entry_price": entry,
            "sl_price": sl,
            "tp_price": tp,
            "status": status,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        })

    def _update_trade_history(self, symbol: str, exit_price: float, pnl: float, status: str):
        for trade in self.trade_history:
            if trade["symbol"] == symbol and trade["status"] == "OPEN":
                trade.update({"exit_price": exit_price, "pnl": pnl, "status": status})
                break

    def get_trade_history(self) -> pd.DataFrame:
        return pd.DataFrame(self.trade_history)

    def get_equity(self) -> float:
        return self.equity

    # -------------------------------
    # Calculate ATR
    # -------------------------------
    def _calculate_atr(self, symbol: str, period: int = 14) -> float:
        try:
            klines = self.client.get_klines(symbol=symbol, interval="1h", limit=period+1)
            df = pd.DataFrame(klines, columns=[
                "time", "open", "high", "low", "close", "volume", "close_time", "quote_asset_volume",
                "number_of_trades", "taker_buy_base", "taker_buy_quote", "ignore"
            ])
            df = df.astype({"high": float, "low": float, "close": float})
            df["tr"] = df["high"] - df["low"]
            df["tr"] = df[["tr", df["high"] - df["close"].shift(), df["low"] - df["close"].shift()]].abs().max(axis=1)
            atr = df["tr"].rolling(period).mean().iloc[-1]
            return atr if not pd.isna(atr) else 1.0
        except Exception:
            return 1.0

    # -------------------------------
    # Position Sizing
    # -------------------------------
    def _calculate_position_size(self, price: float, total_balance_usd: float) -> float:
        max_risk = total_balance_usd * self.risk_mgr.max_risk_percent
        qty = max_risk / price
        return round(qty, 6)  # Binance precision