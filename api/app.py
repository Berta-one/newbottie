# api/app.py
# FastAPI backend for Bottie (live portfolio, signals, ML, optional quantum)
import os, time, asyncio, logging, math, json, hashlib, random
from typing import Any, Dict, List, Optional, Tuple, Set

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ──────────────────────────────────────────────────────────────────────────────
# Optional imports guarded so the app can boot even if some wheels are missing
# ──────────────────────────────────────────────────────────────────────────────
try:
    import ccxt
except Exception as e:
    raise RuntimeError(f"ccxt not installed. Add to requirements.txt: {e}")

try:
    import pandas as pd
    import numpy as np
except Exception as e:
    raise RuntimeError(f"pandas / numpy required. Add to requirements.txt: {e}")

try:
    import joblib  # model loader
except Exception:
    joblib = None

# Qiskit is optional; we fall back gracefully if not present.
try:
    from qiskit import QuantumCircuit
    from qiskit_aer import Aer
except Exception:
    QuantumCircuit = None
    Aer = None

# ──────────────────────────────────────────────────────────────────────────────
# Config (Render → Environment)
# ──────────────────────────────────────────────────────────────────────────────
LOG_LEVEL               = os.getenv("LOG_LEVEL", "INFO").upper()
NETLIFY_URL             = os.getenv("NETLIFY_URL", "*")

EXCHANGE_ID             = os.getenv("EXCHANGE_ID", "binance").lower()
API_KEY                 = os.getenv("BINANCE_API_KEY", os.getenv("API_KEY", "")).strip()
API_SECRET              = os.getenv("BINANCE_API_SECRET", os.getenv("API_SECRET", "")).strip()
API_PASSPHRASE          = os.getenv("API_PASSPHRASE", "").strip()  # coinbaseadvanced
API_UID                 = os.getenv("API_UID", "").strip()          # bitstamp

PRIMARY_QUOTE           = os.getenv("PRIMARY_QUOTE", "USDT").upper()
LOOP_SLEEP_S            = float(os.getenv("LOOP_SLEEP_S", "6"))      # portfolio loop
SIGNAL_INTERVAL_S       = float(os.getenv("SIGNAL_INTERVAL_S", "30"))

# Cost basis (trade history → weighted average cost)
COST_LOOKBACK_DAYS      = int(os.getenv("COST_BASIS_LOOKBACK_DAYS", "120"))
MAX_TRADES_PER_SYMBOL   = int(os.getenv("MAX_TRADES_PER_SYMBOL", "1000"))
FEE_IN_COST_BASIS       = os.getenv("FEE_IN_COST_BASIS", "1").lower() in ("1","true","yes")
COST_CACHE_TTL_SEC      = int(os.getenv("COST_CACHE_TTL_SEC", "600"))

# Signals / features
TRADE_TIMEFRAME         = os.getenv("TRADE_TIMEFRAME", "1h")
TRADE_LOOKBACK_BARS     = int(os.getenv("TRADE_LOOKBACK_BARS", "300"))
TRADE_FAST_EMA          = int(os.getenv("TRADE_FAST_EMA", "12"))
TRADE_SLOW_EMA          = int(os.getenv("TRADE_SLOW_EMA", "26"))
TRADE_MIN_CONF          = float(os.getenv("TRADE_MIN_CONF", "0.55"))
TRADE_SYMBOLS_ENV       = os.getenv("TRADE_SYMBOLS", "")  # optional extra list, CSV

# Weights (do not need to sum to 1; we normalize)
EMA_WEIGHT              = float(os.getenv("EMA_WEIGHT", "0.65"))
ML_WEIGHT               = float(os.getenv("ML_WEIGHT", "0.25"))
QUANTUM_WEIGHT          = float(os.getenv("QUANTUM_WEIGHT", "0.35"))

# ML model files (XGBoost via joblib)
ML_ENABLED              = os.getenv("ML_ENABLED", "1").lower() in ("1","true","yes")
MODEL_XGB_PATH          = os.getenv("MODEL_XGB_PATH", "models/xgb_model.pkl")
MODEL_META_PATH         = os.getenv("MODEL_META_PATH", "models/xgb_meta.json")

