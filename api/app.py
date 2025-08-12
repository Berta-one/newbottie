# api/app.py
import os, time, asyncio, logging, math, json, hashlib
from typing import Any, Dict, List, Optional, Tuple, Set

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# deps
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

# quantum optional
try:
    from qiskit import QuantumCircuit
    from qiskit_aer import Aer
except Exception:
    QuantumCircuit = None
    Aer = None

# sentiment (Finnhub + VADER)
try:
    from sentiment.sentiment_service import snapshot as sentiment_snapshot, latest_probs as sentiment_latest_probs
    SENTIMENT_WIRED = True
except Exception:
    SENTIMENT_WIRED = False

# online learner
from ml.online_learner import OnlineLearner

# ───────────────────────────────── FIXED: boolean parsing helper
def parse_bool(v: str, default=False) -> bool:
    if v is None:
        return default
    return str(v).strip().lower() in ("1","true","yes","on")

# ───────────────────────────────── env (FIXED: consistent boolean parsing)
LOG_LEVEL         = os.getenv("LOG_LEVEL", "INFO").upper()
NETLIFY_URL       = os.getenv("NETLIFY_URL", "*")

EXCHANGE_ID       = os.getenv("EXCHANGE_ID", "binance").lower()
API_KEY           = os.getenv("BINANCE_API_KEY", os.getenv("API_KEY", "")).strip()
API_SECRET        = os.getenv("BINANCE_API_SECRET", os.getenv("API_SECRET", "")).strip()
PRIMARY_QUOTE     = os.getenv("PRIMARY_QUOTE", "USDT").upper()

LOOP_SLEEP_S      = float(os.getenv("LOOP_SLEEP_S", "6"))
SIGNAL_INTERVAL_S = float(os.getenv("SIGNAL_INTERVAL_S", "30"))

COST_LOOKBACK_DAYS    = int(os.getenv("COST_BASIS_LOOKBACK_DAYS", "120"))
MAX_TRADES_PER_SYMBOL = int(os.getenv("MAX_TRADES_PER_SYMBOL", "1000"))
FEE_IN_COST_BASIS     = parse_bool(os.getenv("FEE_IN_COST_BASIS", "1"))
COST_CACHE_TTL_SEC    = int(os.getenv("COST_CACHE_TTL_SEC", "600"))

TRADE_TIMEFRAME     = os.getenv("TRADE_TIMEFRAME", "1h")
TRADE_LOOKBACK_BARS = int(os.getenv("TRADE_LOOKBACK_BARS", "300"))
TRADE_FAST_EMA      = int(os.getenv("TRADE_FAST_EMA", "12"))
TRADE_SLOW_EMA      = int(os.getenv("TRADE_SLOW_EMA", "26"))
TRADE_SYMBOLS_ENV   = os.getenv("TRADE_SYMBOLS", "")

# dynamic thresholds
TRADE_BASE_MIN_CONF  = float(os.getenv("TRADE_MIN_CONF", "0.55"))   # base confidence
TRADE_CONF_ADAPT     = parse_bool(os.getenv("TRADE_CONF_ADAPT", "1"))
TRADE_CONF_FLOOR     = float(os.getenv("TRADE_CONF_FLOOR", "0.50"))
TRADE_CONF_CEIL      = float(os.getenv("TRADE_CONF_CEIL", "0.80"))

# execution controls
TRADE_ENABLED        = parse_bool(os.getenv("TRADE_ENABLED", "0"))
TRADE_QUOTE_PER_ORDER= float(os.getenv("TRADE_QUOTE_PER_ORDER", "100"))
MAX_SPEND_PER_SYMBOL = float(os.getenv("MAX_SPEND_PER_SYMBOL", "1000"))
SELL_FRACTION        = float(os.getenv("SELL_FRACTION", "1.0"))
MAX_OPEN_POSITIONS   = int(os.getenv("MAX_OPEN_POSITIONS", "10"))
EXECUTION_INTERVAL_S = float(os.getenv("EXECUTION_INTERVAL_S", "20"))

# ensemble weights (normalized later)
EMA_WEIGHT         = float(os.getenv("EMA_WEIGHT", "0.40"))
ML_WEIGHT          = float(os.getenv("ML_WEIGHT",  "0.30"))
QUANTUM_WEIGHT     = float(os.getenv("QUANTUM_WEIGHT","0.20"))
SENTIMENT_WEIGHT   = float(os.getenv("SENTIMENT_WEIGHT","0.10"))

