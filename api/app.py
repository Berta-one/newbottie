# api/app.py
import os, time, asyncio, logging, math, json, hashlib
from typing import Any, Dict, List, Optional, Tuple, Set

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ────────────── deps
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
    import joblib
except Exception:
    joblib = None

# Quantum (optional)
try:
    from qiskit import QuantumCircuit
    from qiskit_aer import Aer
except Exception:
    QuantumCircuit = None
    Aer = None

# Sentiment (Finnhub + VADER) — our module
try:
    from sentiment.sentiment_service import snapshot as sentiment_snapshot, latest_probs as sentiment_latest_probs
    SENTIMENT_WIRED = True
except Exception:
    SENTIMENT_WIRED = False

# ────────────── ENV
LOG_LEVEL         = os.getenv("LOG_LEVEL", "INFO").upper()
NETLIFY_URL       = os.getenv("NETLIFY_URL", "*")

EXCHANGE_ID       = os.getenv("EXCHANGE_ID", "binance").lower()
API_KEY           = os.getenv("BINANCE_API_KEY", os.getenv("API_KEY", "")).strip()
API_SECRET        = os.getenv("BINANCE_API_SECRET", os.getenv("API_SECRET", "")).strip()
API_PASSPHRASE    = os.getenv("API_PASSPHRASE", "").strip()  # coinbaseadvanced
API_UID           = os.getenv("API_UID", "").strip()          # bitstamp

PRIMARY_QUOTE     = os.getenv("PRIMARY_QUOTE", "USDT").upper()
LOOP_SLEEP_S      = float(os.getenv("LOOP_SLEEP_S", "6"))
SIGNAL_INTERVAL_S = float(os.getenv("SIGNAL_INTERVAL_S", "30"))

COST_LOOKBACK_DAYS    = int(os.getenv("COST_BASIS_LOOKBACK_DAYS", "120"))
MAX_TRADES_PER_SYMBOL = int(os.getenv("MAX_TRADES_PER_SYMBOL", "1000"))
FEE_IN_COST_BASIS     = os.getenv("FEE_IN_COST_BASIS", "1").lower() in ("1","true","yes")
COST_CACHE_TTL_SEC    = int(os.getenv("COST_CACHE_TTL_SEC", "600"))

TRADE_TIMEFRAME       = os.getenv("TRADE_TIMEFRAME", "1h")
TRADE_LOOKBACK_BARS   = int(os.getenv("TRADE_LOOKBACK_BARS", "300"))
TRADE_FAST_EMA        = int(os.getenv("TRADE_FAST_EMA", "12"))
TRADE_SLOW_EMA        = int(os.getenv("TRADE_SLOW_EMA", "26"))
TRADE_MIN_CONF        = float(os.getenv("TRADE_MIN_CONF", "0.55"))  # used for UI thresholds; sizing uses strength

# dynamic symbol set = all portfolio symbols + optional extra
TRADE_SYMBOLS_ENV     = os.getenv("TRADE_SYMBOLS", "")

# weights (normalized in combine)
EMA_WEIGHT            = float(os.getenv("EMA_WEIGHT", "0.65"))
ML_WEIGHT             = float(os.getenv("ML_WEIGHT", "0.25"))
QUANTUM_WEIGHT        = float(os.getenv("QUANTUM_WEIGHT", "0.35"))
SENTIMENT_WEIGHT      = float(os.getenv("SENTIMENT_WEIGHT", "0.20"))

# ML
ML_ENABLED            = os.getenv("ML_ENABLED", "1").lower() in ("1","true","yes")
MODEL_XGB_PATH       = os.getenv("MODEL_XGB_PATH", "models/xgb_model.pkl")
MODEL_META_PATH      = os.getenv("MODEL_META_PATH", "models/xgb_meta.json")
AUTO_TRAIN_ON_START  = os.getenv("AUTO_TRAIN_ON_START", "0").lower() in ("1","true","yes")
TRAIN_SYMBOLS_ENV    = os.getenv("TRAIN_SYMBOLS", "BTC/USDT,ETH/USDT")
TRAIN_TIMEFRAME      = os.getenv("TRAIN_TIMEFRAME", "1h")
TRAIN_LIMIT          = int(os.getenv("TRAIN_LIMIT", "600"))

# Quantum
QUANTUM_ENABLED       = os.getenv("QUANTUM_ENABLED", "0").lower() in ("1","true","yes")
QUANTUM_BACKEND       = os.getenv("QUANTUM_BACKEND", "aer_simulator")