# Quantum flags
QUANTUM_ENABLED         = os.getenv("QUANTUM_ENABLED", "0").lower() in ("1","true","yes")
QUANTUM_BACKEND         = os.getenv("QUANTUM_BACKEND", "aer_simulator")  # or ibmq_qasm_simulator (if wired)

# ──────────────────────────────────────────────────────────────────────────────
# Logging & App
# ──────────────────────────────────────────────────────────────────────────────
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
log = logging.getLogger("BottieAPI")

app = FastAPI(title="Bottie API", version="1.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[NETLIFY_URL] if NETLIFY_URL != "*" else ["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS", "HEAD"],
    allow_headers=["*"],
)

# Optional Admin UI / WS (safe if file not present)
try:
    from api.admin import router as admin_router, wire_admin_startup
    app.include_router(admin_router)
except Exception as e:
    log.info(f"Admin module not wired: {e}")
    wire_admin_startup = None  # type: ignore

# ──────────────────────────────────────────────────────────────────────────────
# In-memory state
# ──────────────────────────────────────────────────────────────────────────────
_started = time.time()
_equity_series: List[Dict[str, Any]] = []
_positions: Dict[str, Dict[str, float]] = {}   # symbol → {qty, avg_px, last_px}
_signals: List[Dict[str, Any]] = []            # [{symbol, signal, conf, ema, ml, q, t}]
_logs: List[str] = []
_cost_basis_cache: Dict[str, Dict[str, float]] = {}  # symbol → {ts, qty, avg_px}

def add_log(msg: str):
    msg = msg.strip()
    _logs.append(msg)
    if len(_logs) > 1000:
        del _logs[:-700]
    log.info(msg)

# ──────────────────────────────────────────────────────────────────────────────
# Exchange
# ──────────────────────────────────────────────────────────────────────────────
_exchange: Optional[ccxt.Exchange] = None

def _init_exchange() -> ccxt.Exchange:
    if EXCHANGE_ID not in ccxt.exchanges:
        raise RuntimeError(f"Exchange '{EXCHANGE_ID}' not supported by ccxt.")
    klass = getattr(ccxt, EXCHANGE_ID)
    params: Dict[str, Any] = {"enableRateLimit": True}
    # Auth is required for balance/trades; signals can use public OHLCV
    if API_KEY and API_SECRET:
        params.update({"apiKey": API_KEY, "secret": API_SECRET})
    if EXCHANGE_ID == "coinbaseadvanced" and API_PASSPHRASE:
        params["password"] = API_PASSPHRASE
    if EXCHANGE_ID == "bitstamp" and API_UID:
        params["uid"] = API_UID
    ex = klass(params)
    # Spot by default
    if hasattr(ex, "options"):
        ex.options = {**getattr(ex, "options", {}), **{"defaultType": "spot"}}
    add_log(f"Exchange initialized: {EXCHANGE_ID} ({'LIVE' if API_KEY and API_SECRET else 'PUBLIC-ONLY'})")
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

def _symbol_exists(base: str, quote: str) -> bool:
    assert _exchange is not None
    return f"{base}/{quote}" in _exchange.markets

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────
def _nonzero_assets_from_balance(balance: Dict[str, Any]) -> Dict[str, float]:
    assets: Dict[str, float] = {}
    total = balance.get("total") or {}
    for asset, qty in total.items():
        try:
            v = float(qty or 0.0)
        except Exception:
            v = 0.0
        if v > 0:
            assets[asset.upper()] = v
    return assets

def _quote_priority() -> List[str]:
    tail = ["USDT", "USD", "BUSD", "USDC", "BTC", "ETH", "EUR", "TRY", "GBP"]
    if PRIMARY_QUOTE in tail:
        tail.remove(PRIMARY_QUOTE)
    return [PRIMARY_QUOTE] + tail

def _best_symbol_for_asset(asset: str, preferred_quotes: List[str]) -> Optional[str]:
    assert _exchange is not None
    for q in preferred_quotes:
        sym = f"{asset}/{q}"
        if sym in _exchange.markets:
            return sym
    return None

def _fetch_tickers(symbols: List[str]) -> Dict[str, Any]:
    assert _exchange is not None
    syms = [s for s in symbols if s != f"{PRIMARY_QUOTE}/{PRIMARY_QUOTE}"]
    if not syms:
        return {}
    try:
        return _exchange.fetch_tickers(syms) or {}
    except Exception as e:
        add_log(f"ERROR fetch_tickers: {e}")
        return {}