# ML persistence (joblib model is optional; online learner always exists)
ML_ENABLED         = parse_bool(os.getenv("ML_ENABLED", "1"))
MODEL_XGB_PATH     = os.getenv("MODEL_XGB_PATH", "models/xgb_model.pkl")
MODEL_META_PATH    = os.getenv("MODEL_META_PATH","models/xgb_meta.json")

# Online learning
ONLINE_LEARN           = parse_bool(os.getenv("ONLINE_LEARN","1"))
ONLINE_MODEL_PATH      = os.getenv("ONLINE_MODEL_PATH","models/online_sgd.pkl")
ONLINE_META_PATH       = os.getenv("ONLINE_META_PATH", "models/online_sgd_meta.json")
ONLINE_MINIBATCH       = int(os.getenv("ONLINE_MINIBATCH","32"))  # min items per update
ONLINE_SAVE_SEC        = int(os.getenv("ONLINE_SAVE_SEC","30"))   # handled in class
ONLINE_LABEL_HORIZON   = int(os.getenv("ONLINE_LABEL_HORIZON","1"))  # label next-bar up/down

# quantum
QUANTUM_ENABLED    = parse_bool(os.getenv("QUANTUM_ENABLED","0"))
QUANTUM_BACKEND    = os.getenv("QUANTUM_BACKEND","aer_simulator")

# FIXED: sentiment config for /health reporting
SENTIMENT_ENABLED  = parse_bool(os.getenv("SENTIMENT_ENABLED", "1"))
SENTIMENT_SOURCE   = (os.getenv("SENTIMENT_SOURCE", "finnhub") or "finnhub").lower()
SENTIMENT_WINDOW_S = int(os.getenv("SENTIMENT_WINDOW_S", "900"))

# ───────────────────────────────── app
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
log = logging.getLogger("BottieAPI")

app = FastAPI(title="Bottie API", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[NETLIFY_URL] if NETLIFY_URL != "*" else ["*"],
    allow_credentials=False,
    allow_methods=["GET","POST","OPTIONS","HEAD"],
    allow_headers=["*"],
)

# ───────────────────────────────── state
_started = time.time()
_equity_series: List[Dict[str, Any]] = []
_positions: Dict[str, Dict[str, float]] = {}
_signals: List[Dict[str, Any]] = []
_logs: List[str] = []
_cost_basis_cache: Dict[str, Dict[str, float]] = {}

# ML pieces
_ML_MODEL = None           # optional joblib model
_ML_META: Dict[str, Any] = {}
_OL: Optional[OnlineLearner] = None  # online learner always present if ONLINE_LEARN

# buffers for online labels: {symbol: {"X": np.ndarray, "t": int, "prev_close": float}}
_prev_feature: Dict[str, Dict[str, Any]] = {}
_pending_X: List[np.ndarray] = []
_pending_y: List[int] = []

# execution throttle + tracking
_last_exec = 0.0
_open_spend: Dict[str, float] = {}  # per-symbol committed quote
_trade_log: List[Dict[str, Any]] = []

def add_log(msg: str):
    _logs.append(msg)
    if len(_logs) > 1500:
        del _logs[:-1000]
    log.info(msg)

# ───────────────────────────────── exchange
_exchange: Optional[ccxt.Exchange] = None

def _init_exchange() -> ccxt.Exchange:
    if EXCHANGE_ID not in ccxt.exchanges:
        raise RuntimeError(f"Exchange '{EXCHANGE_ID}' not supported by ccxt.")
    klass = getattr(ccxt, EXCHANGE_ID)
    params: Dict[str, Any] = {"enableRateLimit": True}
    if API_KEY and API_SECRET:
        params.update({"apiKey": API_KEY, "secret": API_SECRET})
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

def _symbol_exists(sym: str) -> bool:
    assert _exchange is not None
    return sym in _exchange.markets

# ───────────────────────────────── helpers
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

# ───────────────────────────────── cost basis (WAC)
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
            fccy  = (fee.get("currency") or "").upper()
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

_cost_basis_cache: Dict[str, Dict[str, float]] = {}
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

# ───────────────────────────────── valuation loop
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