# Sentiment
SENTIMENT_ENABLED     = os.getenv("SENTIMENT_ENABLED", "1").lower() in ("1","true","yes")

# Execution / risk
TRADE_ENABLED         = os.getenv("TRADE_ENABLED", "0").lower() in ("1","true","yes")
EXECUTION_INTERVAL_S  = float(os.getenv("EXECUTION_INTERVAL_S", "20"))

# strength gate + cooldown
MIN_STRENGTH_TO_TRADE = float(os.getenv("MIN_STRENGTH_TO_TRADE", "0.20"))
MIN_SECS_BETWEEN_TRADES = float(os.getenv("MIN_SECS_BETWEEN_TRADES", "120"))

# sizing & caps
TRADE_QUOTE_PER_ORDER = float(os.getenv("TRADE_QUOTE_PER_ORDER", "100"))  # base unit
SIZE_ALPHA            = float(os.getenv("SIZE_ALPHA", "1.2"))             # convexity for buy unit
BUY_MAX_MULTIPLIER    = float(os.getenv("BUY_MAX_MULTIPLIER", "2.0"))     # cap * base unit
BUY_MIN_USDT          = float(os.getenv("BUY_MIN_USDT", "12"))            # ensure > most minNotional

MAX_OPEN_POSITIONS    = int(os.getenv("MAX_OPEN_POSITIONS", "10"))
MAX_SPEND_PER_SYMBOL  = float(os.getenv("MAX_SPEND_PER_SYMBOL", "1000"))

SELL_MIN_FRAC         = float(os.getenv("SELL_MIN_FRAC", "0.25"))
SELL_MAX_FRAC         = float(os.getenv("SELL_MAX_FRAC", "1.0"))

# ────────────── App
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
log = logging.getLogger("BottieAPI")

app = FastAPI(title="Bottie API", version="1.6.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[NETLIFY_URL] if NETLIFY_URL != "*" else ["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS", "HEAD"],
    allow_headers=["*"],
)

# ────────────── State
_started = time.time()
_equity_series: List[Dict[str, Any]] = []
_positions: Dict[str, Dict[str, float]] = {}   # sym -> {qty, avg_px, last_px}
_signals: List[Dict[str, Any]] = []
_logs: List[str] = []
_cost_basis_cache: Dict[str, Dict[str, float]] = {}

# execution state
_last_trade_ts: Dict[str, float] = {}          # sym -> last order ts
_market_filters: Dict[str, Dict[str, float]] = {}  # sym -> {"stepSize","minNotional"}

def add_log(msg: str):
    _logs.append(msg)
    if len(_logs) > 1500:
        del _logs[:-1000]
    log.info(msg)

# ────────────── Exchange
_exchange: Optional[ccxt.Exchange] = None

def _init_exchange() -> ccxt.Exchange:
    if EXCHANGE_ID not in ccxt.exchanges:
        raise RuntimeError(f"Exchange '{EXCHANGE_ID}' not supported by ccxt.")
    klass = getattr(ccxt, EXCHANGE_ID)
    params: Dict[str, Any] = {"enableRateLimit": True}
    if API_KEY and API_SECRET:
        params.update({"apiKey": API_KEY, "secret": API_SECRET})
    if EXCHANGE_ID == "coinbaseadvanced" and API_PASSPHRASE:
        params["password"] = API_PASSPHRASE
    if EXCHANGE_ID == "bitstamp" and API_UID:
        params["uid"] = API_UID
    ex = klass(params)
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

# ────────────── Helpers
def _nonzero_assets_from_balance(balance: Dict[str, Any]) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for a, v in (balance.get("total") or {}).items():
        try:
            f = float(v or 0.0)
        except Exception:
            f = 0.0
        if f > 0:
            out[a.upper()] = f
    return out

def _quote_priority() -> List[str]:
    tail = ["USDT","USD","BUSD","USDC","BTC","ETH","EUR","TRY","GBP"]
    if PRIMARY_QUOTE in tail:
        tail.remove(PRIMARY_QUOTE)
    return [PRIMARY_QUOTE] + tail

def _best_symbol_for_asset(asset: str, preferred_quotes: List[str]) -> Optional[str]:
    assert _exchange is not None
    for q in preferred_quotes:
        s = f"{asset}/{q}"
        if s in _exchange.markets:
            return s
    return None

