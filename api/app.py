# api/app.py — LIVE spot + true cost-basis (WAC) from trade history
import os, time, asyncio, logging
from typing import Any, Dict, List, Optional, Tuple

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    import ccxt
except Exception as e:
    raise RuntimeError(f"ccxt not installed. Add to requirements.txt: {e}")

# -----------------------------------------------------------------------------
# Config (Render → Environment)
# -----------------------------------------------------------------------------
NETLIFY_URL       = os.getenv("NETLIFY_URL", "*")
EXCHANGE_ID       = os.getenv("EXCHANGE_ID", "binance").lower()
API_KEY           = os.getenv("API_KEY", os.getenv("BINANCE_API_KEY", ""))
API_SECRET        = os.getenv("API_SECRET", os.getenv("BINANCE_API_SECRET", ""))
API_PASSPHRASE    = os.getenv("API_PASSPHRASE", "")  # e.g., coinbaseadvanced
API_UID           = os.getenv("API_UID", "")          # e.g., bitstamp
PRIMARY_QUOTE     = os.getenv("PRIMARY_QUOTE", "USDT")
LOOP_SLEEP_S      = float(os.getenv("LOOP_SLEEP_S", "7.0"))
LOG_LEVEL         = os.getenv("LOG_LEVEL", "INFO").upper()

# Cost-basis settings
COST_LOOKBACK_DAYS     = int(os.getenv("COST_BASIS_LOOKBACK_DAYS", "120"))  # how far back to fetch trades
MAX_TRADES_PER_SYMBOL  = int(os.getenv("MAX_TRADES_PER_SYMBOL", "1000"))    # safety cap per cycle
FEE_IN_COST_BASIS      = os.getenv("FEE_IN_COST_BASIS", "1") not in ("0", "false", "False", "", None)
COST_CACHE_TTL_SEC     = int(os.getenv("COST_CACHE_TTL_SEC", "600"))        # recalc each 10 min per symbol

# -----------------------------------------------------------------------------
# App + CORS
# -----------------------------------------------------------------------------
log = logging.getLogger("BottieAPI")
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")

