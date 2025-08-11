# status_store.py
import time
import threading
from typing import Any, Dict, List


class StatusStore:
    """In-memory, thread-safe state for API exposure."""
    def __init__(self):
        self._lock = threading.RLock()
        self._state: Dict[str, Any] = {
            "started_at": time.time(),
            "last_update": None,
            "symbols": [],
            "equity": None,
            "positions": {},    # symbol -> {"qty": float, "avg_px": float}
            "last_signals": [], # [{"symbol":..., "signal":..., "conf":..., "p": [sell,buy,hold], "t": ts}]
            "trades": [],       # recent trades (cap at N)
            "logs": []          # short rolling log lines
        }
        self._max_trades = 200
        self._max_logs = 300

    def set_symbols(self, symbols: List[str]):
        with self._lock:
            self._state["symbols"] = symbols

    def set_equity(self, equity: float):
        with self._lock:
            self._state["equity"] = float(equity)
            self._state["last_update"] = time.time()

    def upsert_position(self, symbol: str, qty: float, avg_px: float):
        with self._lock:
            self._state["positions"][symbol] = {"qty": float(qty), "avg_px": float(avg_px)}
            self._state["last_update"] = time.time()

    def add_signal(self, symbol: str, signal: str, conf: float, probs=None):
        with self._lock:
            self._state["last_signals"].append({
                "symbol": symbol,
                "signal": signal,
                "conf": float(conf),
                "p": probs if probs else None,
                "t": time.time(),
            })
            self._state["last_signals"] = self._state["last_signals"][-200:]
            self._state["last_update"] = time.time()

    def add_trade(self, trade: Dict[str, Any]):
        with self._lock:
            self._state["trades"].append(trade)
            self._state["trades"] = self._state["trades"][-self._max_trades:]
            self._state["last_update"] = time.time()

    def add_log(self, line: str):
        with self._lock:
            self._state["logs"].append(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {line}")
            self._state["logs"] = self._state["logs"][-self._max_logs:]

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._state)


# Singleton
STATUS = StatusStore()