def _fetch_tickers(symbols: List[str]) -> Dict[str, Any]:
    assert _exchange is not None
    syms = [s for s in symbols if not s.startswith(f"{PRIMARY_QUOTE}/") and s != f"{PRIMARY_QUOTE}/{PRIMARY_QUOTE}"]
    if not syms:
        return {}
    try:
        return _exchange.fetch_tickers(syms) or {}
    except Exception as e:
        add_log(f"ERROR fetch_tickers: {e}")
        return {}

def _ms_since(days: int) -> int:
    return int((time.time() - days * 86400) * 1000)

# ────────────── Binance filters
def _round_step(qty: float, step: float) -> float:
    if step <= 0:
        return qty
    precision = max(0, int(round(-math.log10(step) + 1e-8)))
    # floor to step
    return math.floor(qty / step) * step if step >= 1e-12 else float(f"{qty:.{precision}f}")

def _binance_filters(sym: str) -> Dict[str, float]:
    """Cache stepSize & minNotional from market info."""
    if sym in _market_filters:
        return _market_filters[sym]
    try:
        m = _exchange.market(sym)  # type: ignore
        step = 0.0
        min_not = 10.0
        info = m.get("info", {})
        # Extract stepSize
        try:
            fl = info.get("filters", [])
            for f in fl:
                if f.get("filterType") == "LOT_SIZE":
                    step = float(f.get("stepSize", "0"))
                if f.get("filterType") == "NOTIONAL":
                    min_not = float(f.get("minNotional", "10"))
        except Exception:
            pass
        if step <= 0:
            step = float(m.get("precision", {}).get("amount", 0)) or 0.00000001
        _market_filters[sym] = {"stepSize": float(step or 0.00000001), "minNotional": float(min_not or 10.0)}
    except Exception:
        _market_filters[sym] = {"stepSize": 0.00000001, "minNotional": 10.0}
    return _market_filters[sym]

def _can_open_more_positions() -> bool:
    # count positions with qty > 0 and not the cash/cash
    n = sum(1 for k, v in _positions.items() if k.endswith(f"/{PRIMARY_QUOTE}") and k != f"{PRIMARY_QUOTE}/{PRIMARY_QUOTE}" and float(v.get("qty", 0)) > 0)
    return n < MAX_OPEN_POSITIONS

# ────────────── Cost basis (WAC)
def _compute_cost_basis_for_symbol(symbol: str) -> Optional[Tuple[float, float]]:
    assert _exchange is not None
    if not (API_KEY and API_SECRET):
        return None
    since = _ms_since(COST_LOOKBACK_DAYS)
    try:
        trades = _exchange.fetch_my_trades(symbol, since=since, limit=MAX_TRADES_PER_SYMBOL)
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
    net_qty, cost = 0.0, 0.0
    base, quote = symbol.split("/")
    for t in trades:
        side = (t.get("side") or "").lower()
        amount = float(t.get("amount") or 0.0)
        price = float(t.get("price") or 0.0)
        if amount <= 0 or price <= 0:
            continue
        eff_amount = amount
        eff_cost_add = 0.0
        if FEE_IN_COST_BASIS:
            fee = t.get("fee") or {}
            fcost = float(fee.get("cost") or 0.0)
            fccy = (fee.get("currency") or "").upper()
            if fcost:
                if fccy == quote:
                    eff_cost_add = fcost
                elif fccy == base:
                    eff_amount = max(0.0, amount - fcost)
        if side == "buy":
            net_qty += eff_amount
            cost    += eff_amount * price + eff_cost_add
        elif side == "sell":
            if net_qty <= 0:
                continue
            avg = cost / net_qty if net_qty > 0 else 0.0
            dec = min(eff_amount, net_qty)
            cost -= avg * dec
            net_qty -= dec

    if net_qty <= 0:
        return (0.0, 0.0)
    return (net_qty, cost / net_qty)

def _get_cost_basis(symbol: str) -> Optional[Tuple[float, float]]:
    now = time.time()
    entry = _cost_basis_cache.get(symbol)
    if entry and (now - entry["ts"] < COST_CACHE_TTL_SEC):
        return (entry["qty"], entry["avg_px"])
    res = _compute_cost_basis_for_symbol(symbol)
    if res:
        qty, avg = res
        _cost_basis_cache[symbol] = {"ts": now, "qty": qty, "avg_px": avg}
    return res

