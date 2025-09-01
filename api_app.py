# Environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")
DEMO_MODE = os.getenv("DEMO_MODE", "0") == "1"
NETLIFY_URL = os.getenv("NETLIFY_URL", "https://dancing-figolla-978034.netlify.app")

import os
import csv
import io
import time
import random
import asyncio
from typing import Any, Dict, List
from fastapi import Response, FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# --- Minimal in‑memory state so UI has something to show ---
_log_categories = ["system", "errors", "trades", "ml", "orders", "risk", "data"]
_logs_buffer: Dict[str, List[Dict[str, Any]]] = {cat: [] for cat in _log_categories}

_started = time.time()
_equity_series: List[Dict[str, Any]] = []   # [{"t": ts, "v": float}]
_positions: Dict[str, Dict[str, float]] = {}  # "BTC/USDT": {"qty":..., "avg_px":...}
_signals: List[Dict[str, Any]] = []  # recent signals
_logs: List[str] = []


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
        "quantum": os.getenv("QUANTUM_BACKEND", "enabled"),
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



@app.get("/reports")
def serve_reports():
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content="""<!DOCTYPE html>
<html><head><title>Trading Reports</title>
<link href='https://cdnjs.cloudflare.com/ajax/libs/tailwindcss/2.2.19/tailwind.min.css' rel='stylesheet'>
</head><body class='bg-gray-50'>
<nav class='bg-blue-600 text-white p-4'><h1>Trading Reports Dashboard</h1></nav>
<div class='container mx-auto p-8'>
<button onclick='loadData()' class='bg-blue-500 text-white px-4 py-2 rounded mb-4'>Load Trading Data</button>
<div id='data'>Click button to load</div>
</div>
<script>
async function loadData() {
const response = await fetch('/api/trades');
const data = await response.json();
document.getElementById('data').innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
}
</script></body></html>""")

@app.get("/logs/last")
def logs_last():
    return {"logs": _logs[-300:]}

# Simple portfolio update loop for demo purposes
async def portfolio_loop():
    """Update portfolio data periodically"""
    while True:
        try:
            # In a real implementation, this would fetch data from Binance API
            # For demo, we'll just update the timestamp
            global _equity_series
            now = int(time.time())
            if _equity_series:
                last_value = _equity_series[-1]["v"]
                new_value = last_value + random.uniform(-50, 50)
                _equity_series.append({"t": now, "v": new_value})
                # Keep the list from growing too large
                if len(_equity_series) > 1000:
                    _equity_series = _equity_series[-1000:]
            
            # Sleep for a while before the next update
            await asyncio.sleep(60)
        except Exception as e:
            print(f"Portfolio loop error: {e}")
            await asyncio.sleep(60)

@app.on_event("startup")
async def _on_startup():
    # Import here to avoid circular imports
    
    # Check if we're in demo mode
    if DEMO_MODE:
        print("Starting in DEMO MODE - Binance API keys not required")
        asyncio.create_task(portfolio_loop())
    else:
        # Only check for API keys in live mode
        if not BINANCE_API_KEY or not BINANCE_API_SECRET:
            raise RuntimeError("Live mode requires BINANCE_API_KEY/SECRET")
        asyncio.create_task(portfolio_loop())
