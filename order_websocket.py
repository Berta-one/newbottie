#!/usr/bin/env python3
"""
Order WebSocket Listener
=========================
- Tracks account changes via user data stream
- Handles OCO updates, position PnL updates, and balance refresh
"""

import threading
from binance import ThreadedWebsocketManager
from datetime import datetime


class OrderWebSocket:
    def __init__(
        self,
        client,
        trade_executor,
        position_monitor,
        portfolio_manager,
        ui_refresh=None,
        log_callback=None,
    ):
        self.client = client
        self.trade_executor = trade_executor
        self.position_monitor = position_monitor
        self.portfolio_manager = portfolio_manager
        self.log = log_callback if log_callback else print
        self.ui_refresh = ui_refresh
        self.ws_manager = None
        self.listen_key = None
        self._running = False

    def start(self):
        if self._running:
            self.log("[WebSocket] Already running.")
            return
        self.ws_manager = ThreadedWebsocketManager(
            api_key=self.client.API_KEY, api_secret=self.client.API_SECRET
        )
        self.ws_manager.start()
        self.listen_key = self.client.stream_get_listen_key()
        self.ws_manager.start_user_socket(callback=self._handle_event)
        self._running = True
        self.log("[WebSocket] Started user data stream.")

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
            self.log("[Portfolio] Balance update received.")
            self.portfolio_manager.refresh_cache()
            if self.ui_refresh:
                self.ui_refresh()

    def _process_order_update(self, msg):
        symbol = msg["s"]
        status = msg["X"]
        executed_qty = float(msg["l"])
        price = float(msg["L"])
        side = msg["S"]

        if status == "FILLED":
            if side == "SELL":
                pnl = self.position_monitor.close_position(symbol, price)
                self.log(f"[PnL] Closed {symbol} @ {price}, Realized PnL: {pnl:.2f}")
                self.trade_executor.active_orders.pop(symbol, None)
            elif side == "BUY":
                self.position_monitor.open_position(symbol, executed_qty, price)
                self.log(
                    f"[Order] Buy filled for {symbol} @ {price}, Qty={executed_qty}"
                )