# ────────────── Portfolio loop
def _value_portfolio(assets: Dict[str, float]) -> Tuple[float, Dict[str, Dict[str, float]]]:
    preferred = _quote_priority()
    assert _exchange is not None

    chosen: Dict[str, str] = {}
    symbols: List[str] = []
    for a, q in assets.items():
        if a == PRIMARY_QUOTE:
            continue
        sym = _best_symbol_for_asset(a, preferred)
        if sym:
            chosen[a] = sym
            symbols.append(sym)

    tick = _fetch_tickers(symbols)
    equity = assets.get(PRIMARY_QUOTE, 0.0)  # cash
    positions: Dict[str, Dict[str, float]] = {}
    if equity > 0:
        positions[f"{PRIMARY_QUOTE}/{PRIMARY_QUOTE}"] = {"qty": equity, "avg_px": 1.0, "last_px": 1.0}

    for asset, qty in assets.items():
        if qty <= 0 or asset == PRIMARY_QUOTE:
            continue
        sym = chosen.get(asset)
        if not sym:
            add_log(f"Skip valuation for {asset} (no direct market to {PRIMARY_QUOTE} or alternatives)")
            continue
        info = tick.get(sym) or {}
        last = float(info.get("last") or info.get("close") or 0.0)
        if last <= 0:
            continue
        cb = _get_cost_basis(sym)
        avg = float(cb[1]) if cb and cb[0] > 0 else last
        positions[sym] = {"qty": float(qty), "avg_px": avg, "last_px": last}
        equity += qty * last
    return equity, positions

async def portfolio_loop():
    await _ensure_exchange()
    add_log(f"Portfolio loop started | exchange={EXCHANGE_ID} | primary_quote={PRIMARY_QUOTE}")
    assert _exchange is not None
    while True:
        try:
            bal = _exchange.fetch_balance(params={}) if (API_KEY and API_SECRET) else {"total": {}}
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
                add_log("Geo-restricted by venue for authenticated calls.")
            else:
                add_log(f"Exchange error: {e}")
        except Exception as e:
            add_log(f"ERROR portfolio_loop: {e}")
        await asyncio.sleep(LOOP_SLEEP_S)

# ────────────── Features & Signals
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
    if not ohlcv or len(ohlcv) < max(TRADE_SLOW_EMA + 2, 50):
        return {"ok": False}
    arr = np.array(ohlcv, dtype=float)
    close = arr[:, 4]
    vol = arr[:, 5]
    emaf = _ema(close, TRADE_FAST_EMA)
    emas = _ema(close, TRADE_SLOW_EMA)
    rsi14 = _rsi(close, 14)
    ret1 = np.zeros_like(close)
    ret1[1:] = (close[1:] - close[:-1]) / (close[:-1] + 1e-12)
    return {"ok": True, "features": {
        "close": close, "vol": vol, "ema_fast": emaf, "ema_slow": emas, "rsi14": rsi14, "ret1": ret1
    }}

def _ema_score(feats: Dict[str, Any]) -> float:
    ef, es = feats["ema_fast"][-1], feats["ema_slow"][-1]
    if math.isnan(ef) or math.isnan(es):
        return 0.0
    px = feats["close"][-1]
    diff = (ef - es) / max(1e-8, px)
    return float(max(-1.0, min(1.0, diff * 50.0)))  # [-1,1]

# ML
_ML_MODEL = None
_ML_META: Dict[str, Any] = {}

def _load_ml():
    global _ML_MODEL, _ML_META
    if not ML_ENABLED or not joblib:
        add_log("ML disabled or joblib missing; EMA/quantum/sentiment only.")
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

def _ml_prob(feats: Dict[str, Any]) -> Optional[float]:
    if not _ML_MODEL:
        return None
    try:
        close = feats["close"]; rsi = feats["rsi14"]; ret1 = feats["ret1"]
        emaf = feats["ema_fast"]; emas = feats["ema_slow"]; vol = feats["vol"]
        x = np.array([[close[-1],
                       (50.0 if np.isnan(rsi[-1]) else rsi[-1]),
                       ret1[-1], emaf[-1], emas[-1], vol[-1]]], dtype=float)
        if hasattr(_ML_MODEL, "predict_proba"):
            p = _ML_MODEL.predict_proba(x)
            return float(p[0, 1]) if p.shape[1] >= 2 else float(np.mean(p[0]))
        if hasattr(_ML_MODEL, "decision_function"):
            s = float(_ML_MODEL.decision_function(x)[0])
            return 1.0 / (1.0 + math.exp(-s))
        if hasattr(_ML_MODEL, "predict"):
            y = _ML_MODEL.predict(x)
            return float(0.5 + 0.5 * np.clip(y[0], -1, 1))
    except Exception as e:
        add_log(f"ML score error: {e}")
    return None

