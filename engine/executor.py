# engine/executor.py
from __future__ import annotations

import os
import math
import logging
from typing import Dict, Optional

try:
    import ccxt  # optional: only needed for live
except Exception:
    ccxt = None  # noqa

logger = logging.getLogger("TradeExecutor")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")


class TradeExecutor:
    """
    Syncs current positions to target weights.
    - Paper mode: tracks PnL notionally (no exchange calls)
    - Live mode: uses ccxt with BINANCE by default (env-configurable)
    """

    def __init__(self, mode: str = "paper") -> None:
        self.mode = mode.lower()
        self.equity = float(os.getenv("EQUITY_START", "10000"))
        self.positions: Dict[str, float] = {}  # symbol -> qty (long+, short- if allowed)
        self.avg_price: Dict[str, float] = {}  # symbol -> avg fill price

        self.fee_rate = float(os.getenv("FEE_RATE", "0.0004"))  # 4 bps

        self.exchange = None
        if self.mode == "live":
            if ccxt is None:
                raise RuntimeError("ccxt not installed; cannot run live mode.")
            api_key = os.getenv("BINANCE_API_KEY")
            api_secret = os.getenv("BINANCE_API_SECRET")
            if not api_key or not api_secret:
                raise RuntimeError("Missing BINANCE_API_KEY / BINANCE_API_SECRET for live mode.")
            self.exchange = ccxt.binance({
                "apiKey": api_key,
                "secret": api_secret,
                "enableRateLimit": True,
            })
            logger.info("Live executor initialized (Binance).")
        else:
            logger.info("Paper executor initialized (equity=%.2f).", self.equity)

    # --- helpers --------------------------------------------------------------

    def _notional_target(self, weight: float) -> float:
        return self.equity * float(weight)

    def _qty_from_notional(self, symbol: str, notional: float, price: float) -> float:
        if price <= 0:
            return 0.0
        return notional / price

    # --- public ---------------------------------------------------------------

    def sync_positions(self, target_weights: Dict[str, float], ref_price_map: Optional[Dict[str, float]] = None) -> None:
        """
        Bring positions to target weights for each symbol.
        In paper mode, we compute trivial fills at ref_price_map with fees.
        In live mode, place market orders to move from current to target.
        """
        ref_price_map = ref_price_map or {}

        for sym, w in target_weights.items():
            price = float(ref_price_map.get(sym, 0.0))
            tgt_notional = self._notional_target(w)
            tgt_qty = self._qty_from_notional(sym, tgt_notional, price)

            cur_qty = float(self.positions.get(sym, 0.0))
            delta = tgt_qty - cur_qty

            if abs(delta) <= 1e-9:
                continue

            side = "BUY" if delta > 0 else "SELL"
            qty = abs(delta)

            if self.mode == "paper":
                self._paper_fill(sym, side, qty, price)
            else:
                self._live_market(sym, side, qty)

    # --- fills ----------------------------------------------------------------

    def _paper_fill(self, symbol: str, side: str, qty: float, price: float) -> None:
        """
        Naive paper fill: execute at ‘price’ and update equity minus fees.
        """
        if price <= 0 or qty <= 0:
            return

        # fees on notional
        notional = qty * price
        fee = notional * self.fee_rate

        # update position
        cur = float(self.positions.get(symbol, 0.0))
        if side == "BUY":
            new_qty = cur + qty
        else:
            new_qty = cur - qty

        # average price tracking (simple)
        prev_notional = cur * self.avg_price.get(symbol, price)
        if side == "BUY":
            new_notional = prev_notional + notional
        else:
            new_notional = prev_notional - notional

        self.positions[symbol] = new_qty
        if abs(new_qty) > 1e-9:
            self.avg_price[symbol] = max(1e-12, new_notional / new_qty)
        else:
            self.avg_price[symbol] = 0.0

        # equity impact: assume moving to target doesn’t realize PnL; only fee drag
        self.equity -= fee

        logger.info("PAPER %s %s qty=%.6f @ %.2f | fee=%.4f | pos=%.6f avg=%.2f | equity=%.2f",
                    side, symbol, qty, price, fee, self.positions[symbol], self.avg_price[symbol], self.equity)

    def _live_market(self, symbol: str, side: str, qty: float) -> None:
        """
        Place market order via ccxt on Binance. Quantity precision and symbol formatting
        may need exchange info; this is a minimal, safe attempt.
        """
        if not self.exchange:
            raise RuntimeError("Exchange not initialized.")

        # ccxt expects symbols like "BTC/USDT"
        mkt_sym = symbol if "/" in symbol else symbol.replace("USDT", "/USDT")

        params = {}
        try:
            order = self.exchange.create_order(mkt_sym, "market", side.lower(), qty, None, params)
            logger.info("LIVE %s %s qty=%.6f | order_id=%s", side.upper(), mkt_sym, qty, order.get("id"))
        except Exception as exc:
            logger.error("Live order failed for %s %s qty=%.6f: %s", mkt_sym, side, qty, exc)