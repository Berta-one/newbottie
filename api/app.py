# api/app.py
# Bottie API — Live Binance spot, true cost basis (WAC), EMA+ML(+Quantum) signals
import os
import time
import math
import json
import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    import ccxt
except Exception as e:
    raise RuntimeError(f"ccxt not installed. Add to requirements.txt: {e}")

# Optional: ML
_ML_ENABLED = os.getenv("ML_ENABLED", "1") not in ("0", "false", "False")
_MODEL_PATH = os.getenv("MODEL_XGB_PATH", "models/xgb_model.pkl")
try:
    import joblib  # for sklearn/xgboost pickles
except Exception:
    joblib = None
    _ML_ENABLED = False

# Optional: Quantum
_Q_ENABLED = os.getenv("QUANTUM_ENABLED", "0") not in ("0", "false", "False")
_QUANTUM_BACKEND_ENV = os.getenv("QUANTUM_BACKEND", "disabled")

# -----------------------------------------------------------------------------
# Config (Render → Environment)
# -----------------------------------------------------------------------------
NETLIFY_URL       = os.getenv("NETLIFY_URL", "*")
EXCHANGE_ID       = os.getenv("EXCHANGE_ID", "binance").lower()
API_KEY           = os.getenv("API_KEY", os.getenv("BINANCE_API_KEY", ""))
API_SECRET        = os.getenv("API_SECRET", os.getenv("BINANCE_API_SECRET", ""))
PRIMARY_QUOTE     = os.getenv("PRIMARY_QUOTE", "USDT").upper()

# Loops + logging
LOOP_SLEEP_S      = float(os.getenv("LOOP_SLEEP_S", "7.0"))
SIGNAL_INTERVAL_S = int(os.getenv("SIGNAL_INTERVAL_S", "30"))
EXEC_INTERVAL_S   = int(os.getenv("EXECUTION_INTERVAL_S", "20"))
LOG_LEVEL         = os.getenv("LOG_LEVEL", "INFO").upper()

# Universe
WATCHLIST_ENV     = os.getenv("TRADE_SYMBOLS", "")
WATCHLIST         = [s.strip() for s in WATCHLIST_ENV.split(",") if s.strip()]

# Signals (EMA/ML/Quantum)
TIMEFRAME         = os.getenv("TRADE_TIMEFRAME", "1h")
FAST_EMA          = int(os.getenv("TRADE_FAST_EMA", "12"))
SLOW_EMA          = int(os.getenv("TRADE_SLOW_EMA", "26"))
LOOKBACK_BARS     = int(os.getenv("TRADE_LOOKBACK_BARS", "300"))

EMA_WEIGHT        = float(os.getenv("EMA_WEIGHT", "0.50"))
ML_WEIGHT         = float(os.getenv("ML_WEIGHT", "0.40"))
Q_WEIGHT          = float(os.getenv("QUANTUM_WEIGHT", "0.10"))
MIN_CONF          = float(os.getenv("TRADE_MIN_CONF", "0.55"))

# Trading toggles (execution is not enabled in this file)
TRADE_ENABLED     = os.getenv("TRADE_ENABLED", "0") not in ("0", "false", "False")

# Cost-basis settings
COST_LOOKBACK_DAYS     = int(os.getenv("COST_BASIS_LOOKBACK_DAYS", "120"))
MAX_TRADES_PER_SYMBOL  = int(os.getenv("MAX_TRADES_PER_SYMBOL", "1000"))
FEE_IN_COST_BASIS      = os.getenv("FEE_IN_COST_BASIS", "1") not in ("0", "false", "False")
COST_CACHE_TTL_SEC     = int(os.getenv("COST_CACHE_TTL_SEC", "600"))

# -----------------------------------------------------------------------------
# App + CORS
# -----------------------------------------------------------------------------
log = logging.getLogger("BottieAPI")
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")

app = FastAPI(title="Bottie API", version="1.2.0")

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

_equity_series: List[Dict[str, Any]] = []          # [{"t": ts, "v": float}]
_positions: Dict[str, Dict[str, float]] = {}       # { "ADA/USDT": {"qty":..., "avg_px":..., "last_px":...}, ... }
_signals: List[Dict[str, Any]] = []                # [{symbol, t, signal, conf, scores, weights}]
_logs: List[str] = []