# Auto-train if missing
def _fit_simple_model_from_ohlcv(ohlcv: List[List[float]]):
    from sklearn.linear_model import LogisticRegression
    try:
        import xgboost as xgb
        XGB = xgb.XGBClassifier(
            n_estimators=200, max_depth=4, learning_rate=0.08,
            subsample=0.8, colsample_bytree=0.8, reg_lambda=1.0,
            n_jobs=2
        )
    except Exception:
        XGB = None

    arr = np.array(ohlcv, dtype=float)
    close = arr[:, 4]
    vol   = arr[:, 5]
    if len(close) < 80:
        raise RuntimeError("Not enough OHLCV to train")

    def ema(a, span):
        return pd.Series(a).ewm(span=span, adjust=False).mean().values

    def rsi(a, p=14):
        delta = np.diff(a)
        up = np.where(delta > 0, delta, 0.0)
        down = np.where(delta < 0, -delta, 0.0)
        ru = pd.Series(up).rolling(p).mean()
        rd = pd.Series(down).rolling(p).mean()
        rs = ru / (rd + 1e-12)
        r = 100.0 - (100.0 / (1.0 + rs))
        return np.concatenate([[np.nan], r.values])

    ema_f = ema(close, max(2, TRADE_FAST_EMA))
    ema_s = ema(close, max(3, TRADE_SLOW_EMA))
    rsi14 = rsi(close, 14)

    ret1 = np.zeros_like(close)
    ret1[1:] = (close[1:] - close[:-1]) / (close[:-1] + 1e-12)

    df = pd.DataFrame({
        "close": close, "vol": vol, "ema_fast": ema_f, "ema_slow": ema_s,
        "rsi14": rsi14, "ret1": ret1
    }).replace([np.inf, -np.inf], np.nan).dropna()

    y_aligned = (df["ret1"] > 0).astype(int).values
    X = df[["close","rsi14","ret1","ema_fast","ema_slow","vol"]].values

    model = XGB if XGB is not None else LogisticRegression(max_iter=1000)
    model.fit(X, y_aligned)
    meta = {"features": ["close","rsi14","ret1","ema_fast","ema_slow","vol"]}
    return model, meta

async def _auto_train_if_missing():
    global _ML_MODEL, _ML_META
    if not (ML_ENABLED and AUTO_TRAIN_ON_START):
        return
    if _ML_MODEL:
        return
    try:
        assert _exchange is not None
        syms = [s.strip() for s in TRAIN_SYMBOLS_ENV.split(",") if s.strip()]
        all_ohlcv: List[List[float]] = []
        for s in syms:
            try:
                data = _exchange.fetch_ohlcv(s, timeframe=TRAIN_TIMEFRAME, limit=TRAIN_LIMIT)
                if data:
                    all_ohlcv.extend(data)
            except Exception as e:
                add_log(f"auto-train: fetch_ohlcv fail {s}: {e}")
        if len(all_ohlcv) < 200:
            add_log("auto-train: not enough combined data to train; skipping")
            return
        model, meta = _fit_simple_model_from_ohlcv(all_ohlcv)
        if joblib:
            os.makedirs(os.path.dirname(MODEL_XGB_PATH), exist_ok=True)
            joblib.dump(model, MODEL_XGB_PATH)
            with open(MODEL_META_PATH, "w") as f:
                json.dump(meta, f, indent=2)
            _ML_MODEL = model; _ML_META = meta
            add_log(f"ML: auto-trained and saved → {MODEL_XGB_PATH}")
        else:
            _ML_MODEL = model; _ML_META = meta
            add_log("ML: auto-trained in memory (joblib not available to persist)")
    except Exception as e:
        add_log(f"auto-train error: {e}")

# Quantum score
def _quantum_prob(symbol: str, feats: Dict[str, Any]) -> Optional[float]:
    if not QUANTUM_ENABLED:
        return None
    if QuantumCircuit is None or Aer is None:
        h = hashlib.sha256(f"{symbol}:{feats['close'][-1]:.8f}".encode()).hexdigest()
        return (int(h[:8], 16) % 1000) / 1000.0
    try:
        px = feats["close"][-1]
        theta = (px % (2 * math.pi))
        qc = QuantumCircuit(1, 1)
        qc.ry(theta, 0)
        qc.measure(0, 0)
        backend = Aer.get_backend(QUANTUM_BACKEND or "aer_simulator")
        shots = 512
        res = backend.run(qc, shots=shots).result()
        counts = res.get_counts()
        return counts.get("1", 0) / shots
    except Exception as e:
        add_log(f"Quantum score error: {e}")
        return None