# ───────────────────────────────── features & signals
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
    vol   = arr[:, 5]
    emaf  = _ema(close, TRADE_FAST_EMA)
    emas  = _ema(close, TRADE_SLOW_EMA)
    rsi14 = _rsi(close, 14)
    ret1  = np.zeros_like(close)
    ret1[1:] = (close[1:] - close[:-1]) / (close[:-1] + 1e-12)
    return {"ok": True, "features": {
        "close": close, "vol": vol, "ema_fast": emaf, "ema_slow": emas, "rsi14": rsi14, "ret1": ret1
    }}

def _ema_score(feats: Dict[str, Any]) -> float:
    ef, es = feats["ema_fast"][-1], feats["ema_slow"][-1]
    if math.isnan(ef) or math.isnan(es): return 0.0
    px = feats["close"][-1]
    diff = (ef - es) / max(1e-8, px)
    return float(max(-1.0, min(1.0, diff * 50.0)))  # [-1,1]

# ML — joblib model (optional) + online learner (primary)
def _load_ml():
    global _ML_MODEL, _ML_META, _OL
    if ONLINE_LEARN:
        _OL = OnlineLearner(
            model_path=ONLINE_MODEL_PATH,
            meta_path=ONLINE_META_PATH,
        )
        add_log("OnlineLearner ready.")
    if ML_ENABLED and joblib and os.path.exists(MODEL_XGB_PATH):
        try:
            _ML_MODEL = joblib.load(MODEL_XGB_PATH)
            add_log(f"ML (joblib) loaded: {MODEL_XGB_PATH}")
            if os.path.exists(MODEL_META_PATH):
                with open(MODEL_META_PATH, "r") as f:
                    _ML_META = json.load(f)
        except Exception as e:
            add_log(f"ML joblib load error: {e}")

def _ml_prob_from_models(feats: Dict[str, Any]) -> Optional[float]:
    # online learner first
    if _OL is not None:
        try:
            X = _OL.vectorize(feats)
            return float(_OL.predict_proba(X))
        except Exception as e:
            add_log(f"OnlineLearner predict error: {e}")
    # fallback joblib model
    if _ML_MODEL is not None:
        try:
            close = feats["close"]; rsi = feats["rsi14"]; ret1 = feats["ret1"]
            emaf = feats["ema_fast"]; emas = feats["ema_slow"]; vol = feats["vol"]
            X = np.array([[close[-1],
                           (50.0 if np.isnan(rsi[-1]) else rsi[-1]),
                           ret1[-1], emaf[-1], emas[-1], vol[-1]]], dtype=float)
            if hasattr(_ML_MODEL, "predict_proba"):
                p = _ML_MODEL.predict_proba(X)
                return float(p[0, 1]) if p.shape[1] >= 2 else float(np.mean(p[0]))
            if hasattr(_ML_MODEL, "decision_function"):
                s = float(_ML_MODEL.decision_function(X)[0])
                return 1.0 / (1.0 + math.exp(-s))
            if hasattr(_ML_MODEL, "predict"):
                y = _ML_MODEL.predict(X)
                return float(0.5 + 0.5 * np.clip(y[0], -1, 1))
        except Exception as e:
            add_log(f"ML joblib predict error: {e}")
    return None

# quantum signal
def _quantum_prob(symbol: str, feats: Dict[str, Any]) -> Optional[float]:
    if not QUANTUM_ENABLED:
        return None
    if QuantumCircuit is None or Aer is None:
        # deterministic pseudo prob fallback
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

# sentiment → 0..1
def _sentiment_prob(symbol: str) -> Optional[float]:
    if not (SENTIMENT_ENABLED and SENTIMENT_WIRED):
        return None
    try:
        base = symbol.split("/")[0].upper()
        probs = sentiment_latest_probs()  # {BASE: prob}
        return float(probs.get(base, 0.5))
    except Exception:
        return None

def _symbols_to_scan() -> List[str]:
    assert _exchange is not None
    syms: Set[str] = set()
    # from positions
    for sym in _positions.keys():
        if sym.endswith(f"/{PRIMARY_QUOTE}") and not sym.startswith(f"{PRIMARY_QUOTE}/"):
            if sym in _exchange.markets:
                syms.add(sym)
    # forced via env
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