def _ms_since(days: int) -> int:
    return int((time.time() - days * 86400) * 1000)

# ──────────────────────────────────────────────────────────────────────────────
# Cost-basis via WAC from trade history (with fees)
# ──────────────────────────────────────────────────────────────────────────────
def _compute_cost_basis_for_symbol(symbol: str) -> Optional[Tuple[float, float]]:
    assert _exchange is not None
    if not (API_KEY and API_SECRET):
        return None
    since = _ms_since(COST_LOOKBACK_DAYS)
    limit = MAX_TRADES_PER_SYMBOL
    try:
        trades = _exchange.fetch_my_trades(symbol, since=since, limit=limit)
    except ccxt.ExchangeError as e:
        if "451" in str(e) or "restricted" in str(e).lower():
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
    cost = 0.0
    base, quote = symbol.split("/")

    for t in trades:
        side = (t.get("side") or "").lower()
        amount = float(t.get("amount") or 0.0)  # base
        price = float(t.get("price") or 0.0)    # quote per base
        if amount <= 0 or price <= 0:
            continue

        eff_amount = amount
        eff_cost_add = 0.0
        if FEE_IN_COST_BASIS:
            fee = t.get("fee") or {}
            fee_cost = float(fee.get("cost") or 0.0)
            fee_ccy = (fee.get("currency") or "").upper()
            if fee_cost:
                if fee_ccy == quote.upper():
                    eff_cost_add = fee_cost               # extra quote spent
                elif fee_ccy == base.upper():
                    eff_amount = max(0.0, amount - fee_cost)  # reduce base acquired/sold

        if side == "buy":
            net_qty += eff_amount
            cost    += eff_amount * price + eff_cost_add
        elif side == "sell":
            if net_qty <= 0:
                continue
            avg_px = cost / net_qty if net_qty > 0 else 0.0
            dec = min(eff_amount, net_qty)
            cost -= avg_px * dec
            net_qty -= dec

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

# ──────────────────────────────────────────────────────────────────────────────
# Portfolio valuation loop
# ──────────────────────────────────────────────────────────────────────────────
def _value_portfolio(assets: Dict[str, float]) -> Tuple[float, Dict[str, Dict[str, float]]]:
    preferred = _quote_priority()
    assert _exchange is not None

    chosen: Dict[str, str] = {}
    symbols: List[str] = []
    for asset, qty in assets.items():
        if asset == PRIMARY_QUOTE:
            continue
        sym = _best_symbol_for_asset(asset, preferred)
        if sym:
            chosen[asset] = sym
            symbols.append(sym)

    tick = _fetch_tickers(symbols)
    equity = 0.0
    positions: Dict[str, Dict[str, float]] = {}

    # quote "cash"
    cash_qty = float(assets.get(PRIMARY_QUOTE, 0.0))
    if cash_qty > 0:
        equity += cash_qty
        positions[f"{PRIMARY_QUOTE}/{PRIMARY_QUOTE}"] = {"qty": cash_qty, "avg_px": 1.0, "last_px": 1.0}

    for asset, qty in assets.items():
        if qty <= 0 or asset == PRIMARY_QUOTE:
            continue
        sym = chosen.get(asset)
        if not sym:
            add_log(f"Skip valuation for {asset} (no direct market to {PRIMARY_QUOTE} or alternatives)")
            continue
        info = tick.get(sym) or {}
        last_px = float(info.get("last") or info.get("close") or 0.0)
        if last_px <= 0:
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
    add_log(f"Portfolio loop started | exchange={EXCHANGE_ID} | primary_quote={PRIMARY_QUOTE}")
    assert _exchange is not None
    while True:
        try:
            if API_KEY and API_SECRET:
                bal = _exchange.fetch_balance(params={})
            else:
                # Public-only mode cannot fetch private balance; show empty
                bal = {"total": {}}
            assets = _nonzero_assets_from_balance(bal)
            equity, pos = _value_portfolio(assets)
            ts = int(time.time())
            _equity_series.append({"t": ts, "v": float(equity)})
            if len(_equity_series) > 2000:
                del _equity_series[:-1000]
            _positions.clear()
            _positions.update(pos)
            add_log(f"snapshot | equity={equity:.2f} positions={len(_positions)}")
        except ccxt.ExchangeError as e:
            if "451" in str(e) or "restricted" in str(e).lower():
                add_log("Geo-restricted by venue for authenticated calls. Use a permitted region/venue.")
            else:
                add_log(f"Exchange error: {e}")
        except Exception as e:
            add_log(f"ERROR portfolio_loop: {e}")
        await asyncio.sleep(LOOP_SLEEP_S)

