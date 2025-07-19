#!/usr/bin/env python3
"""
TradeExecutor
=============
Handles Spot trades with:
- Market orders
- OCO for SL/TP
- Risk checks before execution
"""

class TradeExecutor:
    def __init__(self, client, risk_manager, log_callback=None):
        self.client = client
        self.risk_manager = risk_manager
        self.active_orders = {}
        self.log = log_callback if log_callback else print

    def manual_trade(self, symbol, qty, sl_mult, tp_mult, atr_value=None):
        """Place a BUY market order with SL & TP as OCO."""
        try:
            price = float(self.client.get_symbol_ticker(symbol=symbol)["price"])
            order = self.client.order_market_buy(symbol=symbol, quantity=qty)
            self.log(f"[Manual] BUY {symbol} @ {price} Qty={qty}")

            if atr_value:
                stop_price = round(price - atr_value * sl_mult, 2)
                tp_price = round(price + atr_value * tp_mult, 2)
                oco_order = self.client.create_oco_order(
                    symbol=symbol,
                    side="SELL",
                    quantity=qty,
                    price=str(tp_price),
                    stopPrice=str(stop_price),
                    stopLimitPrice=str(stop_price * 0.999),
                    stopLimitTimeInForce="GTC"
                )
                self.active_orders[symbol] = oco_order
                self.log(f"[OCO] TP={tp_price}, SL={stop_price}")
            return f"BUY executed for {symbol}"
        except Exception as e:
            return f"Error placing trade: {e}"

    def auto_execute(self, signal, total_balance, open_positions, sl_mult, tp_mult):
        """Auto execute based on signal."""
        symbol = signal["symbol"]
        decision = signal["decision"]
        if decision != "BUY":
            return "Skipped non-BUY signal"

        price = float(self.client.get_symbol_ticker(symbol=symbol)["price"])
        qty = round((total_balance * 0.01) / price, 6)

        validation = self.risk_manager.validate_trade(symbol, qty, price, total_balance, open_positions)
        if not validation["status"]:
            self.log(f"[Risk] {validation['reason']}")
            return validation["reason"]

        atr_value = signal.get("atr", 10)  # fallback ATR
        return self.manual_trade(symbol, qty, sl_mult, tp_mult, atr_value)