# Sentiment prob 0..1
def _sentiment_prob(symbol: str) -> Optional[float]:
    if not (SENTIMENT_ENABLED and SENTIMENT_WIRED):
        return None
    try:
        base = symbol.split("/")[0].upper()
        probs = sentiment_latest_probs()  # {BASE: prob 0..1}
        return float(probs.get(base, 0.5))
    except Exception:
        return None

def _symbols_to_scan() -> List[str]:
    assert _exchange is not None
    syms: Set[str] = set()
    for sym in _positions.keys():
        if sym.endswith(f"/{PRIMARY_QUOTE}") and not sym.startswith(f"{PRIMARY_QUOTE}/"):
            if sym in _exchange.markets:
                syms.add(sym)
    if TRADE_SYMBOLS_ENV.strip():
        for s in TRADE_SYMBOLS_ENV.split(","):
            s = s.strip().upper()
            if s and s in _exchange.markets:
                syms.add(s)
    syms.discard(f"{PRIMARY_QUOTE}/{PRIMARY_QUOTE}")
    return sorted(syms)

def _push_signal(sig: Dict[str, Any]):
    for i in range(len(_signals)-1, -1, -1):
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
    add_log(f"Signal loop started | TF={TRADE_TIMEFRAME} | Q={QUANTUM_ENABLED} | ML={ML_ENABLED} | SENT={SENTIMENT_ENABLED and SENTIMENT_WIRED}")
    assert _exchange is not None

    while True:
        t0 = time.time()
        try:
            scan = _symbols_to_scan()
            n_scanned = 0
            for sym in scan:
                try:
                    data = _exchange.fetch_ohlcv(sym, timeframe=TRADE_TIMEFRAME, limit=TRADE_LOOKBACK_BARS)
                except Exception as e:
                    add_log(f"fetch_ohlcv fail {sym}: {e}")
                    continue
                if not data:
                    continue
                f = _build_features(data)
                if not f["ok"]:
                    continue
                feats = f["features"]

                ema_s = _ema_score(feats)
                ema_prob = 0.5 + 0.5 * np.clip(ema_s, -1, 1)

                ml_prob = _ml_prob(feats)
                q_prob  = _quantum_prob(sym, feats)
                s_prob  = _sentiment_prob(sym)

                parts, weights, labs = [ema_prob], [EMA_WEIGHT], ["ema"]
                if ml_prob is not None: parts.append(ml_prob); weights.append(ML_WEIGHT); labs.append("ml")
                if q_prob  is not None: parts.append(q_prob);  weights.append(QUANTUM_WEIGHT); labs.append("q")
                if s_prob  is not None: parts.append(s_prob);  weights.append(SENTIMENT_WEIGHT); labs.append("sent")

                if sum(weights) <= 0:
                    final_prob = float(ema_prob)
                    w_norm = {"ema": 1.0}
                else:
                    w = np.array(weights, dtype=float)
                    w = w / np.sum(w)
                    final_prob = float(np.sum(w * np.array(parts, dtype=float)))
                    w_norm = {labs[i]: float(w[i]) for i in range(len(labs))}

                thr_buy  = 0.5 + 0.5 * TRADE_MIN_CONF
                thr_sell = 0.5 - 0.5 * TRADE_MIN_CONF
                if final_prob >= thr_buy:
                    signal = "BUY"
                elif final_prob <= thr_sell:
                    signal = "SELL"
                else:
                    signal = "HOLD"

                strength = abs(final_prob - 0.5) * 2.0  # 0..1
                _push_signal({
                    "symbol": sym,
                    "signal": signal,
                    "strength": round(float(strength), 4),  # used by execution sizing
                    "ema": round(float(ema_prob), 4),
                    "ml": None if ml_prob is None else round(float(ml_prob), 4),
                    "q": None if q_prob is None else round(float(q_prob), 4),
                    "sent": None if s_prob is None else round(float(s_prob), 4),
                    "final_prob": round(float(final_prob), 4),
                    "thr_buy": round(float(thr_buy), 4),
                    "thr_sell": round(float(thr_sell), 4),
                    "weights": w_norm,
                    "t": int(time.time())
                })
                n_scanned += 1

            add_log(f"signals | n={n_scanned} scanned")
        except Exception as e:
            add_log(f"ERROR signals_loop: {e}")
        await asyncio.sleep(max(0.25, SIGNAL_INTERVAL_S - (time.time() - t0)))