# cost-basis cache: symbol -> {"ts": last_calc, "qty": float, "avg_px": float}
_cost_basis_cache: Dict[str, Dict[str, float]] = {}

# Exchange + Models
_exchange: Optional[ccxt.Exchange] = None
_ml_model = None
_q_backend_readout: Dict[str, str] = {"kind": "none", "backend": _QUANTUM_BACKEND_ENV}

def add_log(msg: str):
    msg = msg.strip()
    _logs.append(msg)
    if len(_logs) > 1000:
        del _logs[:-1000]
    log.info(msg)

# -----------------------------------------------------------------------------
# Quantum detection (non-fatal)
# -----------------------------------------------------------------------------
def _detect_quantum() -> Dict[str, str]:
    if not _Q_ENABLED:
        return {"kind": "none", "backend": _QUANTUM_BACKEND_ENV}
    try:
        from quantum.backends import get_backend
        qb = get_backend()
        name = getattr(qb.backend, "name", None)
        name = name() if callable(name) else (name or "unknown")
        return {"kind": qb.kind, "backend": name}
    except Exception:
        return {"kind": "none", "backend": _QUANTUM_BACKEND_ENV}

# -----------------------------------------------------------------------------
# Exchange (LIVE spot)
# -----------------------------------------------------------------------------
def _init_exchange() -> ccxt.Exchange:
    if not API_KEY or not API_SECRET:
        # Allow startup without keys (service stays up; portfolio loop will log errors)
        add_log("WARNING: API_KEY/API_SECRET missing — authenticated calls will fail.")
    if EXCHANGE_ID != "binance":
        raise RuntimeError("This build is pinned to Binance. Set EXCHANGE_ID=binance.")
    klass = getattr(ccxt, EXCHANGE_ID)
    ex = klass({
        "apiKey": API_KEY,
        "secret": API_SECRET,
        "enableRateLimit": True,
    })
    # Ensure spot
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
    totals = balance.get("total") or {}
    for asset, val in totals.items():
        try:
            qty = float(val or 0.0)
        except Exception:
            qty = 0.0
        if qty > 0:
            assets[asset.upper()] = qty
    return assets

def _quote_priority() -> List[str]:
    tail = ["USDT", "USD", "BUSD", "USDC", "BTC", "ETH", "EUR", "TRY", "GBP"]
    ordered = [PRIMARY_QUOTE] + [x for x in tail if x != PRIMARY_QUOTE]
    seen, pr = set(), []
    for q in ordered:
        if q not in seen:
            seen.add(q); pr.append(q)
    return pr

def _symbol_exists(base: str, quote: str) -> bool:
    assert _exchange is not None
    return f"{base}/{quote}" in _exchange.markets

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
# Cost-basis (WAC) via trade history
# -----------------------------------------------------------------------------
def _ms_since(days: int) -> int:
    return int((time.time() - days * 86400) * 1000)