# ──────────────────────────────────────────────────────────────────────────────
# Simple technical features & EMA signal
# ──────────────────────────────────────────────────────────────────────────────
def _ema(arr: np.ndarray, span: int) -> np.ndarray:
    if len(arr) < span + 2:
        return np.full_like(arr, np.nan, dtype=float)
    return pd.Series(arr).ewm(span=span, adjust=False).mean().values

def _rsi(arr: np.ndarray, period: int = 14) -> np.ndarray:
    if len(arr) <= period + 1:
        return np.full_like(arr, np.nan, dtype=float)
    delta = np.diff(arr)
    up = np.where(delta > 0, delta, 0.0)
    down = np.where(delta < 0, -delta, 0.0)
    roll_up = pd.Series(up).rolling(period).mean()
    roll_down = pd.Series(down).rolling(period).mean()
    rs = roll_up / (roll_down + 1e-12)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return np.concatenate([[np.nan], rsi.values])

def _build_features(ohlcv: List[List[float]]) -> Dict[str, Any]:
    # ohlcv: [ [ts, open, high, low, close, volume], ... ]
    if not ohlcv or len(ohlcv) < max(TRADE_SLOW_EMA + 2, 50):
        return {"ok": False}
    arr = np.array(ohlcv, dtype=float)
    close = arr[:, 4]
    vol = arr[:, 5]
    ema_fast = _ema(close, TRADE_FAST_EMA)
    ema_slow = _ema(close, TRADE_SLOW_EMA)
    rsi14 = _rsi(close, 14)
    ret1 = np.zeros_like(close)
    ret1[1:] = (close[1:] - close[:-1]) / (close[:-1] + 1e-12)

    feats = {
        "close": close,
        "vol": vol,
        "ema_fast": ema_fast,
        "ema_slow": ema_slow,
        "rsi14": rsi14,
        "ret1": ret1,
    }
    return {"ok": True, "features": feats}

def _ema_score(feats: Dict[str, Any]) -> float:
    ef = feats["ema_fast"][-1]
    es = feats["ema_slow"][-1]
    if math.isnan(ef) or math.isnan(es):
        return 0.0
    # scale diff to [-1,1] by dividing by price
    px = feats["close"][-1]
    diff = (ef - es) / max(1e-8, px)
    # squash
    return float(max(-1.0, min(1.0, diff * 50.0)))

# ──────────────────────────────────────────────────────────────────────────────
# ML model loader & prediction
# ──────────────────────────────────────────────────────────────────────────────
_ML_MODEL = None
_ML_META: Dict[str, Any] = {}

def _load_ml():
    global _ML_MODEL, _ML_META
    if not ML_ENABLED or not joblib:
        add_log("ML disabled or joblib missing; EMA/quantum only.")
        return
    try:
        if os.path.exists(MODEL_XGB_PATH):
            _ML_MODEL = joblib.load(MODEL_XGB_PATH)
            add_log(f"ML: loaded model {MODEL_XGB_PATH}")
        else:
            add_log("ML: model not loaded; file not found.")
        if os.path.exists(MODEL_META_PATH):
            with open(MODEL_META_PATH, "r") as f:
                _ML_META = json.load(f)
        else:
            _ML_META = {}
    except Exception as e:
        add_log(f"ML load error: {e}")
        _ML_MODEL = None
        _ML_META = {}