app = FastAPI(title="Bottie API", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[NETLIFY_URL] if NETLIFY_URL != "*" else ["*"],
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# In-memory state
# -----------------------------------------------------------------------------
_started = time.time()
_equity_series: List[Dict[str, Any]] = []         # [{"t": ts, "v": float}]
_positions: Dict[str, Dict[str, float]] = {}      # { "ADA/USDT": {"qty":..., "avg_px":..., "last_px":...}, ... }
_signals: List[Dict[str, Any]] = []
_logs: List[str] = []

# cost-basis cache: symbol -> {"ts": last_calc, "qty": float, "avg_px": float}
_cost_basis_cache: Dict[str, Dict[str, float]] = {}

def add_log(msg: str):
    msg = msg.strip()
    _logs.append(msg)
    if len(_logs) > 1000:
        del _logs[:-1000]
    log.info(msg)

# -----------------------------------------------------------------------------
# Optional quantum flag
# -----------------------------------------------------------------------------
def _detect_quantum() -> Dict[str, str]:
    try:
        from quantum.backends import get_backend  # optional
        qb = get_backend()
        name = getattr(qb.backend, "name", None)
        name = name() if callable(name) else (name or "unknown")
        return {"kind": qb.kind, "backend": name}
    except Exception:
        return {"kind": "none", "backend": os.getenv("QUANTUM_BACKEND", "disabled")}

# -----------------------------------------------------------------------------
# Exchange (LIVE spot)
# -----------------------------------------------------------------------------
_exchange: Optional[ccxt.Exchange] = None

def _init_exchange() -> ccxt.Exchange:
    if not API_KEY or not API_SECRET:
        raise RuntimeError("API_KEY / API_SECRET missing.")
    if EXCHANGE_ID not in ccxt.exchanges:
        raise RuntimeError(f"Exchange '{EXCHANGE_ID}' not supported by CCXT.")
    klass = getattr(ccxt, EXCHANGE_ID)
    params = {"apiKey": API_KEY, "secret": API_SECRET, "enableRateLimit": True}
    if EXCHANGE_ID == "coinbaseadvanced" and API_PASSPHRASE:
        params["password"] = API_PASSPHRASE
    if EXCHANGE_ID == "bitstamp" and API_UID:
        params["uid"] = API_UID
    ex = klass(params)
    if hasattr(ex, "options"):
        ex.options = {**getattr(ex, "options", {}), **{"defaultType": "spot"}}
    add_log(f"Exchange initialized: {EXCHANGE_ID} (LIVE)")
    return ex

async def _ensure_exchange():
    global _exchange
    if _exchange is None:
        _exchange = _init_exchange()
        try:
            _exchange.load_markets()
            add_log(f"Loaded {len(_exchange.markets)} markets on {EXCHANGE_ID}")
        except Exception as e:
            add_log(f"ERROR load_markets: {e}")

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
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
    tail = ["USD", "BUSD", "USDC", "BTC", "ETH", "EUR", "TRY", "GBP"]
    ordered = [PRIMARY_QUOTE] + [x for x in tail if x != PRIMARY_QUOTE]
    # keep unique order
    seen, pr = set(), []
    for q in ordered:
        if q not in seen:
            seen.add(q); pr.append(q)
    return pr

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

# -----------------------------------------------------------------------------
# Cost-basis (true avg entry) via WAC from trade history
# -----------------------------------------------------------------------------
def _ms_since(days: int) -> int:
    return int((time.time() - days * 86400) * 1000)

def _compute_cost_basis_for_symbol(symbol: str) -> Optional[Tuple[float, float]]:
    """
    Returns (net_qty, avg_px) for current position using Weighted Average Cost (WAC).
    Process trades chronologically within lookback; fees included if enabled.
    """
    assert _exchange is not None
    since = _ms_since(COST_LOOKBACK_DAYS)
    limit = MAX_TRADES_PER_SYMBOL

    try:
        trades = _exchange.fetch_my_trades(symbol, since=since, limit=limit)
    except ccxt.ExchangeError as e:
        msg = str(e).lower()
        if "451" in msg or "restricted" in msg:
            add_log(f"Restricted for trades on {symbol} in this region.")
            return None
        add_log(f"Exchange error fetch_my_trades({symbol}): {e}")
        return None
    except Exception as e:
        add_log(f"ERROR fetch_my_trades({symbol}): {e}")
        return None

    if not trades:
        return None

    # Sort by time
    trades.sort(key=lambda t: t.get("timestamp") or 0)

    net_qty = 0.0     # base units
    cost    = 0.0     # in quote currency

    for t in trades:
        side   = (t.get("side") or "").lower()      # "buy" / "sell"
        amount = float(t.get("amount") or 0.0)      # base
        price  = float(t.get("price") or 0.0)       # quote per base
        fee    = t.get("fee") or {}
        fee_cost = float(fee.get("cost") or 0.0)
        fee_ccy  = (fee.get("currency") or "").upper()

        if amount <= 0 or price <= 0:
            continue

        # Include fee if configured:
        # - If fee paid in QUOTE -> increase cost (extra quote spent)
        # - If fee paid in BASE  -> reduce acquired base amount
        eff_amount = amount
        eff_cost_add = 0.0
        if FEE_IN_COST_BASIS and fee_cost:
            if fee_ccy == symbol.split("/")[1].upper():  # fee in QUOTE
                eff_cost_add = fee_cost
            elif fee_ccy == symbol.split("/")[0].upper():  # fee in BASE
                eff_amount = max(0.0, amount - fee_cost)   # reduce acquired/sold base

        if side == "buy":
            # increase inventory and cost
            net_qty += eff_amount
            cost    += eff_amount * price + eff_cost_add
        elif side == "sell":
            # reduce inventory; WAC removes cost at current avg
            if net_qty <= 0:
                # no inventory tracked; skip WAC decrement (can't go negative)
                continue
            avg_px = cost / net_qty if net_qty > 0 else 0.0
            dec_amount = min(eff_amount, net_qty)
            cost    -= avg_px * dec_amount
            net_qty -= dec_amount
        # else ignore unknown side

    if net_qty <= 0:
        return (0.0, 0.0)

    avg_px = cost / net_qty if net_qty > 0 else 0.0
    return (net_qty, avg_px)

def _get_cost_basis(symbol: str) -> Optional[Tuple[float, float]]:
    # simple TTL cache
    now = time.time()
    entry = _cost_basis_cache.get(symbol)
    if entry and (now - entry["ts"] < COST_CACHE_TTL_SEC):
        return (entry["qty"], entry["avg_px"])
    res = _compute_cost_basis_for_symbol(symbol)
    if res:
        qty, avg_px = res
        _cost_basis_cache[symbol] = {"ts": now, "qty": qty, "avg_px": avg_px}
    return res

# -----------------------------------------------------------------------------
# Valuation loop
# -----------------------------------------------------------------------------
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
            # cash: no cost basis
            positions[symbol] = {"qty": float(qty), "avg_px": 1.0, "last_px": 1.0}
            equity += qty * 1.0
            continue

        sym = chosen.get(asset)
        if not sym:
            add_log(f"Skip valuation for {asset} (no direct market to {PRIMARY_QUOTE} or alternatives)")
            continue

        info = tick.get(sym) or {}
        last_px = float(info.get("last") or info.get("close") or 0.0)
        if last_px <= 0.0:
            add_log(f"Missing price for {sym}, skipping")
            continue

        # True cost basis via WAC (cached)
        cb = _get_cost_basis(sym)
        if cb:
            cb_qty, cb_avg = cb
            # We present the current balance qty with avg from history if there is inventory
            avg_px = float(cb_avg) if cb_qty > 0 else float(last_px)
        else:
            avg_px = float(last_px)  # fallback

        positions[sym] = {"qty": float(qty), "avg_px": float(avg_px), "last_px": float(last_px)}
        equity += qty * last_px

    return equity, positions

async def portfolio_loop():
    await _ensure_exchange()
    add_log(f"Portfolio loop started | exchange={EXCHANGE_ID} | primary_quote={PRIMARY_QUOTE} | LIVE spot")
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

        except ccxt.ExchangeError as e:
            msg = str(e)
            if "451" in msg or "restricted" in msg.lower():
                add_log("Geo-restricted by venue for authenticated calls. Use a permitted region/venue.")
            else:
                add_log(f"Exchange error: {msg}")
        except Exception as e:
            add_log(f"ERROR portfolio_loop: {e}")

        await asyncio.sleep(LOOP_SLEEP_S)

# -----------------------------------------------------------------------------
# Startup
# -----------------------------------------------------------------------------
@app.on_event("startup")
async def _on_startup():
    asyncio.create_task(portfolio_loop())

# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------
@app.get("/")
def root():
    return {"ok": True, "service": "bottie", "time": time.time()}

@app.get("/health")
def health():
    last_eq = _equity_series[-1]["v"] if _equity_series else None
    return {
        "status": "UP",
        "ok": True,
        "service": "bottie",
        "time": int(time.time()),
        "quantum": _detect_quantum(),
        "exchange": EXCHANGE_ID,
        "primary_quote": PRIMARY_QUOTE,
        "equity": last_eq,
    }

@app.get("/status")
def status():
    last_eq = _equity_series[-1]["v"] if _equity_series else None
    return {
        "started_at": _started,
        "equity": last_eq,
        "equity_series": _equity_series[-300:],
        "positions": _positions,
        "last_signals": _signals[-100:],
    }

@app.get("/logs/last")
def logs_last():
    return {"logs": _logs[-300:]}

@app.get("/costbasis")
def costbasis():
    """
    Inspect current cached cost-basis per symbol.
    """
    out = {}
    for sym, entry in _cost_basis_cache.items():
        out[sym] = {"qty": entry["qty"], "avg_px": entry["avg_px"], "age_sec": time.time() - entry["ts"]}
    return out