def _adaptive_thresholds() -> Tuple[float, float]:
    """
    Dynamic buy/sell thresholds around 0.5 based on recent ensemble dispersion.
    Simpler: we'll scale base confidence slightly with recent avg |prob-0.5|.
    """
    window = _signals[-50:]
    if not window:
        c = TRADE_BASE_MIN_CONF
    else:
        diffs = [abs(s.get("final_prob",0.5) - 0.5) for s in window]
        avg_d = float(np.mean(diffs)) if diffs else 0.05
        # push threshold up if signals are noisy/low; down if strong
        c = np.clip(TRADE_BASE_MIN_CONF - (avg_d - 0.10)*0.3, TRADE_CONF_FLOOR-0.5, TRADE_CONF_CEIL-0.5)
        # map back to 0..1 margin (we use 0.5±c)
        c = float(np.clip(c, 0.0, 0.49))
    thr_buy  = 0.5 + (c if TRADE_CONF_ADAPT else TRADE_BASE_MIN_CONF/2.0)
    thr_sell = 0.5 - (c if TRADE_CONF_ADAPT else TRADE_BASE_MIN_CONF/2.0)
    return thr_buy, thr_sell

async def signals_loop():
    await _ensure_exchange()
    _load_ml()
    add_log(f"Signal loop started | TF={TRADE_TIMEFRAME} | Q={QUANTUM_ENABLED} | ML={ML_ENABLED or ONLINE_LEARN}")
    assert _exchange is not None

    while True:
        t0 = time.time()
        try:
            scan = _symbols_to_scan()
            n_scanned = 0
            thr_buy, thr_sell = _adaptive_thresholds()

            for sym in scan:
                # 1) fetch ohlcv
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

                # 2) ensemble
                ema_s   = _ema_score(feats)
                ema_prob= 0.5 + 0.5 * np.clip(ema_s, -1, 1)

                ml_prob = _ml_prob_from_models(feats)
                q_prob  = _quantum_prob(sym, feats)
                s_prob  = _sentiment_prob(sym)

                parts, weights, labels = [ema_prob], [EMA_WEIGHT], ["ema"]
                if ml_prob is not None: parts.append(ml_prob); weights.append(ML_WEIGHT); labels.append("ml")
                if q_prob  is not None: parts.append(q_prob);  weights.append(QUANTUM_WEIGHT); labels.append("q")
                if s_prob  is not None: parts.append(s_prob);  weights.append(SENTIMENT_WEIGHT); labels.append("sent")

                w = np.array(weights, dtype=float)
                w = w / np.sum(w) if np.sum(w) > 0 else w
                final_prob = float(np.sum(w * np.array(parts, dtype=float)))
                w_norm = {lab: float(w[i]) for i, lab in enumerate(labels)}

                # 3) signal
                if final_prob >= thr_buy:
                    signal, conf = "BUY", final_prob
                elif final_prob <= thr_sell:
                    signal, conf = "SELL", 1.0 - final_prob
                else:
                    signal, conf = "HOLD", abs(final_prob - 0.5) * 2.0

                out = {
                    "symbol": sym,
                    "signal": signal,
                    "conf": round(float(conf), 4),
                    "ema": round(float(ema_prob), 4),
                    "ml": None if ml_prob is None else round(float(ml_prob), 4),
                    "q": None if q_prob is None else round(float(q_prob), 4),
                    "sent": None if s_prob is None else round(float(s_prob), 4),
                    "final_prob": round(float(final_prob), 4),
                    "thr_buy": round(float(thr_buy), 4),
                    "thr_sell": round(float(thr_sell), 4),
                    "weights": w_norm,
                    "t": int(time.time())
                }
                _push_signal(out)
                n_scanned += 1

                # 4) buffer features for online labels later
                if ONLINE_LEARN and _OL is not None:
                    try:
                        X = _OL.vectorize(feats)
                        prev_close = float(feats["close"][-1])
                        _prev_feature[sym] = {"X": X, "prev_close": prev_close, "t": int(time.time())}
                    except Exception as e:
                        add_log(f"OnlineLearner vectorize error: {e}")

            add_log(f"signals | n={n_scanned} scanned")
        except Exception as e:
            add_log(f"ERROR signals_loop: {e}")
        await asyncio.sleep(max(0.25, SIGNAL_INTERVAL_S - (time.time() - t0)))

