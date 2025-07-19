#!/usr/bin/env python3
"""
Order WebSocket Listener
=========================
Listens for real-time Binance spot account updates:
- Order execution reports
- Balance changes
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
        self.listen_key = None
        self._thread = None
        self._running = False

    def start(self):
        """Start the user data WebSocket."""
        if self._running:
            self.log("WebSocket already running.")
            return

        self.ws_manager = ThreadedWebsocketManager(api_key=self.client.API_KEY, api_secret=self.client.API_SECRET)
        self.ws_manager.start()

        self.listen_key = self.client.stream_get_listen_key()
        self._thread = threading.Thread(target=self._start_socket, daemon=True)
        self._thread.start()
        self._running = True
        self.log("[WebSocket] Started listening for account updates.")

    def _start_socket(self):
        self.ws_manager.start_user_socket(callback=self._handle_event)
        self.ws_manager.join()

    def stop(self):
        if self._running and self.ws_manager:
            self.ws_manager.stop()
            self._running = False
            self.log("[WebSocket] Stopped.")

    def _handle_event(self, msg):
        """
        Handles account updates:
        - executionReport: Order status changes
        """
        event_type = msg.get("e")
        if event_type == "executionReport":
            self._process_order_update(msg)

    def _process_order_update(self, msg):
        """
        Process trade execution updates and update positions.
        """
        symbol = msg["s"]
        status = msg["X"]
        executed_qty = float(msg["l"])
        price = float(msg["L"])
        side = msg["S"]

        if status == "FILLED" and side == "SELL":
            # Close position
            pnl = self.position_monitor.close_position(symbol, price)
            self.log(f"[PnL] Closed {symbol} @ {price}, Realized PnL: {pnl:.2f}")
            if symbol in self.trade_executor.active_orders:
                del self.trade_executor.active_orders[symbol]

        elif status == "FILLED" and side == "BUY":
            self.log(f"[Order] Buy filled for {symbol} @ {price}, Qty={executed_qty}")
        else:
            self.log(f"[Order Update] {symbol}: Status={status}")