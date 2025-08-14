# api/app.py
import os
import time
from typing import Any, Dict, List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Bottie API", version="1.0.0")

# Allow your Netlify site (or "*" while testing)
NETLIFY_URL = os.getenv("NETLIFY_URL", "https://dancing-figolla-978034.netlify.app")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Minimal in‑memory state so UI has something to show ---
_started = time.time()
_equity_series: List[Dict[str, Any]] = []   # [{"t": ts, "v": float}]
_positions: Dict[str, Dict[str, float]] = {}  # "BTC/USDT": {"qty":..., "avg_px":...}
_signals: List[Dict[str, Any]] = []  # recent signals
_logs: List[str] = []


def _seed_demo():
    global _equity_series, _positions, _signals, _logs
    now = int(time.time())
    _equity_series = [{"t": now - 60 * i, "v": 10000 + i * 3} for i in range(30)][::-1]
    _positions.update({
        "BTC/USDT": {"qty": 0.015, "avg_px": 50000.0},
        "ETH/USDT": {"qty": 0.300, "avg_px": 3000.0},
    })
    _signals.extend([
        {"symbol": "BTC/USDT", "signal": "BUY", "conf": 0.62, "t": now - 45},
        {"symbol": "ETH/USDT", "signal": "HOLD", "conf": 0.40, "t": now - 30},
        {"symbol": "BTC/USDT", "signal": "SELL", "conf": 0.55, "t": now - 15},
    ])
    _logs.extend([
        "engine: started",
        "portfolio: initialized",
        "ws: (demo) synthetic feed",
    ])


_seed_demo()


@app.get("/")
def root():
    return {"ok": True, "service": "bottie", "time": time.time()}


@app.get("/health")
def health():
    # This shape matches what many dashboards expect
    return {
        "status": "UP",
        "ok": True,
        "service": "bottie",
        "time": int(time.time()),
        "quantum": os.getenv("QUANTUM_BACKEND", "disabled"),
    }


@app.get("/status")
def status():
    # one snapshot object the UI can read
    return {
        "started_at": _started,
        "equity": _equity_series[-1]["v"] if _equity_series else None,
        "equity_series": _equity_series[-120:],  # keep it light
        "positions": _positions,
        "last_signals": _signals[-50:],
    }


@app.get("/logs/last")
def logs_last():
    return {"logs": _logs[-300:]}

@app.on_event("startup")
async def _on_startup():
    # Raise loudly if keys are missing
    if not BINANCE_API_KEY or not BINANCE_API_SECRET:
        raise RuntimeError("Live mode requires BINANCE_API_KEY/SECRET")
    asyncio.create_task(portfolio_loop())