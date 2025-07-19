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
        """
        Initialize WebSocket listener for Binance Spot account.
        :param client: Binance Client instance
        :param trade_executor: TradeExecutor instance
        :param position_monitor: PositionMonitor instance
        :param log_callback: Optional logging callback
        """
        self.client = client
        self.trade_executor = trade_executor
        self.position_monitor = position_monitor
        self.log = log_callback if log_callback else print
        self.ws_manager = None
        self._thread = None
        self._running = False

    def start(self):
        """Start the user data WebSocket for live order/account updates."""
        if self._running:
            self.log("[WebSocket] Already running.")
            return

        # Start WebSocket Manager
        self.ws_manager = ThreadedWebsocketManager(api_key=self.client.API_KEY, api_secret=self.client.API_SECRET)
        self.ws_manager.start()

        # Start user data socket in a separate thread
        self._thread = threading.Thread(target=self._start_socket, daemon=True)
        self._thread.start()
        self._running = True
        self.log("[WebSocket] Started listening for account updates.")

    def _start_socket(self):
        """Start user socket and listen for account/order updates."""
        self.ws_manager.start_user_socket(callback=self._handle_event)
        self.ws_manager.join()

    def stop(self):
        """Stop the WebSocket manager."""
        if self._running and self.ws_manager:
            self.ws_manager.stop()
            self._running = False
            self.log("[WebSocket] Stopped successfully.")

    def _handle_event(self, msg):
        """
        Handle Binance user data events.
        :param msg: Event message from Binance WebSocket
        """
        event_type = msg.get("e")
        if event_type == "executionReport":
            self._process_order_update(msg)
        elif event_type == "outboundAccountPosition":
            self._process_balance_update(msg)

    def _process_order_update(self, msg):
        """
        Handle order execution updates:
        - Detect FILLED buy/sell orders
        - Update PositionMonitor and active_orders in TradeExecutor
        """
        symbol = msg["s"]       # Symbol (e.g., BTCUSDT)
        status = msg["X"]       # Order status
        side = msg["S"]         # BUY or SELL
        price = float(msg["L"]) # Last executed price
        qty = float(msg["l"])   # Last executed quantity

        if status == "FILLED":
            if side == "BUY":
                # Add position if not present
                self.position_monitor.open_position(symbol, price, qty)
                self.log(f"[Order FILLED] BUY {symbol} @ {price} (Qty={qty})")
            elif side == "SELL":
                # Close position and calculate PnL
                pnl = self.position_monitor.close_position(symbol, price)
                self.log(f"[Order FILLED] SELL {symbol} @ {price} | Realized PnL: {pnl:.2f}")
                if symbol in self.trade_executor.active_orders:
                    del self.trade_executor.active_orders[symbol]
        else:
            self.log(f"[Order Update] {symbol}: Status={status}, Side={side}")

    def _process_balance_update(self, msg):
        """Handle balance updates for logging/debugging."""
        balances = msg.get("B", [])
        changes = {b["a"]: b["f"] for b in balances if float(b["f"]) > 0}
        if changes:
            self.log(f"[Balance Update] {changes}")