def _ml_score(feats: Dict[str, Any]) -> Optional[float]:
    if not _ML_MODEL:
        return None
    # Build 1-row feature vector aligned to what trainer produced
    try:
        close = feats["close"]
        rsi = feats["rsi14"]
        ret1 = feats["ret1"]
        emaf = feats["ema_fast"]
        emas = feats["ema_slow"]
        vol = feats["vol"]
        x = np.array([[
            close[-1],
            rsi[-1] if not np.isnan(rsi[-1]) else 50.0,
            ret1[-1],
            emaf[-1],
            emas[-1],
            vol[-1],
        ]], dtype=float)
        # If the model has predict_proba → use probability of "up" class
        if hasattr(_ML_MODEL, "predict_proba"):
            proba = _ML_MODEL.predict_proba(x)
            # assume binary [down, up]
            if proba.shape[1] == 2:
                return float(proba[0, 1])
            # else fallback to mean
            return float(np.mean(proba[0]))
        # Else try decision_function or predict → squash to 0..1
        if hasattr(_ML_MODEL, "decision_function"):
            s = float(_ML_MODEL.decision_function(x)[0])
            return 1.0 / (1.0 + math.exp(-s))
        if hasattr(_ML_MODEL, "predict"):
            y = _ML_MODEL.predict(x)
            # map to 0..1 best-effort
            return float(0.5 + 0.5 * np.clip(y[0], -1, 1))
    except Exception as e:
        add_log(f"ML score error: {e}")
    return None

# ──────────────────────────────────────────────────────────────────────────────
# Optional quantum score
# ──────────────────────────────────────────────────────────────────────────────
def _quantum_score(symbol: str, feats: Dict[str, Any]) -> Optional[float]:
    if not QUANTUM_ENABLED:
        return None
    # If qiskit-aer is missing, gracefully degrade to a deterministic pseudo-score
    if QuantumCircuit is None or Aer is None:
        # deterministic pseudo-random in [0,1) per symbol and latest price
        h = hashlib.sha256(f"{symbol}:{feats['close'][-1]:.8f}".encode()).hexdigest()
        return (int(h[:8], 16) % 1000) / 1000.0
    try:
        # Tiny circuit seeded by last price bits → measure |1> prob
        px = feats["close"][-1]
        seed = int((px * 1e6) % (2**16))
        random.seed(seed)
        theta = (px % 6.283185307179586)  # mod 2π
        qc = QuantumCircuit(1, 1)
        qc.ry(theta, 0)
        qc.measure(0, 0)
        backend = Aer.get_backend("aer_simulator")
        shots = 512
        result = backend.run(qc, shots=shots).result()
        counts = result.get_counts()
        p1 = counts.get("1", 0) / shots
        return float(p1)
    except Exception as e:
        add_log(f"Quantum score error: {e}")
        return None

# ──────────────────────────────────────────────────────────────────────────────
# Signals loop
# ──────────────────────────────────────────────────────────────────────────────
def _symbols_to_scan() -> List[str]:
    assert _exchange is not None
    syms: Set[str] = set()
    # from live positions
    for sym in _positions.keys():
        if sym.endswith(f"/{PRIMARY_QUOTE}") and not sym.startswith(f"{PRIMARY_QUOTE}/"):
            syms.add(sym)
    # from env list
    if TRADE_SYMBOLS_ENV.strip():
        for s in TRADE_SYMBOLS_ENV.split(","):
            s = s.strip().upper()
            if not s:
                continue
            if s in _exchange.markets:
                syms.add(s)
    # avoid quote/quote nonsense
    syms = {s for s in syms if s != f"{PRIMARY_QUOTE}/{PRIMARY_QUOTE}"}
    return sorted(syms)

def _push_signal(sig: Dict[str, Any]):
    # keep only last one per symbol
    for i in range(len(_signals) - 1, -1, -1):
        if _signals[i].get("symbol") == sig.get("symbol"):
            _signals[i] = sig
            break
    else:
        _signals.append(sig)
    if len(_signals) > 1000:
        del _signals[:-700]