def _compute_cost_basis_for_symbol(symbol: str) -> Optional[Tuple[float, float]]:
    """
    Returns (net_qty, avg_px) using Weighted Average Cost across historical trades.
    Includes fees if configured.
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

    trades.sort(key=lambda t: t.get("timestamp") or 0)

    net_qty = 0.0
    cost    = 0.0

    base, quote = symbol.split("/")

    for t in trades:
        side   = (t.get("side") or "").lower()
        amount = float(t.get("amount") or 0.0)
        price  = float(t.get("price") or 0.0)
        fee    = t.get("fee") or {}
        fee_cost = float(fee.get("cost") or 0.0)
        fee_ccy  = (fee.get("currency") or "").upper()

        if amount <= 0 or price <= 0:
            continue

        eff_amount = amount
        eff_cost_add = 0.0
        if FEE_IN_COST_BASIS and fee_cost:
            if fee_ccy == quote:
                eff_cost_add = fee_cost
            elif fee_ccy == base:
                eff_amount = max(0.0, amount - fee_cost)

        if side == "buy":
            net_qty += eff_amount
            cost    += eff_amount * price + eff_cost_add
        elif side == "sell":
            if net_qty <= 0:
                continue
            avg_px = cost / net_qty if net_qty > 0 else 0.0
            dec_amount = min(eff_amount, net_qty)
            cost    -= avg_px * dec_amount
            net_qty -= dec_amount

    if net_qty <= 0:
        return (0.0, 0.0)

    avg_px = cost / net_qty if net_qty > 0 else 0.0
    return (net_qty, avg_px)

def _get_cost_basis(symbol: str) -> Optional[Tuple[float, float]]:
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
# Indicators / Features
# -----------------------------------------------------------------------------
def ema(series: List[float], period: int) -> List[float]:
    if period <= 1 or len(series) < period:
        return [float("nan")] * len(series)
    k = 2.0 / (period + 1.0)
    out = [float("nan")] * len(series)
    # seed with SMA
    sma = sum(series[:period]) / period
    out[period - 1] = sma
    prev = sma
    for i in range(period, len(series)):
        val = series[i] * k + prev * (1.0 - k)
        out[i] = val
        prev = val
    return out

def rsi(series: List[float], period: int = 14) -> List[float]:
    if len(series) < period + 1:
        return [float("nan")] * len(series)
    gains, losses = [], []
    out = [float("nan")] * len(series)
    for i in range(1, len(series)):
        ch = series[i] - series[i - 1]
        gains.append(max(0.0, ch))
        losses.append(max(0.0, -ch))
    # seed averages
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    rs = (avg_gain / avg_loss) if avg_loss > 0 else float("inf")
    out[period] = 100.0 - (100.0 / (1.0 + rs))
    ag, al = avg_gain, avg_loss
    for i in range(period + 1, len(series)):
        g = gains[i - 1]
        l = losses[i - 1]
        ag = (ag * (period - 1) + g) / period
        al = (al * (period - 1) + l) / period
        rs = (ag / al) if al > 0 else float("inf")
        out[i] = 100.0 - (100.0 / (1.0 + rs))
    return out

def pct_change(a: float, b: float) -> float:
    # (a/b - 1)
    try:
        if b == 0:
            return 0.0
        return (a / b) - 1.0
    except Exception:
        return 0.0

def build_features(closes: List[float]) -> Optional[List[float]]:
    """
    Returns normalized features:
    [ret3, ret8, ret21, vol20_norm, rsi14_norm] in [-1..1] where applicable.
    """
    n = len(closes)
    if n < 60:
        return None
    r3  = pct_change(closes[-1], closes[-4])     # 3 bars ago
    r8  = pct_change(closes[-1], closes[-9])
    r21 = pct_change(closes[-1], closes[-22])
    # Volatility proxy: mean abs returns last 20 bars
    rets = [pct_change(closes[i], closes[i - 1]) for i in range(1, n)]
    vol20 = sum(abs(x) for x in rets[-20:]) / 20.0 if len(rets) >= 20 else 0.0
    # Normalize roughly
    rsi14 = rsi(closes, 14)[-1]
    rsi_norm = 0.0 if math.isnan(rsi14) else (rsi14 / 100.0)  # 0..1
    vol_norm = min(1.0, max(0.0, vol20 * 10.0))               # heuristic
    # clip returns to [-1,1] for safety
    def clip01(x: float) -> float:
        return float(min(1.0, max(-1.0, x)))
    feats = [clip01(r3), clip01(r8), clip01(r21), vol_norm, rsi_norm]
    return feats

# -----------------------------------------------------------------------------
# Signals
# -----------------------------------------------------------------------------
def _get_positions_copy() -> Dict[str, Dict[str, float]]:
    return dict(_positions)

def _push_signal(sig: Dict[str, Any]):
    # keep only last one per symbol
    existing_idx = None
    for i in range(len(_signals) - 1, -1, -1):
        if _signals[i].get("symbol") == sig.get("symbol"):
            existing_idx = i
            break
    if existing_idx is not None:
        _signals[existing_idx] = sig
    else:
        _signals.append(sig)
    if len(_signals) > 500:
        del _signals[:-300]

def _universe_from_positions_and_watchlist() -> List[str]:
    """
    Build a valid list of symbols to scan:
    - Include explicit WATCHLIST
    - Include symbols we currently hold
    - Exclude BASE==QUOTE and non-listed pairs to avoid USDT/USDT etc.
    """
    assert _exchange is not None
    all_syms = set()
    for s in WATCHLIST:
        if s:
            all_syms.add(s.upper())
    for sym in _get_positions_copy().keys():
        all_syms.add(sym.upper())

    valid = []
    for sym in sorted(all_syms):
        try:
            base, quote = sym.split("/")
        except ValueError:
            continue
        if base == quote:
            continue
        if sym not in _exchange.markets:
            continue
        valid.append(sym)
    return valid

def _ema_score(closes: List[float]) -> float:
    if len(closes) < max(FAST_EMA, SLOW_EMA) + 1:
        return 0.5
    e_fast = ema(closes, FAST_EMA)[-1]
    e_slow = ema(closes, SLOW_EMA)[-1]
    if math.isnan(e_fast) or math.isnan(e_slow):
        return 0.5
    # map EMA spread to [0,1]
    spread = (e_fast - e_slow) / closes[-1]
    # squashed sigmoid-ish
    score = 1.0 / (1.0 + math.exp(-8.0 * spread))
    return float(score)

def _ml_score(feats: List[float]) -> float:
    if not _ML_ENABLED or _ml_model is None:
        return 0.5
    try:
        import numpy as np
        X = np.array(feats, dtype=float).reshape(1, -1)
        if hasattr(_ml_model, "predict_proba"):
            proba = _ml_model.predict_proba(X)[0]
            # Assume binary [bear, bull]
            score = float(proba[-1])
        else:
            # fallback to predict → map to 0/1
            pred = _ml_model.predict(X)[0]
            score = float(pred) if isinstance(pred, (int, float)) else 0.5
        return min(1.0, max(0.0, score))
    except Exception as e:
        add_log(f"ML error: {e}")
        return 0.5

def _quantum_score(feats: List[float]) -> float:
    if not _Q_ENABLED:
        return 0.5
    try:
        # Optional: if you have a quantum predictor, call it here
        # from quantum.hybrid_models import quantum_signal_score
        # return float(quantum_signal_score(feats))
        return 0.5  # neutral until wired
    except Exception as e:
        add_log(f"Quantum error: {e}")
        return 0.5

async def signals_loop():
    await _ensure_exchange()
    add_log(f"Signal loop started | TF={TIMEFRAME} | FAST={FAST_EMA} | SLOW={SLOW_EMA} | Q={_Q_ENABLED} | ML={_ML_ENABLED}")
    while True:
        try:
            assert _exchange is not None
            uni = _universe_from_positions_and_watchlist()
            if not uni:
                add_log("signals | no symbols to scan")
                await asyncio.sleep(SIGNAL_INTERVAL_S)
                continue

            for sym in uni:
                try:
                    ohlcv = _exchange.fetch_ohlcv(sym, timeframe=TIMEFRAME, limit=LOOKBACK_BARS)
                except Exception as e:
                    add_log(f"fetch_ohlcv fail {sym}: {e}")
                    continue
                if not ohlcv or len(ohlcv) < max(FAST_EMA, SLOW_EMA) + 30:
                    continue

                closes = [c[4] for c in ohlcv]
                ema_s = _ema_score(closes)
                feats = build_features(closes)
                ml_s  = _ml_score(feats) if feats else 0.5
                q_s   = _quantum_score(feats) if feats else 0.5

                # Weighted combo
                total_w = EMA_WEIGHT + ML_WEIGHT + Q_WEIGHT
                if total_w <= 0:
                    combined = 0.5
                else:
                    combined = (EMA_WEIGHT * ema_s + ML_WEIGHT * ml_s + Q_WEIGHT * q_s) / total_w

                # Map score → signal
                if combined >= MIN_CONF:
                    signal = "BUY"
                elif combined <= (1.0 - MIN_CONF):
                    signal = "SELL"
                else:
                    signal = "HOLD"

                _push_signal({
                    "symbol": sym,
                    "t": int(time.time()),
                    "signal": signal,
                    "conf": round(float(combined), 4),
                    "scores": {"ema": round(float(ema_s), 4), "ml": round(float(ml_s), 4), "q": round(float(q_s), 4)},
                    "weights": {"ema": EMA_WEIGHT, "ml": ML_WEIGHT, "q": Q_WEIGHT},
                })

            add_log(f"signals | n={len(uni)} scanned")

        except Exception as e:
            add_log(f"ERROR signals_loop: {e}")

        await asyncio.sleep(SIGNAL_INTERVAL_S)

# -----------------------------------------------------------------------------
# Portfolio valuation loop
# -----------------------------------------------------------------------------
def _value_portfolio(assets: Dict[str, float]) -> Tuple[float, Dict[str, Dict[str, float]]]:
    preferred = _quote_priority()
    symbols: List[str] = []
    chosen: Dict[str, str] = {}

    # Build symbols to quote everything into PRIMARY_QUOTE where possible
    for asset, qty in assets.items():
        if qty <= 0:
            continue
        if asset == PRIMARY_QUOTE:
            continue  # cash; value at 1
        sym = _best_symbol_for_asset(asset, preferred)
        if sym:
            chosen[asset] = sym
            symbols.append(sym)

    tick = _fetch_tickers(symbols)
    equity = 0.0
    positions: Dict[str, Dict[str, float]] = {}

    # Add cash first
    if assets.get(PRIMARY_QUOTE, 0.0) > 0.0:
        q_qty = float(assets[PRIMARY_QUOTE])
        positions[f"{PRIMARY_QUOTE}/{PRIMARY_QUOTE}"] = {"qty": q_qty, "avg_px": 1.0, "last_px": 1.0}
        equity += q_qty * 1.0

    for asset, qty in assets.items():
        if qty <= 0 or asset == PRIMARY_QUOTE:
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

        cb = _get_cost_basis(sym)
        if cb:
            cb_qty, cb_avg = cb
            avg_px = float(cb_avg) if cb_qty > 0 else float(last_px)
        else:
            avg_px = float(last_px)

        positions[sym] = {"qty": float(qty), "avg_px": float(avg_px), "last_px": float(last_px)}
        equity += qty * last_px

    return equity, positions

async def portfolio_loop():
    await _ensure_exchange()
    add_log(f"Portfolio loop started | exchange={EXCHANGE_ID} | primary_quote={PRIMARY_QUOTE} | LIVE")
    while True:
        try:
            assert _exchange is not None
            if not API_KEY or not API_SECRET:
                add_log("No API keys provided — skipping fetch_balance()")
                await asyncio.sleep(LOOP_SLEEP_S)
                continue

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
# Startup: init exchange, load ML, set quantum flag, start loops
# -----------------------------------------------------------------------------
def _load_ml():
    global _ml_model
    if not _ML_ENABLED:
        add_log("ML: disabled by env")
        return
    if joblib is None:
        add_log("ML: joblib not available; disable ML or add joblib to requirements")
        return
    try:
        _ml_model = joblib.load(_MODEL_PATH)
        # quick sanity check
        if not (hasattr(_ml_model, "predict") or hasattr(_ml_model, "predict_proba")):
            add_log(f"ML: model at {_MODEL_PATH} lacks predict/predict_proba; ignoring")
            _ml_model = None
            return
        add_log(f"ML: loaded model {_MODEL_PATH}")
    except Exception as e:
        add_log(f"ML: model not loaded; falling back to EMA/quantum only ({e})")

@app.on_event("startup")
async def _on_startup():
    global _q_backend_readout
    _q_backend_readout = _detect_quantum()
    _load_ml()
    asyncio.create_task(portfolio_loop())
    asyncio.create_task(signals_loop())
    add_log("Startup complete.")

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
        "quantum": _q_backend_readout,
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

@app.get("/signals")
def get_signals():
    return {"symbols": [s["symbol"] for s in _signals[-200:]], "items": _signals[-200:]}

@app.get("/logs/last")
def logs_last():
    return {"logs": _logs[-300:]}

@app.get("/costbasis")
def costbasis():
    out = {}
    for sym, entry in _cost_basis_cache.items():
        out[sym] = {"qty": entry["qty"], "avg_px": entry["avg_px"], "age_sec": time.time() - entry["ts"]}
    return out