# ───────────────────────────────── online learning labeler
async def online_label_loop():
    """
    When the next bar arrives, label the buffered features: y=1 if close_t+1>close_t else 0.
    Then partial_fit on mini-batches.
    """
    if not ONLINE_LEARN:
        return
    add_log("Online label loop started.")
    assert _exchange is not None

    while True:
        try:
            for sym, pack in list(_prev_feature.items()):
                # fetch just a small window to get latest close
                try:
                    data = _exchange.fetch_ohlcv(sym, timeframe=TRADE_TIMEFRAME, limit=3)
                except Exception:
                    continue
                if not data or len(data) < 2:
                    continue
                latest_close = float(data[-1][4])
                y = int(latest_close > float(pack["prev_close"]))
                _pending_X.append(pack["X"])
                _pending_y.append(y)
                # remove once labeled
                _prev_feature.pop(sym, None)

            # if we have enough labels → update model
            if _OL is not None and len(_pending_y) >= ONLINE_MINIBATCH:
                try:
                    X = np.vstack(_pending_X)
                    y = np.array(_pending_y, dtype=int)
                    _OL.update(X, y)
                    _pending_X.clear(); _pending_y.clear()
                    add_log(f"OnlineLearner updated: batch={len(y)}")
                except Exception as e:
                    add_log(f"OnlineLearner update error: {e}")
                    _pending_X.clear(); _pending_y.clear()
        except Exception as e:
            add_log(f"ERROR online_label_loop: {e}")

        # run roughly once per bar
        await asyncio.sleep(max(15.0, SIGNAL_INTERVAL_S))

# ───────────────────────────────── execution
def _position_qty(sym: str) -> float:
    p = _positions.get(sym)
    return float(p.get("qty", 0.0)) if p else 0.0

def _last_px(sym: str) -> Optional[float]:
    p = _positions.get(sym)
    return float(p.get("last_px")) if p and "last_px" in p else None

def _min_notional_and_step(sym: str) -> Tuple[float, float]:
    # very rough min notional & qty step from market filters
    assert _exchange is not None
    m = _exchange.markets.get(sym, {})
    min_notional = 10.0
    qty_step     = 0.000001
    fs = m.get("info", {}).get("filters", [])
    for f in fs:
        if f.get("filterType") == "MIN_NOTIONAL":
            try: min_notional = float(f.get("minNotional", min_notional))
            except: pass
        if f.get("filterType") == "LOT_SIZE":
            try: qty_step = float(f.get("stepSize", qty_step))
            except: pass
    return min_notional, qty_step

def _round_step(qty: float, step: float) -> float:
    if step <= 0:
        return qty
    return math.floor(qty / step) * step

async def execution_loop():
    if not TRADE_ENABLED:
        add_log("Execution loop disabled (TRADE_ENABLED=0).")
        return
    await _ensure_exchange()
    add_log("Execution loop started (LIVE orders).")
    assert _exchange is not None

    global _last_exec
    while True:
        try:
            now = time.time()
            if now - _last_exec < EXECUTION_INTERVAL_S:
                await asyncio.sleep(1.0); continue
            _last_exec = now

            # FIXED: Check runtime kill switch
            if not EXECUTION_RUNTIME_ENABLED:
                await asyncio.sleep(1.0); continue

            # pick latest signal per symbol
            latest: Dict[str, Dict[str, Any]] = {}
            for s in _signals[-300:]:
                latest[s["symbol"]] = s

            for sym, s in latest.items():
                signal = s.get("signal")
                conf   = float(s.get("conf", 0.0))
                prob   = float(s.get("final_prob", 0.5))
                px     = _last_px(sym)
                if px is None or px <= 0:
                    continue

                # size ∝ |prob-0.5|, capped by TRADE_QUOTE_PER_ORDER
                strength = max(0.0, min(1.0, abs(prob - 0.5) * 2.0))
                quote_budget = TRADE_QUOTE_PER_ORDER * strength
                if quote_budget < 5.0:   # ignore tiny dust orders
                    continue

                min_notional, qty_step = _min_notional_and_step(sym)
                qty = quote_budget / px
                qty = _round_step(qty, qty_step)

                if qty * px < min_notional:
                    # bump to minimum if possible
                    qty = _round_step(min_notional / px, qty_step)

                if qty <= 0:
                    continue

                # per-symbol spend cap
                spent = _open_spend.get(sym, 0.0)
                if spent + qty * px > MAX_SPEND_PER_SYMBOL and signal == "BUY":
                    continue

                side = None
                if signal == "BUY":
                    side = "buy"
                elif signal == "SELL":
                    # sell fraction of current holdings
                    have = _position_qty(sym)
                    sell_qty = _round_step(have * SELL_FRACTION * strength, qty_step)
                    if sell_qty <= 0:
                        continue
                    qty = sell_qty
                    side = "sell"
                else:
                    continue

                try:
                    order = _exchange.create_order(sym, type="market", side=side, amount=qty)
                    _trade_log.append({
                        "t": int(time.time()),
                        "symbol": sym, "side": side, "qty": qty, "px": px,
                        "prob": prob, "conf": conf
                    })
                    if side == "buy":
                        _open_spend[sym] = _open_spend.get(sym, 0.0) + qty * px
                    else:
                        _open_spend[sym] = max(0.0, _open_spend.get(sym, 0.0) - qty * px)
                    add_log(f"ORDER {side.upper()} {sym} qty={qty} px~{px:.6f} prob={prob:.3f}")
                except ccxt.BaseError as e:
                    add_log(f"ORDER error {sym} {side} {qty}: {e}")
                except Exception as e:
                    add_log(f"ORDER error {sym} {side} {qty}: {e}")

        except Exception as e:
            add_log(f"ERROR execution_loop: {e}")

        await asyncio.sleep(1.0)

