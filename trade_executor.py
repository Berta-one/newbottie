#!/usr/bin/env python3
"""
Trade Executor for Hybrid Quantum Trading Bot
=============================================
Handles:
- Manual Trades
- Auto Trades
- Stop Loss & Take Profit using OCO
- ATR-based risk-adjusted trade sizing
- Spot-only execution
- PnL tracking (delegates to PositionMonitor)
"""

from __future__ import annotations
import time
from datetime import datetime
from typing import Dict, Any
from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException
from risk_manager import RiskManager
from position_monitor import PositionMonitor
from market_analyzer import MarketAnalyzer


class TradeExecutor:
    def __init__(self, client: Client, risk_mgr: RiskManager, log_callback=None):
        self.client = client
        self.risk_mgr = risk_mgr
        self.log = log_callback if log_callback else print
        self.position_monitor = PositionMonitor()
        self.market_analyzer = MarketAnalyzer(client)
        self.active_orders: Dict[str, Any] = {}  # symbol -> order details

    # -------------------------------
    # Manual Trade
    # -------------------------------
    def manual_trade(self, symbol: str, qty: float, sl_mult: float, tp_mult: float) -> str:
        """Executes a manual spot buy with OCO for SL/TP."""
        try:
            price = float(self.client.get_symbol_ticker(symbol=symbol)["price"])
            atr = self.market_analyzer.get_atr(symbol)  # Average True Range
            stop_price = round(price - atr * sl_mult, 2)
            limit_price = round(price - atr * sl_mult * 1.01, 2)
            take_profit_price = round(price + atr * tp_mult, 2)

            self.log(f"[Manual Trade] {symbol}: Price={price}, SL={stop_price}, TP={take_profit_price}")

            # Place market buy
            buy_order = self.client.order_market_buy(symbol=symbol, quantity=qty)
            self.position_monitor.add_position(symbol, qty, price)

            # Place OCO for SL & TP
            oco_order = self._place_oco_sell(symbol, qty, stop_price, limit_price, take_profit_price)
            self.active_orders[symbol] = {"buy_order": buy_order, "oco_order": oco_order}

            return f"✅ Manual trade executed for {symbol}: Qty={qty}, Price={price}"
        except BinanceAPIException as e:
            return f"❌ Binance API error: {e}"
        except Exception as e:
            return f"❌ Manual trade failed: {e}"

    # -------------------------------
    # Auto Trade
    # -------------------------------
    def auto_execute(self, signal: Dict[str, Any], total_balance: float, open_positions: int,
                     sl_mult: float, tp_mult: float) -> str:
        """Executes an auto trade if risk checks pass."""
        try:
            symbol = signal.get("symbol")
            decision = signal.get("decision", "HOLD")
            if decision != "BUY":
                return f"Skipped {symbol} (Signal={decision})"

            price = float(self.client.get_symbol_ticker(symbol=symbol)["price"])
            qty = self._calculate_quantity(symbol, total_balance, price)

            # Risk check
            validation = self.risk_mgr.validate_trade(symbol, qty, price, total_balance, open_positions)
            if not validation["status"]:
                return f"❌ Risk Check Failed: {validation['reason']}"

            # Execute trade
            return self.manual_trade(symbol, qty, sl_mult, tp_mult)
        except Exception as e:
            return f"❌ Auto trade failed: {e}"

    # -------------------------------
    # OCO Order Placement
    # -------------------------------
    def _place_oco_sell(self, symbol: str, qty: float, stop_price: float,
                        limit_price: float, take_profit_price: float):
        """Places an OCO sell order for SL and TP."""
        try:
            oco_order = self.client.create_oco_order(
                symbol=symbol,
                side=SIDE_SELL,
                quantity=qty,
                price=str(take_profit_price),
                stopPrice=str(stop_price),
                stopLimitPrice=str(limit_price),
                stopLimitTimeInForce=TIME_IN_FORCE_GTC
            )
            self.log(f"OCO order placed: TP={take_profit_price}, SL={stop_price}")
            return oco_order
        except BinanceAPIException as e:
            self.log(f"OCO order failed: {e}")
            return None

    # -------------------------------
    # Position Size Calculation
    # -------------------------------
    def _calculate_quantity(self, symbol: str, total_balance: float, price: float) -> float:
        """Calculate quantity based on max risk % and symbol price."""
        max_risk = self.risk_mgr.max_risk_percent * total_balance
        qty = round(max_risk / price, 6)
        return max(qty, 0.0001)  # Ensure min lot size

    # -------------------------------
    # Active Orders
    # -------------------------------
    def get_active_orders(self) -> Dict[str, Any]:
        return self.active_orders