# ────────────── Sentiment loop (pulls and scores news)
async def sentiment_loop():
    if not (SENTIMENT_ENABLED and SENTIMENT_WIRED):
        add_log("Sentiment loop disabled or provider not wired.")
        return
    add_log("Sentiment loop started.")
    while True:
        try:
            _ = sentiment_snapshot()  # pulls + scores + keeps rolling window inside module
        except Exception as e:
            add_log(f"ERROR sentiment_loop: {e}")
        await asyncio.sleep(60)

# ────────────── Execution
async def _place_market_order(sym: str, side: str, qty: float) -> Optional[Dict[str, Any]]:
    assert _exchange is not None
    if qty <= 0:
        return None
    try:
        order = _exchange.create_order(symbol=sym, type="market", side=side.lower(), amount=qty)
        add_log(f"ORDER {side} {sym} qty={qty}")
        return order
    except Exception as e:
        add_log(f"ERROR order {side} {sym} qty={qty}: {e}")
        return None

async def _execute_signal(sym: str, sig: Dict[str, Any]):
    """Strength‑based sizing, minNotional/step checks, exposure caps, cooldown."""
    side = sig.get("signal")
    if side not in ("BUY", "SELL"):
        return

    now = time.time()
    last_t = _last_trade_ts.get(sym, 0)
    if now - last_t < MIN_SECS_BETWEEN_TRADES:
        add_log(f"SKIP {sym}: cooldown {int(now-last_t)}s < {int(MIN_SECS_BETWEEN_TRADES)}")
        return

    pos = _positions.get(sym)  # {"qty","avg_px","last_px"}
    last = (pos or {}).get("last_px") or 0.0
    if last <= 0:
        add_log(f"SKIP {sym}: no last price")
        return

    strength = float(sig.get("strength", 0.0))
    if strength < MIN_STRENGTH_TO_TRADE:
        add_log(f"SKIP {sym}: strength {strength:.3f} < MIN_STRENGTH_TO_TRADE {MIN_STRENGTH_TO_TRADE:.3f}")
        return

    filters = _binance_filters(sym)
    step    = filters["stepSize"]
    min_not = filters["minNotional"]

    def _valid_qty(qty: float) -> float:
        q = _round_step(qty, step)
        if q <= 0:
            return 0.0
        if last * q < max(min_not, BUY_MIN_USDT):
            return 0.0
        return q

    try:
        if side == "BUY":
            if not _can_open_more_positions():
                add_log(f"SKIP BUY {sym}: reached MAX_OPEN_POSITIONS={MAX_OPEN_POSITIONS}")
                return
            current_expo = float(pos["qty"]) * last if pos else 0.0
            if current_expo >= MAX_SPEND_PER_SYMBOL:
                add_log(f"SKIP BUY {sym}: exposure {current_expo:.2f} ≥ MAX_SPEND_PER_SYMBOL {MAX_SPEND_PER_SYMBOL}")
                return

            dyn_unit = TRADE_QUOTE_PER_ORDER * max(0.1, strength ** SIZE_ALPHA)
            spend_cap = min(TRADE_QUOTE_PER_ORDER * BUY_MAX_MULTIPLIER,
                            MAX_SPEND_PER_SYMBOL - current_expo)
            spend = max(BUY_MIN_USDT, min(dyn_unit, spend_cap))
            qty = _valid_qty(spend / last)
            if qty <= 0:
                add_log(f"SKIP BUY {sym}: invalid qty (spend={spend:.2f}, step={step}, minNotional={min_not})")
                return
            order = await _place_market_order(sym, "BUY", qty)
            if order:
                _last_trade_ts[sym] = now

        elif side == "SELL":
            if not pos or pos.get("qty", 0.0) <= 0:
                add_log(f"SKIP SELL {sym}: no position to sell")
                return
            frac = SELL_MIN_FRAC + (SELL_MAX_FRAC - SELL_MIN_FRAC) * strength
            qty = _valid_qty(float(pos["qty"]) * max(0.0, min(1.0, frac)))
            if qty <= 0:
                add_log(f"SKIP SELL {sym}: invalid qty (pos={pos.get('qty')}, step={step}, minNotional={min_not})")
                return
            order = await _place_market_order(sym, "SELL", qty)
            if order:
                _last_trade_ts[sym] = now

    except Exception as e:
        add_log(f"ERROR _execute_signal {sym}: {e}")

