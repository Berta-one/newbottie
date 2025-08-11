# api/app.py
import os
import time
import asyncio
import logging
from typing import Any, Dict, List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Shared runtime state for the UI
# (you should already have this file from earlier steps)
try:
    from status_store import STATUS  # singleton with set_equity(), upsert_position(), add_signal(), add_log(), snapshot()
except Exception as e:
    raise RuntimeError(f"status_store.py is missing: {e}")

# Your trading engine (light orchestrator that owns an ExecutionManager)
try:
    from engine.integrated_portfolio_engine import IntegratedPortfolioEngine
except Exception as e:
    raise RuntimeError(f"engine.integrated_portfolio_engine import failed: {e}")

log = logging.getLogger("BottieAPI")
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper(),
                    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")

app = FastAPI(title="Bottie API", version="1.0.0")

# ---- CORS (Netlify front-end) ----
NETLIFY_URL = os.getenv("NETLIFY_URL", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[NETLIFY_URL] if NETLIFY_URL != "*" else ["*"],
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

# ---- Config knobs (via Render env vars) ----
SYMBOLS = [s.strip() for s in os.getenv("SYMBOLS", "BTC/USDT,ETH/USDT").split(",") if s.strip()]
EQUITY_START = float(os.getenv("EQUITY_START", "10000"))
LOOP_SLEEP_S = float(os.getenv("LOOP_SLEEP_S", "1.0"))
USE_SYNTHETIC = os.getenv("USE_SYNTHETIC", "1") not in ("0", "false", "False")
QUANTUM_BACKEND_ENV = os.getenv("QUANTUM_BACKEND", "disabled")

# Engine instance + control flag
_engine: IntegratedPortfolioEngine | None = None
_run = True

# Try to report quantum backend (safe)
def _detect_quantum() -> Dict[str, str]:
    try:
        from quantum.backends import get_backend  # optional
        qb = get_backend()
        name = getattr(qb.backend, "name", None)
        name = name() if callable(name) else (name or "unknown")
        return {"kind": qb.kind, "backend": name}
    except Exception:
        return {"kind": "none", "backend": "disabled"}

QUANTUM_INFO = _detect_quantum()


# -------- Helpers to read engine state safely --------
def _read_equity_positions_from_engine() -> tuple[float | None, Dict[str, Dict[str, float]]]:
    """
    We don't assume a strict schema; read common fields with getattr().
    Expected: engine.exec_manager.equity (float), engine.exec_manager.positions (dict)
    """
    if not _engine:
        return None, {}
    exec_mgr = getattr(_engine, "exec_manager", None)
    if not exec_mgr:
        return None, {}
    equity = getattr(exec_mgr, "equity", None)
    positions = getattr(exec_mgr, "positions", {}) or {}
    # Normalize positions shape to {sym: {"qty": float, "avg_px": float}}
    norm: Dict[str, Dict[str, float]] = {}
    for sym, val in positions.items():
        if isinstance(val, dict):
            qty = float(val.get("qty", val.get("quantity", 0.0)) or 0.0)
            avg = float(val.get("avg_px", val.get("avg_price", 0.0)) or 0.0)
        elif isinstance(val, (list, tuple)) and len(val) >= 2:
            qty, avg = float(val[0]), float(val[1])
        else:
            qty, avg = 0.0, 0.0
        norm[str(sym)] = {"qty": qty, "avg_px": avg}
    return (float(equity) if equity is not None else None), norm


def _read_signals_from_engine() -> List[Dict[str, Any]]:
    """
    If your engine/executor records signals, surface them.
    We look for engine.exec_manager.last_signals or engine.last_signals.
    """
    if not _engine:
        return []
    for path in ("exec_manager.last_signals", "last_signals"):
        try:
            obj = _engine
            for part in path.split("."):
                obj = getattr(obj, part)
            if isinstance(obj, list):
                return obj[-100:]
        except Exception:
            continue
    return []


# -------- Synthetic bars (fallback) --------
def _synthetic_bars(prices: Dict[str, float]) -> List[Dict[str, Any]]:
    bars = []
    t = time.time()
    for s, px in prices.items():
        drift = 0.0006 if int(t) % 7 < 3 else -0.0005
        new_px = px * (1.0 + drift)
        prices[s] = new_px
        bars.append({
            "symbol": s,
            "close": new_px,
            "high": new_px * 1.0015,
            "low": new_px * 0.9985,
            "volume": 12000.0
        })
    return bars


# -------- Background loop --------
async def bot_loop():
    global _engine
    STATUS.add_log(f"API starting; symbols={SYMBOLS}, equity_start={EQUITY_START}")
    STATUS.set_symbols(SYMBOLS)

    _engine = IntegratedPortfolioEngine(symbols=SYMBOLS, initial_capital=EQUITY_START)
    STATUS.add_log("Engine initialized")

    # If your engine has its own async start (e.g., websockets), call it:
    # if hasattr(_engine, "start_async"):
    #     await _engine.start_async()

    prices = {s: (50000.0 if "BTC" in s.upper() else 3000.0) for s in SYMBOLS}

    while _run:
        try:
            # Feed the engine either with real data (plug WS/candles here) or synthetic fallback
            bars = _synthetic_bars(prices) if USE_SYNTHETIC else []
            for bar in bars:
                _engine.on_bar(bar)

            # Read state from engine and mirror to STATUS for the UI
            equity, positions = _read_equity_positions_from_engine()
            if equity is not None:
                STATUS.set_equity(equity)
            for sym, p in positions.items():
                STATUS.upsert_position(sym, p["qty"], p["avg_px"])

            # If your engine collects signals, surface them
            for sig in _read_signals_from_engine():
                STATUS.add_signal(
                    symbol=sig.get("symbol"),
                    signal=str(sig.get("signal", "")).upper(),
                    conf=float(sig.get("conf", sig.get("confidence", 0.0)) or 0.0),
                    probs=sig.get("probs") or sig.get("p")
                )

            await asyncio.sleep(LOOP_SLEEP_S)
        except Exception as e:
            log.exception("bot_loop error: %s", e)
            STATUS.add_log(f"ERROR: {e}")
            await asyncio.sleep(1.0)


@app.on_event("startup")
async def _on_startup():
    # Launch the bot loop
    asyncio.create_task(bot_loop())


# ----------------- API ENDPOINTS -----------------
@app.get("/")
def root():
    return {"ok": True, "service": "bottie", "time": time.time()}


@app.get("/health")
def health():
    return {
        "status": "UP",
        "ok": True,
        "service": "bottie",
        "time": int(time.time()),
        "quantum": QUANTUM_INFO or {"kind": "none", "backend": QUANTUM_BACKEND_ENV},
    }


@app.get("/status")
def status():
    # StatusStore snapshot is what the Netlify UI consumes
    return STATUS.snapshot()


@app.get("/logs/last")
def logs_last():
    return {"logs": STATUS.snapshot().get("logs", [])[-300:]}