# api_app.py
import os
import time
import asyncio
import logging
from typing import Dict, Any, List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from status_store import STATUS
# near top of api_app.py
try:
    from quantum.backends import get_backend
    _qb = get_backend()
    QUANTUM_KIND = _qb.kind
    QUANTUM_BACKEND_NAME = getattr(_qb.backend, "name", lambda: "unknown")()
except Exception:
    QUANTUM_KIND, QUANTUM_BACKEND_NAME = "none", "none"

# in /health or /status response
# e.g., inside /health:
return {"ok": True, "service": "bottie", "time": time.time(),
        "quantum": {"kind": QUANTUM_KIND, "backend": QUANTUM_BACKEND_NAME}}
# import your engine
from engine.integrated_portfolio_engine import IntegratedPortfolioEngine

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
log = logging.getLogger("BottieAPI")

app = FastAPI(title="Bottie Status API", version="1.0.0")

# CORS for Netlify front-end
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later to your Netlify domain
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# --- Background bot state ---
_symbols = os.getenv("SYMBOLS", "BTC/USDT,ETH/USDT").split(",")
_symbols = [s.strip() for s in _symbols if s.strip()]
_initial_cap = float(os.getenv("EQUITY_START", "10000"))
_loop_sleep = float(os.getenv("LOOP_SLEEP_S", "1.0"))
_run_flag = True
_engine: IntegratedPortfolioEngine | None = None


def _synthetic_bars(symbols: List[str], px: Dict[str, float]) -> List[Dict[str, Any]]:
    bars = []
    for s in symbols:
        drift = 0.0005 if (time.time() % 9) < 4.5 else -0.0004
        px[s] *= (1.0 + drift)
        close = px[s]
        bars.append({
            "symbol": s, "close": close,
            "high": close * 1.001, "low": close * 0.999,
            "volume": 10_000
        })
    return bars


async def bot_loop():
    """Background task: feeds bars into engine and updates STATUS."""
    global _engine
    STATUS.set_symbols(_symbols)
    prices = {s: (50000.0 if "BTC" in s.upper() else 3000.0) for s in _symbols}
    log.info("Starting engine with symbols=%s capital=%.2f", _symbols, _initial_cap)
    _engine = IntegratedPortfolioEngine(symbols=_symbols, initial_capital=_initial_cap)
    STATUS.add_log("Engine started")

    # OPTIONAL: if your engine exposes callbacks, wire them here to update STATUS with real events.
    # For now we demonstrate synthetic loop and where to hook.
    while _run_flag:
        try:
            for bar in _synthetic_bars(_symbols, prices):
                # You can add signal extraction if your engine exposes it.
                _engine.on_bar(bar)
                # Example: if your execution manager exposes positions/equity, read and set here:
                #   pos = _engine.exec_manager.positions  # adapt to your structure
                #   for sym, p in pos.items():
                #       STATUS.upsert_position(sym, p["qty"], p["avg_px"])
                #   STATUS.set_equity(_engine.exec_manager.equity)

            await asyncio.sleep(_loop_sleep)
        except Exception as exc:
            log.exception("Bot loop error: %s", exc)
            STATUS.add_log(f"ERROR: {exc}")
            await asyncio.sleep(1.0)


@app.on_event("startup")
async def _on_startup():
    asyncio.create_task(bot_loop())


@app.get("/health")
async def health():
    return {"ok": True, "service": "bottie", "time": time.time()}


@app.get("/status")
async def status():
    return STATUS.snapshot()


@app.get("/logs/last")
async def last_logs():
    return {"logs": STATUS.snapshot().get("logs", [])}