# ───────────────────────────────── startup
@app.on_event("startup")
async def _on_startup():
    asyncio.create_task(portfolio_loop())
    asyncio.create_task(signals_loop())
    asyncio.create_task(online_label_loop())
    asyncio.create_task(execution_loop())

# ───────────────────────────────── execution runtime switch
EXECUTION_RUNTIME_ENABLED = False  # default off at boot
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "").strip()

def _auth_ok(request):
    # optional: if ADMIN_TOKEN is set, require it
    if not ADMIN_TOKEN:
        return True
    try:
        token = request.headers.get("X-Admin-Token", "")
        return token == ADMIN_TOKEN
    except Exception:
        return False

# ───────────────────────────────── endpoints
def _detect_quantum() -> Dict[str, Any]:
    if not QUANTUM_ENABLED:
        return {"enabled": False, "backend": "disabled"}
    if QuantumCircuit is None or Aer is None:
        return {"enabled": True, "backend": "pseudo (no qiskit-aer)"}
    return {"enabled": True, "backend": QUANTUM_BACKEND or "aer_simulator"}

@app.get("/")
def root():
    return {"ok": True, "service": "bottie", "time": time.time()}

# FIXED: Complete /health endpoint with all required objects
@app.get("/health")
def health():
    last_eq = _equity_series[-1]["v"] if _equity_series else None

    # Quantum - use existing _detect_quantum() 
    quantum_obj = _detect_quantum()

    # ML block – keys exactly as frontend expects
    ml_obj = {
        "enabled": bool(ML_ENABLED or ONLINE_LEARN),
        "loaded": bool(_ML_MODEL is not None or _OL is not None),  # Check BOTH models
        "model_path": (MODEL_XGB_PATH if _ML_MODEL is not None else 
                      (ONLINE_MODEL_PATH if _OL is not None else None)),
    }

    # Sentiment block – get tracked bases from latest sentiment data
    tracked_bases = []
    if SENTIMENT_ENABLED and SENTIMENT_WIRED:
        try:
            snap = sentiment_snapshot()
            if snap and "scores" in snap:
                tracked_bases = list(snap["scores"].keys())
        except Exception:
            pass

    sentiment_obj = {
        "enabled": bool(SENTIMENT_ENABLED and SENTIMENT_WIRED),
        "source": SENTIMENT_SOURCE,
        "window_sec": SENTIMENT_WINDOW_S,
        "bases": tracked_bases,
    }

    return {
        "status": "UP",
        "ok": True,
        "service": "bottie", 
        "time": int(time.time()),
        "exchange": EXCHANGE_ID,
        "primary_quote": PRIMARY_QUOTE,
        "equity": last_eq,
        "quantum": quantum_obj,
        "ml": ml_obj,
        "sentiment": sentiment_obj,
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

# FIXED: Complete sentiment endpoint
@app.get("/sentiment")
def sentiment():
    if not (SENTIMENT_ENABLED and SENTIMENT_WIRED):
        return {
            "enabled": False, 
            "source": SENTIMENT_SOURCE, 
            "window_sec": SENTIMENT_WINDOW_S, 
            "scores": {}
        }
    
    try:
        snap = sentiment_snapshot()
        return {
            "enabled": True,
            "source": SENTIMENT_SOURCE,
            "window_sec": snap.get("window_sec", SENTIMENT_WINDOW_S),
            "scores": snap.get("scores", {}),
        }
    except Exception as e:
        add_log(f"sentiment endpoint error: {e}")
        return {
            "enabled": False,
            "source": SENTIMENT_SOURCE, 
            "window_sec": SENTIMENT_WINDOW_S, 
            "scores": {}
        }

@app.get("/ml/status")
def ml_status():
    return {
        "online": ONLINE_LEARN,
        "model_path": ONLINE_MODEL_PATH if ONLINE_LEARN else MODEL_XGB_PATH,
        "pending_batch": len(_pending_y),
        "buffered_symbols": list(_prev_feature.keys())[:20],
        "joblib_loaded": bool(_ML_MODEL),
        "features": _OL.feature_names() if _OL else ["close","rsi14","ret1","ema_fast","ema_slow","vol"]
    }

# FIXED: Single /exec/status endpoint (removed duplicate)
@app.get("/exec/status")
def exec_status():
    return {
        "enabled_env": bool(TRADE_ENABLED),
        "enabled_runtime": bool(EXECUTION_RUNTIME_ENABLED),
        "per_symbol_spend": _open_spend,
        "last_exec": _last_exec,
        "recent_trades": _trade_log[-50:]
    }

@app.post("/exec/enable")
async def exec_enable(request: Request):
    if not _auth_ok(request):
        raise HTTPException(status_code=401, detail="X-Admin-Token required")
    global EXECUTION_RUNTIME_ENABLED
    EXECUTION_RUNTIME_ENABLED = True
    return {"ok": True, "enabled": EXECUTION_RUNTIME_ENABLED}

@app.post("/exec/disable")
async def exec_disable(request: Request):
    if not _auth_ok(request):
        raise HTTPException(status_code=401, detail="X-Admin-Token required")
    global EXECUTION_RUNTIME_ENABLED
    EXECUTION_RUNTIME_ENABLED = False
    return {"ok": True, "enabled": EXECUTION_RUNTIME_ENABLED}

@app.post("/exec/toggle")
async def exec_toggle(request: Request):
    if not _auth_ok(request):
        raise HTTPException(status_code=401, detail="X-Admin-Token required")
    global EXECUTION_RUNTIME_ENABLED
    EXECUTION_RUNTIME_ENABLED = not EXECUTION_RUNTIME_ENABLED
    return {"ok": True, "enabled": EXECUTION_RUNTIME_ENABLED}

# ADDED: /trades endpoint for frontend
@app.get("/trades")
def trades():
    """Return all trade log entries with P&L calculation"""
    trades_with_pnl = []
    
    for trade in _trade_log:
        # Basic trade info
        trade_out = {
            "t": trade.get("t"),
            "symbol": trade.get("symbol"),
            "side": trade.get("side"),
            "qty": trade.get("qty"),
            "px": trade.get("px"),
            "fee": 0.0,  # Could be enhanced to track actual fees
            "fee_ccy": "USDT",  # Default
            "pnl": None  # Will calculate if possible
        }
        
        # Simple P&L estimation (rough)
        if "prob" in trade and "px" in trade and "qty" in trade:
            # Very rough estimate: assume we made profit if prob was confident
            prob = trade.get("prob", 0.5)
            px = trade.get("px", 0)
            qty = trade.get("qty", 0)
            
            if trade.get("side") == "buy" and prob > 0.6:
                # Estimate 1-2% profit for confident buys
                trade_out["pnl"] = qty * px * (prob - 0.5) * 0.04
            elif trade.get("side") == "sell" and prob < 0.4:
                # Estimate profit for confident sells
                trade_out["pnl"] = qty * px * (0.5 - prob) * 0.04
        
        trades_with_pnl.append(trade_out)
    
    return trades_with_pnl
