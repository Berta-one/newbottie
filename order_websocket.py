#!/usr/bin/env python3
"""
Order WebSocket Listener
=========================
Listens for real-time Binance Spot account updates:
- Order execution reports
- Balance updates
Updates:
- PositionMonitor (PnL tracking)
- TradeExecutor active orders
"""

import threading
from binance import ThreadedWebsocketManager
from datetime import datetime

class OrderWebSocket:
    def __init__(self, client, trade_executor, position_monitor, log_callback=None):
        self.client = client
        self.trade_executor = trade_executor
        self.position_monitor = position_monitor
        self.log = log_callback if log_callback else print
        self.ws_manager = None
        self._thread = None
        self._running = False

    def start(self):
        if self._running:
            self.log("[WebSocket] Already running.")
            return

        self.ws_manager = ThreadedWebsocketManager(api_key=self.client.API_KEY, api_secret=self.client.API_SECRET)
        self.ws_manager.start()

        self._thread = threading.Thread(target=self._start_socket, daemon=True)
        self._thread.start()
        self._running = True
        self.log("[WebSocket] Listening for account updates...")

    def _start_socket(self):
        self.ws_manager.start_user_socket(callback=self._handle_event)
        self.ws_manager.join()

    def stop(self):
        if self._running and self.ws_manager:
            self.ws_manager.stop()
            self._running = False
            self.log("[WebSocket] Stopped.")

    def _handle_event(self, msg):
        event_type = msg.get("e")
        if event_type == "executionReport":
            self._process_order_update(msg)
        elif event_type == "outboundAccountPosition":
            self._process_balance_update(msg)

    def _process_order_update(self, msg):
        symbol = msg["s"]
        status = msg["X"]
        side = msg["S"]
        price = float(msg["L"]) if msg["L"] != "0.00000000" else None
        qty = float(msg["l"]) if msg["l"] != "0.00000000" else None

        if status == "FILLED":
            if side == "BUY":
                self.position_monitor.open_position(symbol, price, qty)
                self.log(f"[Order FILLED] BUY {symbol} @ {price} Qty={qty}")
            elif side == "SELL":
                pnl = self.position_monitor.close_position(symbol, price)
                self.log(f"[Order FILLED] SELL {symbol} @ {price} | PnL: {pnl:.2f}")
                if symbol in self.trade_executor.active_orders:
                    del self.trade_executor.active_orders[symbol]

    def _process_balance_update(self, msg):
        balances = msg.get("B", [])
        changes = {b["a"]: b["f"] for b in balances if float(b["f"]) > 0}
        if changes:
            self.log(f"[Balance Update] {changes}")