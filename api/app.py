# api/app.py  — LIVE BINANCE SPOT (no testnet, no mock data)
import os, time, asyncio, logging
from typing import Any, Dict, List, Optional, Tuple
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# --- deps
try:
    import ccxt
except Exception as e:
    raise RuntimeError(f"ccxt not installed. Add to requirements.txt: {e}")

def _detect_quantum() -> Dict[str, str]:
    try:
        from quantum.backends import get_backend  # optional
        qb = get_backend()
        name = getattr(qb.backend, "name", None)
        name = name() if callable(name) else (name or "unknown")
        return {"kind": qb.kind, "backend": name}
    except Exception:
        return {"kind": "none", "backend": os.getenv("QUANTUM_BACKEND", "disabled")}

NETLIFY_URL   = os.getenv("NETLIFY_URL", "*")
BINANCE_API_KEY    = os.getenv("BINANCE_API_KEY", "")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")
PRIMARY_QUOTE = os.getenv("PRIMARY_QUOTE", "USDT")
LOOP_SLEEP_S  = float(os.getenv("LOOP_SLEEP_S", "5.0"))
LOG_LEVEL     = os.getenv("LOG_LEVEL", "INFO").upper()

log = logging.getLogger("BottieAPI")
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")

app = FastAPI(title="Bottie API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[NETLIFY_URL] if NETLIFY_URL != "*" else ["*"],
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

_started = time.time()
_equity_series: List[Dict[str, Any]] = []
_positions: Dict[str, Dict[str, float]] = {}
_signals: List[Dict[str, Any]] = []
_logs: List[str] = []

def add_log(msg: str):
    msg = msg.strip()
    _logs.append(msg)
    if len(_logs) > 1000:
        del _logs[:-1000]
    log.info(msg)
# --- quick live check: fetch balances NOW (no cached data) ---
@app.get("/status_live_now")
def status_live_now():
    import math
    assert _exchange is not None, "Exchange not init"
    bal = _exchange.fetch_balance(params={})
    assets = _nonzero_assets_from_balance(bal)
    equity, positions = _value_portfolio(assets)
    return {
        "mode": "live-spot-now",
        "time": int(time.time()),
        "equity": float(equity),
        "positions": positions,
        "assets_raw": {k: float(v) for k, v in assets.items()},
    }
# --- binance LIVE spot
_exchange: Optional[ccxt.binance] = None
def _init_binance() -> ccxt.binance:
    if not BINANCE_API_KEY or not BINANCE_API_SECRET:
        raise RuntimeError("BINANCE_API_KEY / BINANCE_API_SECRET missing.")
    ex = ccxt.binance({
        "apiKey": BINANCE_API_KEY,
        "secret": BINANCE_API_SECRET,
        "enableRateLimit": True,
        "options": {"defaultType": "spot"},
    })
    add_log("Binance initialized (LIVE spot)")
    return ex

async def _ensure_exchange():
    global _exchange
    if _exchange is None:
        _exchange = _init_binance()
        try:
            _exchange.load_markets()
            add_log(f"Loaded {len(_exchange.markets)} markets")
        except Exception as e:
            add_log(f"ERROR load_markets: {e}")

def _nonzero_assets_from_balance(balance: Dict[str, Any]) -> Dict[str, float]:
    assets: Dict[str, float] = {}
    for asset, entry in (balance.get("total") or {}).items():
        try:
            qty = float(entry or 0.0)
        except Exception:
            qty = 0.0
        if qty > 0:
            assets[asset] = qty
    return assets

def _symbol_exists(base: str, quote: str) -> bool:
    assert _exchange is not None
    return f"{base}/{quote}" in _exchange.markets

def _quote_priority() -> List[str]:
    tail = ["USD", "BUSD", "USDC", "BTC", "ETH", "EUR", "TRY"]
    return [PRIMARY_QUOTE] + [x for x in tail if x != PRIMARY_QUOTE]

def _best_symbol_for_asset(asset: str, preferred_quotes: List[str]) -> Optional[str]:
    for q in preferred_quotes:
        if _symbol_exists(asset, q):
            return f"{asset}/{q}"
    return None

def _fetch_tickers(symbols: List[str]) -> Dict[str, Any]:
    assert _exchange is not None
    if not symbols:
        return {}
    try:
        return _exchange.fetch_tickers(symbols) or {}
    except Exception as e:
        add_log(f"ERROR fetch_tickers: {e}")
        return {}

def _value_portfolio(assets: Dict[str, float]) -> Tuple[float, Dict[str, Dict[str, float]]]:
    preferred = _quote_priority()
    symbols: List[str] = []
    chosen: Dict[str, str] = {}
    for asset, qty in assets.items():
        if asset.upper() == PRIMARY_QUOTE.upper():
            chosen[asset] = f"{asset}/{PRIMARY_QUOTE}"
            continue
        sym = _best_symbol_for_asset(asset, preferred)
        if sym:
            chosen[asset] = sym
            symbols.append(sym)

    tick = _fetch_tickers(symbols)
    equity = 0.0
    positions: Dict[str, Dict[str, float]] = {}

    for asset, qty in assets.items():
        if qty <= 0:
            continue
        if asset.upper() == PRIMARY_QUOTE.upper():
            symbol = f"{asset}/{PRIMARY_QUOTE}"
            last_px = 1.0
        else:
            sym = chosen.get(asset)
            if not sym:
                add_log(f"Skip valuation for {asset} (no {asset}/{PRIMARY_QUOTE} or alternatives)")
                continue
            symbol = sym
            info = tick.get(sym) or {}
            last_px = float(info.get("last") or info.get("close") or 0.0)
            if last_px <= 0.0:
                add_log(f"Missing price for {sym}, skipping")
                continue
        equity += qty * last_px
        positions[symbol] = {"qty": float(qty), "avg_px": float(last_px), "last_px": float(last_px)}
    return equity, positions

async def portfolio_loop():
    await _ensure_exchange()
    add_log(f"Portfolio loop started | primary_quote={PRIMARY_QUOTE} | LIVE spot")
    while True:
        try:
            assert _exchange is not None
            balance = _exchange.fetch_balance(params={})
            assets = _nonzero_assets_from_balance(balance)
            equity, positions = _value_portfolio(assets)

            now = int(time.time())
            _equity_series.append({"t": now, "v": float(equity)})
            if len(_equity_series) > 2000:
                del _equity_series[:-1000]

            _positions.clear()
            _positions.update(positions)

            add_log(f"snapshot | equity={equity:.2f} positions={len(_positions)}")
        except Exception as e:
            add_log(f"ERROR portfolio_loop: {e}")
        await asyncio.sleep(LOOP_SLEEP_S)

@app.on_event("startup")
async def _on_startup():
    asyncio.create_task(portfolio_loop())

@app.get("/")
def root():
    return {"ok": True, "service": "bottie", "time": time.time()}

@app.get("/health")
def health():
    last_eq = _equity_series[-1]["v"] if _equity_series else None
    return {
        "status": "UP", "ok": True, "service": "bottie", "time": int(time.time()),
        "quantum": _detect_quantum(), "primary_quote": PRIMARY_QUOTE, "live_spot": True,
        "equity": last_eq,
    }

@app.get("/status")
def status():
    last_eq = _equity_series[-1]["v"] if _equity_series else None
    return {
        "started_at": _started, "equity": last_eq,
        "equity_series": _equity_series[-300:], "positions": _positions,
        "last_signals": _signals[-100:],
    }

@app.get("/logs/last")
def logs_last():
    return {"logs": _logs[-300:]}