async def signals_loop():
    await _ensure_exchange()
    _load_ml()
    add_log(f"Signal loop started | TF={TRADE_TIMEFRAME} | FAST={TRADE_FAST_EMA} | SLOW={TRADE_SLOW_EMA} | Q={QUANTUM_ENABLED} | ML={ML_ENABLED}")
    assert _exchange is not None

    while True:
        t0 = time.time()
        try:
            scan = _symbols_to_scan()
            n_scanned = 0
            for sym in scan:
                # fetch OHLCV
                try:
                    data = _exchange.fetch_ohlcv(sym, timeframe=TRADE_TIMEFRAME, limit=TRADE_LOOKBACK_BARS)
                except Exception as e:
                    add_log(f"fetch_ohlcv fail {sym}: {e}")
                    continue
                if not data or len(data) < max(TRADE_SLOW_EMA + 2, 50):
                    continue

                f = _build_features(data)
                if not f["ok"]:
                    continue
                feats = f["features"]

                # EMA score → [-1,1] → map to [0,1] for blending
                ema_s = _ema_score(feats)
                ema_prob = 0.5 + 0.5 * np.clip(ema_s, -1, 1)

                # ML probability in [0,1]
                ml_prob = _ml_score(feats)
                # Quantum probability in [0,1]
                q_prob = _quantum_score(sym, feats)

                # Blend
                parts = []
                weights = []
                parts.append(ema_prob); weights.append(EMA_WEIGHT)
                if ml_prob is not None:
                    parts.append(ml_prob); weights.append(ML_WEIGHT)
                if q_prob is not None:
                    parts.append(q_prob); weights.append(QUANTUM_WEIGHT)

                if sum(weights) <= 0:
                    final_prob = ema_prob  # fallback
                else:
                    w = np.array(weights, dtype=float)
                    w = w / np.sum(w)
                    p = np.array(parts, dtype=float)
                    final_prob = float(np.sum(w * p))

                # Translate to signal
                # BUY if prob >= (0.5 + min_conf/2), SELL if <= (0.5 - min_conf/2)
                # This keeps symmetric threshold around 0.5
                thr_buy = 0.5 + 0.5 * TRADE_MIN_CONF
                thr_sell = 0.5 - 0.5 * TRADE_MIN_CONF
                if final_prob >= thr_buy:
                    sig = "BUY"
                    conf = final_prob
                elif final_prob <= thr_sell:
                    sig = "SELL"
                    conf = 1.0 - final_prob
                else:
                    sig = "HOLD"
                    conf = abs(final_prob - 0.5) * 2.0  # 0..1 centered

                _push_signal({
                    "symbol": sym,
                    "signal": sig,
                    "conf": round(float(conf), 4),
                    "ema": round(float(ema_prob), 4),
                    "ml": (None if ml_prob is None else round(float(ml_prob), 4)),
                    "q": (None if q_prob is None else round(float(q_prob), 4)),
                    "t": int(time.time())
                })
                n_scanned += 1

            add_log(f"signals | n={n_scanned} scanned")
        except Exception as e:
            add_log(f"ERROR signals_loop: {e}")

        # sleep remainder of interval
        dt = time.time() - t0
        await asyncio.sleep(max(0.25, SIGNAL_INTERVAL_S - dt))

# ──────────────────────────────────────────────────────────────────────────────
# Startup
# ──────────────────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def _on_startup():
    # Start portfolio valuation loop (works public-only too; shows empty if no keys)
    asyncio.create_task(portfolio_loop())
    # Start signals loop
    asyncio.create_task(signals_loop())
    # Wire admin auto-train scheduler if available
    if wire_admin_startup:
        wire_admin_startup(app)

# ──────────────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────────────
def _detect_quantum() -> Dict[str, Any]:
    if not QUANTUM_ENABLED:
        return {"enabled": False, "backend": "disabled"}
    if QuantumCircuit is None or Aer is None:
        return {"enabled": True, "backend": "pseudo (no qiskit-aer)"}
    return {"enabled": True, "backend": QUANTUM_BACKEND or "aer_simulator"}

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
        "exchange": EXCHANGE_ID,
        "primary_quote": PRIMARY_QUOTE,
        "equity": last_eq,
        "quantum": _detect_quantum(),
        "ml": {
            "enabled": ML_ENABLED,
            "loaded": bool(_ML_MODEL),
            "model_path": MODEL_XGB_PATH if _ML_MODEL else None,
        },
    }

@app.get("/status")
def status():
    last_eq = _equity_series[-1]["v"] if _equity_series else None
    return {
        "started_at": _started,
        "equity": last_eq,
        "equity_series": _equity_series[-300:],
        "positions": _positions,
        "last_signals": _signals[-200:],
    }

@app.get("/signals")
def signals():
    return {"signals": _signals[-300:]}

@app.get("/logs/last")
def logs_last():
    return {"logs": _logs[-300:]}

@app.get("/costbasis")
def costbasis():
    out = {}
    for sym, entry in _cost_basis_cache.items():
        out[sym] = {"qty": entry["qty"], "avg_px": entry["avg_px"], "age_sec": time.time() - entry["ts"]}
    return out