# engine/execution_manager.py
from __future__ import annotations

import os
import time
import logging
from dataclasses import dataclass, field
from typing import Dict, Tuple, List

from engine.signal_generator import SignalGenerator
from engine.portfolio_manager import HybridPortfolioManager
from engine.executor import TradeExecutor

logger = logging.getLogger("ExecutionManager")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")


@dataclass
class SymbolState:
    position: float = 0.0            # +qty long, -qty short (if you support it), 0 flat
    avg_price: float = 0.0
    last_signal: str = "HOLD"
    last_conf: float = 0.0
    last_trade_ts: float = 0.0
    last_price: float = 0.0


class ExecutionManager:
    """
    - Generates per-symbol signals using SignalGenerator
    - Applies risk/cooldown/confirmation rules
    - Computes target weights via PortfolioManager (quantum or classical)
    - Syncs positions via TradeExecutor
    """

    def __init__(
        self,
        symbols: List[str],
        initial_capital: float = 10_000.0,
        min_trade_conf: float | None = None,
        trade_cooldown_s: float | None = None,
        max_pos_per_symbol: float | None = None,
        mode: str | None = None,  # "paper" or "live"
    ) -> None:
        self.symbols = symbols
        self.signal_gen = SignalGenerator()
        # Tunables (env overrides) — needed before HybridPortfolioManager
        self.min_trade_conf = float(os.getenv("MIN_TRADE_CONF", min_trade_conf if min_trade_conf is not None else 0.15))
        self.trade_cooldown_s = float(os.getenv("TRADE_COOLDOWN_S", trade_cooldown_s if trade_cooldown_s is not None else 30.0))
        self.max_pos_per_symbol = float(os.getenv("MAX_POS_PCT", max_pos_per_symbol if max_pos_per_symbol is not None else 0.5))  # of equity
        _lambda_risk = float(os.getenv("PORTFOLIO_LAMBDA_RISK", "0.1"))
        self.portfolio = HybridPortfolioManager(max_pos_pct=self.max_pos_per_symbol, lambda_risk=_lambda_risk)
        self.executor = TradeExecutor(mode=mode or os.getenv("BOT_MODE", "paper"))

        self.state: Dict[str, SymbolState] = {sym: SymbolState() for sym in symbols}

        logger.info(
            "ExecutionManager init | mode=%s min_conf=%.3f cooldown=%ss max_pos_pct=%.2f",
            self.executor.mode, self.min_trade_conf, self.trade_cooldown_s, self.max_pos_per_symbol
        )

    # --- policy knobs ---------------------------------------------------------

    def _can_trade(self, sym: str) -> bool:
        now = time.time()
        st = self.state[sym]
        if (now - st.last_trade_ts) < self.trade_cooldown_s:
            return False
        return True

    def _confirm_signal(self, sym: str, signal: str, conf: float) -> bool:
        if conf < self.min_trade_conf:
            return False
        # Optional: require change vs last signal to avoid churn
        prev = self.state[sym].last_signal
        if signal == "HOLD":
            return False
        # Allow same signal if confidence greatly improved
        if signal == prev and conf < (self.state[sym].last_conf + 0.05):
            return False
        return True

    # --- main entry -----------------------------------------------------------

    def on_bar(self, bar: Dict) -> None:
        """
        bar: {"symbol": "BTC/USDT", "close": float, "high": float, "low": float, "volume": float, ...}
        """
        sym = str(bar["symbol"])
        price = float(bar.get("close", 0.0))
        st = self.state.setdefault(sym, SymbolState())
        st.last_price = price

        # 1) Generate signal
        signal, conf = self.signal_gen.generate(bar)
        logger.info("Symbol=%s signal=%s conf=%.3f price=%.2f", sym, signal, conf, price)

        # 2) Guardrails: cooldown + confidence
        if not self._can_trade(sym):
            logger.info("Cooldown active for %s; skipping trade.", sym)
            st.last_signal, st.last_conf = signal, conf
            return

        if not self._confirm_signal(sym, signal, conf):
            logger.info("Signal not confirmed for %s (conf %.3f < min %.3f or HOLD).",
                        sym, conf, self.min_trade_conf)
            st.last_signal, st.last_conf = signal, conf
            return

        # 3) Map latest bar to per-symbol confidence (others → 0) for weighting
        conf_map = {s: 0.0 for s in self.symbols}
        if signal == "BUY":
            conf_map[sym] = float(conf)
        elif signal == "SELL":
            conf_map[sym] = 0.0
        weights = self.portfolio.target_weights(self.symbols, conf_map)

        # 4) Cap per-symbol max exposure
        for s, w in list(weights.items()):
            if abs(w) > self.max_pos_per_symbol:
                logger.info("Capping weight for %s from %.3f → %.3f", s, w, self.max_pos_per_symbol * (1 if w > 0 else -1))
                weights[s] = self.max_pos_per_symbol * (1 if w > 0 else -1)

        # 5) Execute
        self.executor.sync_positions(weights, ref_price_map={sym: price})

        # 6) Update state
        st.last_signal, st.last_conf = signal, conf
        st.last_trade_ts = time.time()