async def execution_loop():
    if not TRADE_ENABLED:
        add_log("Execution loop disabled (TRADE_ENABLED=0).")
        return
    await _ensure_exchange()
    add_log("Execution loop started (live orders ON).")
    while True:
        try:
            latest_by_sym: Dict[str, Dict[str, Any]] = {}
            for s in _signals[-400:]:
                latest_by_sym[s["symbol"]] = s
            for sym, sig in latest_by_sym.items():
                if sig["signal"] in ("BUY", "SELL"):
                    await _execute_signal(sym, sig)
        except Exception as e:
            add_log(f"ERROR execution_loop: {e}")
        await asyncio.sleep(EXECUTION_INTERVAL_S)

# ────────────── Startup
@app.on_event("startup")
async def _on_startup():
    asyncio.create_task(portfolio_loop())
    asyncio.create_task(signals_loop())
    asyncio.create_task(sentiment_loop())
    asyncio.create_task(_auto_train_if_missing())
    if TRADE_ENABLED:
        asyncio.create_task(execution_loop())

# ────────────── Endpoints
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
        "ml": {"enabled": ML_ENABLED, "loaded": bool(_ML_MODEL), "model_path": MODEL_XGB_PATH if _ML_MODEL else None},
        "sentiment": {"enabled": SENTIMENT_ENABLED and SENTIMENT_WIRED}
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

@app.get("/sentiment")
def sentiment():
    if not (SENTIMENT_ENABLED and SENTIMENT_WIRED):
        return {"enabled": False, "scores": {}}
    return sentiment_snapshot()

@app.get("/execute/preview")
def execute_preview():
    """What the bot would trade now, with reasons."""
    out = []
    try:
        latest_by_sym: Dict[str, Dict[str, Any]] = {}
        for s in _signals[-400:]:
            latest_by_sym[s["symbol"]] = s

        for sym, sig in latest_by_sym.items():
            row = {"symbol": sym, "signal": sig.get("signal"), "strength": sig.get("strength")}
            reason = None
            act = None
            if sig.get("signal") not in ("BUY", "SELL"):
                reason = "HOLD"
            else:
                pos = _positions.get(sym)
                last = (pos or {}).get("last_px") or 0.0
                if last <= 0:
                    reason = "no last price"
                else:
                    min_strength = MIN_STRENGTH_TO_TRADE
                    strength = float(sig.get("strength", 0.0))
                    if strength < min_strength:
                        reason = f"strength {strength:.3f} < {min_strength:.3f}"
                    else:
                        filters = _binance_filters(sym)
                        step = filters["stepSize"]; min_not = filters["minNotional"]
                        if sig["signal"] == "BUY":
                            if not _can_open_more_positions():
                                reason = f"MAX_OPEN_POSITIONS={MAX_OPEN_POSITIONS}"
                            else:
                                current_expo = float(pos["qty"]) * last if pos else 0.0
                                if current_expo >= MAX_SPEND_PER_SYMBOL:
                                    reason = f"exposure {current_expo:.2f} ≥ MAX_SPEND_PER_SYMBOL"
                                else:
                                    dyn_unit = TRADE_QUOTE_PER_ORDER * max(0.1, strength ** SIZE_ALPHA)
                                    spend_cap = min(TRADE_QUOTE_PER_ORDER * BUY_MAX_MULTIPLIER,
                                                    MAX_SPEND_PER_SYMBOL - current_expo)
                                    spend = max(BUY_MIN_USDT, min(dyn_unit, spend_cap))
                                    qty = _round_step(spend / last, step)
                                    if qty <= 0 or last * qty < max(min_not, BUY_MIN_USDT):
                                        reason = f"invalid qty (spend={spend:.2f}, step={step}, minNotional={min_not})"
                                    else:
                                        act = {"side": "BUY", "qty": qty, "spend": spend}
                        else:  # SELL
                            if not pos or pos.get("qty", 0.0) <= 0:
                                reason = "no position"
                            else:
                                frac = SELL_MIN_FRAC + (SELL_MAX_FRAC - SELL_MIN_FRAC) * strength
                                qty = _round_step(float(pos["qty"]) * max(0.0, min(1.0, frac)), step)
                                if qty <= 0 or last * qty < max(min_not, BUY_MIN_USDT):
                                    reason = f"invalid qty (pos={pos.get('qty')}, step={step}, minNotional={min_not})"
                                else:
                                    act = {"side": "SELL", "qty": qty, "value": qty * last}

            row["action"] = act
            row["reason"] = reason
            out.append(row)
    except Exception as e:
        return {"error": str(e)}
    return {"preview": out}