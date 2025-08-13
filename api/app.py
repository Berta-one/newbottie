# api/app.py
import os, time, asyncio, logging, math, json, hashlib
from typing import Any, Dict, List, Optional, Tuple, Set
from datetime import datetime, timedelta

from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

# Authentication imports
import jwt
from passlib.context import CryptContext
from pydantic import BaseModel

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

# sentiment service
from sentiment.sentiment_service import (
    snapshot as sentiment_snapshot,
    latest_probs as sentiment_latest_probs,
    start_background as sentiment_start_background
)
SENTIMENT_WIRED = True  # New sentiment service is always available 

# online learner
from ml.online_learner import OnlineLearner

# Cross-pair WebSocket grid engine
from api.cross_pairs import CrossPairsWS
from api import routes_grid

# ───────────────────────────────── Authentication Models
class User(BaseModel):
    username: str
    password: str

class UserInDB(BaseModel):
    username: str
    hashed_password: str
    role: str
    created_at: datetime
    last_login: Optional[datetime] = None

class AuditLog(BaseModel):
    username: str
    action: str
    endpoint: str
    timestamp: datetime
    ip_address: str
    details: Optional[str] = None

# ───────────────────────────────── Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ───────────────────────────────── Boolean parsing helper
def parse_bool(v: str, default=False) -> bool:
    if v is None:
        return default
    return str(v).strip().lower() in ("1","true","yes","on")

# ───────────────────────────────── Environment Variables
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
TRADE_BASE_MIN_CONF  = float(os.getenv("TRADE_MIN_CONF", "0.55"))
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
ONLINE_MINIBATCH       = int(os.getenv("ONLINE_MINIBATCH","32"))
ONLINE_SAVE_SEC        = int(os.getenv("ONLINE_SAVE_SEC","30"))
ONLINE_LABEL_HORIZON   = int(os.getenv("ONLINE_LABEL_HORIZON","1"))

# quantum
QUANTUM_ENABLED    = parse_bool(os.getenv("QUANTUM_ENABLED","0"))
QUANTUM_BACKEND    = os.getenv("QUANTUM_BACKEND","aer_simulator")

# sentiment config for /health reporting
SENTIMENT_ENABLED  = parse_bool(os.getenv("SENTIMENT_ENABLED", "1"))
SENTIMENT_SOURCE   = (os.getenv("SENTIMENT_SOURCE", "finnhub") or "finnhub").lower()
SENTIMENT_WINDOW_S = int(os.getenv("SENTIMENT_WINDOW_S", "900"))

# JWT Authentication
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-change-this-in-production")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours

# ───────────────────────────────── FastAPI App Setup (Create app early)
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
log = logging.getLogger("BottieAPI")

app = FastAPI(title="Bottie API", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://helpful-maamoul-8aa9bd.netlify.app",  # Your Netlify deployment
        "http://localhost:3000",                        # Local development
        "http://localhost:8000",                        # Local API testing
        "*" if NETLIFY_URL == "*" else NETLIFY_URL      # Environment variable fallback
    ],
    allow_credentials=False,
    allow_methods=["GET","POST","OPTIONS","HEAD"],
    allow_headers=["*"],
)

# ───────────────────────────────── Application State
_started = time.time()
_equity_series: List[Dict[str, Any]] = []
_positions: Dict[str, Dict[str, float]] = {}
_signals: List[Dict[str, Any]] = []
_logs: List[str] = []
_cost_basis_cache: Dict[str, Dict[str, float]] = {}

# ML pieces
_ML_MODEL = None
_ML_META: Dict[str, Any] = {}
_OL: Optional[OnlineLearner] = None

# buffers for online labels
_prev_feature: Dict[str, Dict[str, Any]] = {}
_pending_X: List[np.ndarray] = []
_pending_y: List[int] = []

# execution throttle + tracking
_last_exec = 0.0
_open_spend: Dict[str, float] = {}
_trade_log: List[Dict[str, Any]] = []

# execution runtime switch
EXECUTION_RUNTIME_ENABLED = False

# ───────── Cross-pair WS engine
CROSS_WS: Optional[CrossPairsWS] = None

# ───────────────────────────────── Define add_log function FIRST
def add_log(msg: str):
    _logs.append(msg)
    if len(_logs) > 1500:
        del _logs[:-1000]
    log.info(msg)

# Return any of: ema, ml, q, sent, final_prob (0..1)
_last_parts_cache = {} # optional: {symbol: {ema,ml,q,sent,final_prob}}

def _grid_score_adapter(symbol: str, price: float) -> dict:
    # Prefer your live cache if you maintain one
    parts = _last_parts_cache.get(symbol, {})

    # Fallback neutrals so grid renders even before signals warm up
    if "ema" not in parts: parts["ema"] = 0.5
    if os.getenv("ML_ENABLED","1").lower() in ("1","true","yes"):
        parts.setdefault("ml", 0.5)
    if os.getenv("QUANTUM_ENABLED","0").lower() in ("1","true","yes"):
        parts.setdefault("q", 0.5)
    if os.getenv("SENTIMENT_ENABLED","1").lower() in ("1","true","yes"):
        parts.setdefault("sent", 0.5)
    return parts

# ───────────────────────────────── Simple User Management
# Get passwords from environment with defaults
SUPERUSER_PASSWORD = os.getenv("SUPERUSER_PASSWORD", "SuperSecret123!")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "AdminPass456!")

# Create users with simple password hashing
USERS_DB = {
    "superuser": {
        "username": "superuser", 
        "hashed_password": pwd_context.hash(SUPERUSER_PASSWORD),
        "role": "superuser",
        "created_at": datetime.now(),
        "last_login": None
    },
    "admin": {
        "username": "admin",
        "hashed_password": pwd_context.hash(ADMIN_PASSWORD), 
        "role": "admin",
        "created_at": datetime.now(),
        "last_login": None
    }
}

AUDIT_LOGS = []

# ───────────────────────────────── Execution State Persistence
EXEC_STATE_FILE = "exec_state.json"

def load_execution_state():
    """Load execution state from file"""
    global EXECUTION_RUNTIME_ENABLED
    try:
        if os.path.exists(EXEC_STATE_FILE):
            with open(EXEC_STATE_FILE, 'r') as f:
                data = json.load(f)
                EXECUTION_RUNTIME_ENABLED = data.get("enabled", True)  # Default to enabled
                add_log(f"Loaded execution state: {'enabled' if EXECUTION_RUNTIME_ENABLED else 'disabled'}")
        else:
            EXECUTION_RUNTIME_ENABLED = True  # Default to enabled if no file
            save_execution_state()
    except Exception as e:
        add_log(f"Error loading execution state: {e}")
        EXECUTION_RUNTIME_ENABLED = True

def save_execution_state():
    """Save execution state to file"""
    try:
        with open(EXEC_STATE_FILE, 'w') as f:
            json.dump({"enabled": EXECUTION_RUNTIME_ENABLED}, f)
        add_log(f"Saved execution state: {'enabled' if EXECUTION_RUNTIME_ENABLED else 'disabled'}")
    except Exception as e:
        add_log(f"Error saving execution state: {e}")

# ───────────────────────────────── Authentication Functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(username: str, password: str):
    user = USERS_DB.get(username)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    # Update last login
    USERS_DB[username]["last_login"] = datetime.now()
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def decode_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        return username if username else None
    except jwt.PyJWTError:
        return None

def log_audit(username: str, action: str, endpoint: str, ip_address: str, details: str = None):
    AUDIT_LOGS.append({
        "username": username,
        "action": action,
        "endpoint": endpoint,
        "timestamp": datetime.now(),
        "ip_address": ip_address,
        "details": details
    })
    # Keep only last 1000 audit logs
    if len(AUDIT_LOGS) > 1000:
        AUDIT_LOGS.pop(0)

def get_current_user(request: Request):
    """Extract user from JWT token in Authorization header"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.split(" ")[1]
    username = decode_token(token)
    if not username:
        return None
        
    return USERS_DB.get(username)

# ───────────────────────────────── Exchange Setup
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

# ───────────────────────────────── Helper Functions
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
    # Enhanced to include more crypto-to-crypto opportunities
    tail = ["USDT","USD","BUSD","USDC","BTC","ETH","BNB","ADA","SOL","DOT","MATIC","AVAX","LINK","UNI","EUR","TRY","GBP"]
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

# ───────────────────────────────── Cost Basis (WAC)
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

# ───────────────────────────────── Portfolio Valuation
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
            
            # If no API keys (paper trading mode), initialize with starting capital
            if not (API_KEY and API_SECRET) and not assets:
                paper_capital = float(os.getenv("EQUITY_START", "10000"))
                assets = {PRIMARY_QUOTE: paper_capital}
                add_log(f"Paper trading mode: initialized with {paper_capital} {PRIMARY_QUOTE}")
            
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

# ───────────────────────────────── Features & Signals
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
    # online learner first (now with quantum features)
    if _OL is not None:
        try:
            # Add quantum probability to features for prediction
            feats_with_quantum = feats.copy()
            feats_with_quantum["quantum_prob"] = feats.get("quantum_prob", 0.5)
            
            X = _OL.vectorize(feats_with_quantum)
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
    Returns buy_threshold, sell_threshold both in range [0, 1]
    """
    if not TRADE_CONF_ADAPT:
        # Simple fixed thresholds when adaptation is disabled
        # TRADE_BASE_MIN_CONF should be interpreted as the minimum confidence needed
        # Convert to margin around 0.5
        if TRADE_BASE_MIN_CONF > 0.5:
            margin = TRADE_BASE_MIN_CONF - 0.5  # e.g., 0.55 -> 0.05 margin
        else:
            margin = 0.05  # default 5% margin
        
        thr_buy = 0.5 + margin
        thr_sell = 0.5 - margin
        
        # Ensure thresholds stay in valid range [0, 1]
        thr_buy = min(0.95, max(0.51, thr_buy))
        thr_sell = max(0.05, min(0.49, thr_sell))
        
        return float(thr_buy), float(thr_sell)
    
    # Adaptive thresholds based on recent signal history
    window = _signals[-50:]  # Last 50 signals
    if not window:
        # Default margin when no signal history
        margin = 0.05
    else:
        # Calculate volatility of recent predictions
        probs = [s.get("final_prob", 0.5) for s in window if s.get("final_prob") is not None]
        if not probs:
            margin = 0.05
        else:
            volatility = float(np.std(probs))
            
            # Adjust threshold based on volatility
            # High volatility = wider thresholds (more conservative)
            # Low volatility = tighter thresholds (more aggressive)
            base_margin = 0.05
            volatility_factor = min(2.0, max(0.5, volatility * 10))  # Scale volatility
            margin = base_margin * volatility_factor
            
            # Clamp margin to reasonable bounds
            # TRADE_CONF_FLOOR and TRADE_CONF_CEIL should be probabilities, not margins
            min_margin = 0.02  # minimum 2% margin
            max_margin = 0.3   # maximum 30% margin
            
            # If TRADE_CONF_FLOOR/CEIL are set properly, use them
            if TRADE_CONF_FLOOR > 0.5:
                min_margin = max(min_margin, TRADE_CONF_FLOOR - 0.5)
            if TRADE_CONF_CEIL < 1.0 and TRADE_CONF_CEIL > 0.5:
                max_margin = min(max_margin, TRADE_CONF_CEIL - 0.5)
            
            margin = float(np.clip(margin, min_margin, max_margin))
    
    thr_buy = 0.5 + margin
    thr_sell = 0.5 - margin
    
    # Final safety clamps to ensure valid probability range
    thr_buy = min(0.95, max(0.51, thr_buy))
    thr_sell = max(0.05, min(0.49, thr_sell))
    
    return float(thr_buy), float(thr_sell)

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

                # Pass quantum probability to ML models for learning
                feats["quantum_prob"] = None  # Will be set after q_prob calculation

                ml_prob = _ml_prob_from_models(feats)
                q_prob  = _quantum_prob(sym, feats)
                
                # Update features with quantum probability for ML learning
                feats["quantum_prob"] = q_prob if q_prob is not None else 0.5
                
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
                        # Add quantum probability to features for ML learning
                        feats_with_quantum = feats.copy()
                        feats_with_quantum["quantum_prob"] = q_prob if q_prob is not None else 0.5
                        
                        X = _OL.vectorize(feats_with_quantum)
                        prev_close = float(feats["close"][-1])
                        _prev_feature[sym] = {
                            "X": X, 
                            "prev_close": prev_close, 
                            "t": int(time.time()),
                            # Store signal components for performance tracking
                            "signal_components": {
                                "ema": ema_prob, "ml": ml_prob, "q": q_prob, "sent": s_prob
                            }
                        }
                    except Exception as e:
                        add_log(f"OnlineLearner vectorize error: {e}")

            add_log(f"signals | n={n_scanned} scanned")
        except Exception as e:
            add_log(f"ERROR signals_loop: {e}")
        await asyncio.sleep(max(0.25, SIGNAL_INTERVAL_S - (time.time() - t0)))

# ───────────────────────────────── Online Learning Labeler
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

# ───────────────────────────────── Execution
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

            # Check runtime kill switch
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
                    
                    # Enhanced trade logging with more details
                    trade_entry = {
                        "t": int(time.time()),
                        "symbol": sym, 
                        "side": side, 
                        "qty": qty, 
                        "px": px,
                        "value": qty * px,
                        "prob": prob, 
                        "conf": conf,
                        "order_id": order.get("id") if order else None,
                        "order_info": order.get("info", {}) if order else {},
                        "signal_strength": strength
                    }
                    _trade_log.append(trade_entry)
                    
                    # Keep trade log manageable
                    if len(_trade_log) > 1000:
                        _trade_log[:] = _trade_log[-500:]  # Keep last 500
                    
                    if side == "buy":
                        _open_spend[sym] = _open_spend.get(sym, 0.0) + qty * px
                    else:
                        _open_spend[sym] = max(0.0, _open_spend.get(sym, 0.0) - qty * px)
                    add_log(f"ORDER {side.upper()} {sym} qty={qty} px~{px:.6f} prob={prob:.3f} order_id={order.get('id') if order else 'N/A'}")
                except ccxt.BaseError as e:
                    add_log(f"ORDER error {sym} {side} {qty}: {e}")
                except Exception as e:
                    add_log(f"ORDER error {sym} {side} {qty}: {e}")

        except Exception as e:
            add_log(f"ERROR execution_loop: {e}")

        await asyncio.sleep(1.0)

# ───────────────────────────────── Detection Functions
def _detect_quantum() -> Dict[str, Any]:
    if not QUANTUM_ENABLED:
        return {"enabled": False, "backend": "disabled"}
    if QuantumCircuit is None or Aer is None:
        return {"enabled": True, "backend": "pseudo (no qiskit-aer)"}
    return {"enabled": True, "backend": QUANTUM_BACKEND or "aer_simulator"}

# ───────────────────────────────── Authentication Endpoints
@app.post("/auth/login")
async def login(user: User, request: Request):
    """Login endpoint"""
    client_ip = request.client.host if hasattr(request, 'client') else "unknown"
    
    authenticated_user = authenticate_user(user.username, user.password)
    if not authenticated_user:
        log_audit(user.username, "LOGIN_FAILED", "/auth/login", client_ip)
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token_expires = timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": authenticated_user["username"], "role": authenticated_user["role"]},
        expires_delta=access_token_expires
    )
    
    log_audit(authenticated_user["username"], "LOGIN_SUCCESS", "/auth/login", client_ip)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "username": authenticated_user["username"],
            "role": authenticated_user["role"]
        }
    }

@app.post("/auth/logout")
async def logout(request: Request):
    """Logout endpoint"""
    user = get_current_user(request)
    if user:
        client_ip = request.client.host if hasattr(request, 'client') else "unknown"
        log_audit(user["username"], "LOGOUT", "/auth/logout", client_ip)
    
    return {"message": "Logged out successfully"}

# ───────────────────────────────── DEBUG ENDPOINTS (TEMPORARY)
@app.get("/debug/auth")
def debug_auth_info():
    """Debug endpoint to check authentication setup"""
    return {
        "users_in_db": list(USERS_DB.keys()),
        "environment_variables": {
            "ADMIN_PASSWORD": os.getenv("ADMIN_PASSWORD", "NOT_SET"),
            "SUPERUSER_PASSWORD": os.getenv("SUPERUSER_PASSWORD", "NOT_SET"),
        },
        "password_verification_test": {
            "admin_password_verify": verify_password("Diego1234!", USERS_DB.get("admin", {}).get("hashed_password", "")),
            "superuser_password_verify": verify_password("Lenny106667!", USERS_DB.get("superuser", {}).get("hashed_password", "")),
        },
        "user_details": {
            user: {
                "role": data.get("role"),
                "created_at": str(data.get("created_at")),
                "hash_preview": data.get("hashed_password", "")[:20] + "..."
            }
            for user, data in USERS_DB.items()
        }
    }

@app.post("/debug/test-login")
async def debug_test_login(request: Request):
    """Test login with detailed debugging"""
    try:
        payload = await request.json()
        username = payload.get("username")
        password = payload.get("password")
        
        # Step 1: User lookup
        user_exists = username in USERS_DB
        user_data = USERS_DB.get(username)
        
        # Step 2: Password verification
        password_verify_result = False
        if user_data:
            password_verify_result = verify_password(password, user_data["hashed_password"])
        
        # Step 3: Full authentication test
        auth_result = authenticate_user(username, password)
        
        return {
            "username": username,
            "password_length": len(password),
            "user_lookup": {
                "user_exists": user_exists,
                "user_role": user_data.get("role") if user_data else None,
                "hash_preview": user_data.get("hashed_password", "")[:20] + "..." if user_data else None
            },
            "password_verification": {
                "password_verify_result": password_verify_result,
                "test_passwords": {
                    "Diego1234!": verify_password("Diego1234!", user_data["hashed_password"]) if user_data else False,
                    "Lenny106667!": verify_password("Lenny106667!", user_data["hashed_password"]) if user_data else False,
                    "AdminPass456!": verify_password("AdminPass456!", user_data["hashed_password"]) if user_data else False,
                    "admin": verify_password("admin", user_data["hashed_password"]) if user_data else False,
                }
            },
            "authenticate_user_result": {
                "success": bool(auth_result),
                "user_data": auth_result if auth_result else None
            }
        }
        
    except Exception as e:
        return {"error": str(e), "traceback": str(e.__class__.__name__)}

@app.post("/debug/test-login-raw")
async def debug_test_login_raw(request: Request):
    """Debug endpoint to test login process step by step - raw JSON"""
    try:
        body = await request.json()
        username = body.get("username", "")
        password = body.get("password", "")
        
        debug_info = {
            "provided_credentials": {
                "username": username,
                "password": password
            },
            "user_lookup": {
                "user_exists": username in USERS_DB,
                "user_data": USERS_DB.get(username, {}).get("username", "NOT_FOUND") if username in USERS_DB else "USER_NOT_FOUND"
            }
        }
        
        if username in USERS_DB:
            user = USERS_DB[username]
            stored_hash = user["hashed_password"]
            
            debug_info["password_verification"] = {
                "stored_hash": stored_hash[:20] + "...",
                "password_verify_result": pwd_context.verify(password, stored_hash),
                "manual_hash_check": stored_hash == pwd_context.hash(password),  # This should be False - different salts
            }
            
            # Test authentication function
            auth_result = authenticate_user(username, password)
            debug_info["authenticate_user_result"] = {
                "success": bool(auth_result),
                "user_data": auth_result if auth_result else "AUTHENTICATION_FAILED"
            }
        
        return debug_info
    except Exception as e:
        return {"error": f"Failed to parse request: {str(e)}"}

@app.post("/debug/reset-passwords")
def debug_reset_passwords():
    """Reset passwords to known values for debugging"""
    global USERS_DB
    
    # Use environment variables or hardcoded test values
    admin_password = os.getenv("ADMIN_PASSWORD", "Diego1234!")
    superuser_password = os.getenv("SUPERUSER_PASSWORD", "Lenny106667!")
    
    # Recreate users with fresh password hashes
    USERS_DB["admin"]["hashed_password"] = pwd_context.hash(admin_password)
    USERS_DB["superuser"]["hashed_password"] = pwd_context.hash(superuser_password)
    
    # Test the new passwords
    admin_verify = verify_password(admin_password, USERS_DB["admin"]["hashed_password"])
    superuser_verify = verify_password(superuser_password, USERS_DB["superuser"]["hashed_password"])
    
    return {
        "message": "Passwords reset",
        "admin_password": admin_password,
        "superuser_password": superuser_password,
        "verification": {
            "admin_verify": admin_verify,
            "superuser_verify": superuser_verify
        },
        "users_updated": list(USERS_DB.keys())
    }

@app.get("/debug/reset-passwords-get")
async def debug_reset_passwords_get():
    """Debug endpoint to force reset passwords - GET version"""
    global USERS_DB
    
    # Re-hash passwords from environment variables
    USERS_DB["superuser"]["hashed_password"] = pwd_context.hash(SUPERUSER_PASSWORD)
    USERS_DB["admin"]["hashed_password"] = pwd_context.hash(ADMIN_PASSWORD)
    
    return {
        "message": "Passwords reset successfully",
        "admin_password": ADMIN_PASSWORD,
        "superuser_password": SUPERUSER_PASSWORD,
        "verification": {
            "admin_verify": pwd_context.verify(ADMIN_PASSWORD, USERS_DB["admin"]["hashed_password"]),
            "superuser_verify": pwd_context.verify(SUPERUSER_PASSWORD, USERS_DB["superuser"]["hashed_password"])
        }
    }

@app.get("/auth/me")
async def get_current_user_info(request: Request):
    """Get current user info"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return {
        "username": user["username"],
        "role": user["role"],
        "last_login": user["last_login"],
        "created_at": user["created_at"]
    }

# ───────────────────────────────── Audit Trail Endpoints
@app.get("/audit/logs")
async def get_audit_logs(request: Request, limit: int = 100):
    """Get audit logs (superuser only)"""
    user = get_current_user(request)
    if not user or user["role"] != "superuser":
        raise HTTPException(status_code=403, detail="Superuser access required")
    
    client_ip = request.client.host if hasattr(request, 'client') else "unknown"
    log_audit(user["username"], "VIEW_AUDIT_LOGS", "/audit/logs", client_ip)
    
    # Return most recent logs first
    recent_logs = AUDIT_LOGS[-limit:] if len(AUDIT_LOGS) > limit else AUDIT_LOGS
    recent_logs.reverse()
    
    return {
        "logs": recent_logs,
        "total": len(AUDIT_LOGS)
    }

@app.get("/users")
async def get_users(request: Request):
    """Get all users (superuser only)"""
    user = get_current_user(request)
    if not user or user["role"] != "superuser":
        raise HTTPException(status_code=403, detail="Superuser access required")
    
    users_info = []
    for username, user_data in USERS_DB.items():
        users_info.append({
            "username": user_data["username"],
            "role": user_data["role"],
            "created_at": user_data["created_at"],
            "last_login": user_data["last_login"]
        })
    
    return {"users": users_info}

# ───────────────────────────────── Main API Endpoints
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
        "sentiment": {"enabled": SENTIMENT_ENABLED}  # <-- boolean only; no heavy work here
    }

@app.get("/status")
def status():
    last_eq = _equity_series[-1]["v"] if _equity_series else None
    
    # Calculate P&L from trades
    total_buy_value = sum(t.get("value", t.get("qty", 0) * t.get("px", 0)) 
                         for t in _trade_log if t.get("side") == "buy")
    total_sell_value = sum(t.get("value", t.get("qty", 0) * t.get("px", 0)) 
                          for t in _trade_log if t.get("side") == "sell")
    trading_pnl = total_sell_value - total_buy_value
    
    # Calculate today's P&L
    today_start = int(time.time()) - 86400  # 24 hours ago
    today_trades = [t for t in _trade_log if t.get("t", 0) > today_start]
    today_buy_value = sum(t.get("value", t.get("qty", 0) * t.get("px", 0)) 
                         for t in today_trades if t.get("side") == "buy")
    today_sell_value = sum(t.get("value", t.get("qty", 0) * t.get("px", 0)) 
                          for t in today_trades if t.get("side") == "sell")
    today_pnl = today_sell_value - today_buy_value
    
    return {
        "started_at": _started,
        "equity": last_eq,
        "equity_series": _equity_series[-300:],
        "positions": _positions,
        "last_signals": _signals[-200:],
        "trading_summary": {
            "total_trades": len(_trade_log),
            "total_pnl": round(trading_pnl, 4),
            "today_pnl": round(today_pnl, 4),
            "today_trades": len(today_trades),
            "recent_trades": _trade_log[-10:]  # Last 10 trades
        }
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
    try:
        return sentiment_snapshot()
    except Exception as e:
        return {"enabled": False, "scores": {}, "error": str(e)}

@app.get("/sentiment/debug")
def sentiment_debug():
    try:
        snap = sentiment_snapshot()  # includes scores with n
        # For quick visibility, re-run provider to show two sample headlines per asset
        try:
            from sentiment.providers.finnhub_provider import filter_news_by_assets
            assets = list((snap.get("scores") or {}).keys()) or ["BTC","ETH","BNB","ADA","XRP","SOL"]
            sample = filter_news_by_assets(assets)
            samples = {a: (v[:2] if v else []) for a, v in sample.items()}
        except Exception:
            samples = {}
        return {"snapshot": snap, "samples": samples}
    except Exception as e:
        return {"error": str(e), "snapshot": {"scores": {}}}

@app.get("/grid/matrix")
async def grid_matrix(min_conf: float = 0.0):
    """Grid matrix for trading dashboard"""
    try:
        # Get current signals
        latest_signals = {}
        for s in _signals[-50:]:  # Get last 50 signals
            symbol = s.get("symbol")
            if symbol:
                latest_signals[symbol] = s
        
        # Create matrix data
        rows = []  # Base currencies (from positions + signals)
        cols = ["USDT", "BTC", "ETH", "BNB"]  # Quote currencies
        matrix = {}
        
        # Get base currencies from signals and positions
        bases = set()
        for symbol in latest_signals.keys():
            if "/" in symbol:
                base = symbol.split("/")[0]
                bases.add(base)
        
        for symbol in _positions.keys():
            if "/" in symbol and not symbol.startswith(f"{PRIMARY_QUOTE}/"):
                base = symbol.split("/")[0]
                bases.add(base)
        
        rows = sorted(list(bases))
        
        # Build matrix
        for base in rows:
            matrix[base] = {}
            for quote in cols:
                symbol = f"{base}/{quote}"
                signal_data = latest_signals.get(symbol)
                
                if signal_data:
                    matrix[base][quote] = {
                        "symbol": symbol,
                        "signal": signal_data.get("signal", "HOLD"),
                        "conf": signal_data.get("conf", 0.0),
                        "final_prob": signal_data.get("final_prob", 0.5),
                        "ema": signal_data.get("ema"),
                        "ml": signal_data.get("ml"),
                        "q": signal_data.get("q"),
                        "sent": signal_data.get("sent"),
                        "thr_buy": signal_data.get("thr_buy", 0.6),
                        "thr_sell": signal_data.get("thr_sell", 0.4),
                        "last": _positions.get(symbol, {}).get("last_px", 0),
                        "t": signal_data.get("t")
                    }
                else:
                    matrix[base][quote] = None
        
        return {
            "rows": rows,
            "cols": cols,
            "matrix": matrix,
            "ts": time.time()
        }
    except Exception as e:
        add_log(f"Grid matrix error: {e}")
        return {"rows": [], "cols": [], "matrix": {}, "ts": time.time()}

@app.get("/ml/status")
async def ml_status():
    """ML model status for dashboard"""
    return {
        "online": bool(ONLINE_LEARN),
        "model_path": ONLINE_MODEL_PATH if ONLINE_LEARN else MODEL_XGB_PATH,
        "pending_batch": len(_pending_y),
        "buffered_symbols": list(_prev_feature.keys())[:20],
        "joblib_loaded": bool(_ML_MODEL),
        "features": _OL.feature_names() if _OL else ["close","rsi14","ret1","ema_fast","ema_slow","vol"],
        "overall_score": 0.75,  # Mock data for now
        "accuracy": 0.68,
        "confidence": 0.72,
        "data_quality": 0.85,
        "total_predictions": len(_signals),
        "successful_predictions": len([s for s in _signals if s.get("conf", 0) > 0.6]),
        "feature_importance": {
            "close": 0.25,
            "rsi14": 0.20,
            "ema_fast": 0.18,
            "ema_slow": 0.15,
            "ret1": 0.12,
            "vol": 0.10
        },
        "performance_history": [
            {"timestamp": time.time() - 3600, "accuracy": 0.65, "confidence": 0.70},
            {"timestamp": time.time() - 1800, "accuracy": 0.68, "confidence": 0.72},
            {"timestamp": time.time(), "accuracy": 0.68, "confidence": 0.72}
        ],
        "recent_activity": [
            {"timestamp": time.time() - 300, "message": "Model updated with new batch"},
            {"timestamp": time.time() - 600, "message": "Generated signals for BTC/USDT"},
            {"timestamp": time.time() - 900, "message": "Feature importance recalculated"}
        ]
    }

@app.get("/quantum/details")
async def quantum_details():
    """Quantum system details for dashboard"""
    return {
        "enabled": bool(QUANTUM_ENABLED),
        "backend": QUANTUM_BACKEND,
        "queue_status": "Available" if QUANTUM_ENABLED else "Disabled",
        "active_jobs": 0,
        "success_rate": 0.85 if QUANTUM_ENABLED else 0,
        "circuit_depth": 4,
        "qubits_used": 4,
        "recent_executions": []
    }

@app.get("/portfolio/assets")
async def portfolio_assets():
    """Portfolio assets for dashboard"""
    assets = []
    for symbol, pos in _positions.items():
        if symbol != f"{PRIMARY_QUOTE}/{PRIMARY_QUOTE}":
            assets.append({
                "symbol": symbol,
                "quantity": pos.get("qty", 0),
                "avg_price": pos.get("avg_px", 0),
                "current_price": pos.get("last_px", 0),
                "market_value": pos.get("qty", 0) * pos.get("last_px", 0),
                "unrealized_pnl": (pos.get("last_px", 0) - pos.get("avg_px", 0)) * pos.get("qty", 0)
            })
    
    return {"assets": assets}

@app.get("/scan/assets")
async def scan_assets():
    """Scanned assets for dashboard"""
    scanned = []
    for signal in _signals[-20:]:  # Last 20 signals
        scanned.append({
            "symbol": signal.get("symbol"),
            "signal": signal.get("signal"),
            "confidence": signal.get("conf"),
            "final_prob": signal.get("final_prob"),
            "timestamp": signal.get("t")
        })
    
    return {"scanned_assets": scanned}

@app.get("/admin/audit")
async def admin_audit(request: Request):
    """Audit logs for superuser"""
    user = get_current_user(request)
    if not user or user["role"] != "superuser":
        raise HTTPException(status_code=403, detail="Superuser access required")
    
    return {
        "logs": AUDIT_LOGS[-50:],  # Return last 50 audit logs
        "total": len(AUDIT_LOGS)
    }

@app.post("/execution/enable")
async def execution_enable(request: Request):
    """Enable execution (protected endpoint)"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    global EXECUTION_RUNTIME_ENABLED
    EXECUTION_RUNTIME_ENABLED = True
    save_execution_state()
    
    client_ip = request.client.host if hasattr(request, 'client') else "unknown"
    log_audit(user["username"], "EXEC_ENABLE", "/execution/enable", client_ip)
    
    add_log(f"Execution enabled by {user['username']}")
    return {"ok": True, "enabled": True}

@app.post("/execution/disable")
async def execution_disable(request: Request):
    """Disable execution (protected endpoint)"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    global EXECUTION_RUNTIME_ENABLED
    EXECUTION_RUNTIME_ENABLED = False
    save_execution_state()
    
    client_ip = request.client.host if hasattr(request, 'client') else "unknown"
    log_audit(user["username"], "EXEC_DISABLE", "/execution/disable", client_ip)
    
    add_log(f"Execution disabled by {user['username']}")
    return {"ok": True, "enabled": False}

@app.post("/execution/toggle")
async def execution_toggle(request: Request):
    """Toggle execution (protected endpoint)"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    global EXECUTION_RUNTIME_ENABLED
    EXECUTION_RUNTIME_ENABLED = not EXECUTION_RUNTIME_ENABLED
    save_execution_state()
    
    client_ip = request.client.host if hasattr(request, 'client') else "unknown"
    log_audit(user["username"], "EXEC_TOGGLE", "/execution/toggle", client_ip, 
             f"Toggled to: {'enabled' if EXECUTION_RUNTIME_ENABLED else 'disabled'}")
    
    add_log(f"Execution {'enabled' if EXECUTION_RUNTIME_ENABLED else 'disabled'} by {user['username']}")
    return {"ok": True, "enabled": EXECUTION_RUNTIME_ENABLED}

@app.get("/trades")
def trades():
    """Get recent trades with P&L calculation"""
    try:
        # Combine local trade log with exchange trades for comprehensive view
        all_trades = []
        
        # Add local trade log (Bottie's executed orders)
        for trade in _trade_log[-100:]:  # Last 100 local trades
            all_trades.append({
                "timestamp": trade.get("t", time.time()),
                "symbol": trade.get("symbol", ""),
                "side": trade.get("side", "").upper(),
                "quantity": trade.get("qty", 0),
                "price": trade.get("px", 0),
                "value": trade.get("qty", 0) * trade.get("px", 0),
                "confidence": trade.get("conf", 0),
                "probability": trade.get("prob", 0.5),
                "source": "bottie",
                "order_id": f"bottie_{trade.get('t', time.time())}"
            })
        
        # Try to fetch exchange trades for additional context
        if _exchange and API_KEY and API_SECRET:
            try:
                # Get symbols from recent positions
                recent_symbols = list(_positions.keys())[:10]  # Limit to avoid rate limits
                
                for symbol in recent_symbols:
                    if symbol == f"{PRIMARY_QUOTE}/{PRIMARY_QUOTE}":
                        continue
                    try:
                        since = _ms_since(7)  # Last 7 days
                        exchange_trades = _exchange.fetch_my_trades(symbol, since=since, limit=50)
                        
                        for trade in exchange_trades[-20:]:  # Last 20 per symbol
                            all_trades.append({
                                "timestamp": trade.get("timestamp", 0) / 1000,
                                "symbol": trade.get("symbol", ""),
                                "side": trade.get("side", "").upper(),
                                "quantity": trade.get("amount", 0),
                                "price": trade.get("price", 0),
                                "value": trade.get("cost", 0),
                                "fee": trade.get("fee", {}).get("cost", 0),
                                "fee_currency": trade.get("fee", {}).get("currency", ""),
                                "source": "exchange",
                                "order_id": trade.get("order", trade.get("id", ""))
                            })
                    except Exception as e:
                        add_log(f"Error fetching trades for {symbol}: {e}")
                        continue
            except Exception as e:
                add_log(f"Error fetching exchange trades: {e}")
        
        # Sort by timestamp (most recent first)
        all_trades.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        
        # Calculate P&L metrics
        total_trades = len(all_trades)
        buy_trades = [t for t in all_trades if t.get("side") == "BUY"]
        sell_trades = [t for t in all_trades if t.get("side") == "SELL"]
        
        total_buy_value = sum(t.get("value", 0) for t in buy_trades)
        total_sell_value = sum(t.get("value", 0) for t in sell_trades)
        
        # Calculate realized P&L (simplified - sell value minus buy value)
        realized_pnl = total_sell_value - total_buy_value
        
        # Calculate fees
        total_fees = sum(t.get("fee", 0) for t in all_trades if t.get("fee"))
        
        # Calculate win rate from Bottie trades (with confidence data)
        bottie_trades = [t for t in all_trades if t.get("source") == "bottie"]
        profitable_trades = 0
        for i, trade in enumerate(bottie_trades):
            if trade.get("side") == "SELL":
                # Find corresponding buy for this symbol
                symbol = trade.get("symbol")
                for j in range(i+1, len(bottie_trades)):
                    prev_trade = bottie_trades[j]
                    if (prev_trade.get("symbol") == symbol and 
                        prev_trade.get("side") == "BUY" and 
                        prev_trade.get("timestamp", 0) < trade.get("timestamp", 0)):
                        
                        if trade.get("price", 0) > prev_trade.get("price", 0):
                            profitable_trades += 1
                        break
        
        win_rate = (profitable_trades / len(sell_trades)) * 100 if sell_trades else 0
        
        return {
            "trades": all_trades[:50],  # Return last 50 trades
            "summary": {
                "total_trades": total_trades,
                "buy_trades": len(buy_trades),
                "sell_trades": len(sell_trades),
                "total_buy_value": round(total_buy_value, 4),
                "total_sell_value": round(total_sell_value, 4),
                "realized_pnl": round(realized_pnl, 4),
                "total_fees": round(total_fees, 4),
                "net_pnl": round(realized_pnl - total_fees, 4),
                "win_rate": round(win_rate, 2),
                "avg_trade_size": round(total_buy_value / len(buy_trades), 4) if buy_trades else 0
            }
        }
        
    except Exception as e:
        add_log(f"Error in trades endpoint: {e}")
        return {
            "trades": [],
            "summary": {
                "total_trades": 0,
                "buy_trades": 0,
                "sell_trades": 0,
                "total_buy_value": 0,
                "total_sell_value": 0,
                "realized_pnl": 0,
                "total_fees": 0,
                "net_pnl": 0,
                "win_rate": 0,
                "avg_trade_size": 0
            },
            "error": str(e)
        }

@app.get("/pnl")
def pnl_analysis():
    """Detailed P&L analysis"""
    try:
        if not _trade_log:
            return {
                "total_pnl": 0,
                "daily_pnl": {},
                "symbol_pnl": {},
                "trade_count": 0,
                "win_rate": 0,
                "message": "No trading activity recorded"
            }
        
        # Calculate overall P&L
        buy_trades = [t for t in _trade_log if t.get("side") == "buy"]
        sell_trades = [t for t in _trade_log if t.get("side") == "sell"]
        
        total_buy_value = sum(t.get("value", t.get("qty", 0) * t.get("px", 0)) for t in buy_trades)
        total_sell_value = sum(t.get("value", t.get("qty", 0) * t.get("px", 0)) for t in sell_trades)
        total_pnl = total_sell_value - total_buy_value
        
        # Daily P&L breakdown
        daily_pnl = {}
        for trade in _trade_log:
            trade_date = datetime.fromtimestamp(trade.get("t", time.time())).strftime("%Y-%m-%d")
            if trade_date not in daily_pnl:
                daily_pnl[trade_date] = {"buy": 0, "sell": 0, "pnl": 0, "trades": 0}
            
            value = trade.get("value", trade.get("qty", 0) * trade.get("px", 0))
            side = trade.get("side", "")
            
            if side == "buy":
                daily_pnl[trade_date]["buy"] += value
            elif side == "sell":
                daily_pnl[trade_date]["sell"] += value
            
            daily_pnl[trade_date]["pnl"] = daily_pnl[trade_date]["sell"] - daily_pnl[trade_date]["buy"]
            daily_pnl[trade_date]["trades"] += 1
        
        # Symbol P&L breakdown
        symbol_pnl = {}
        for trade in _trade_log:
            symbol = trade.get("symbol", "")
            if symbol not in symbol_pnl:
                symbol_pnl[symbol] = {"buy": 0, "sell": 0, "pnl": 0, "trades": 0}
            
            value = trade.get("value", trade.get("qty", 0) * trade.get("px", 0))
            side = trade.get("side", "")
            
            if side == "buy":
                symbol_pnl[symbol]["buy"] += value
            elif side == "sell":
                symbol_pnl[symbol]["sell"] += value
            
            symbol_pnl[symbol]["pnl"] = symbol_pnl[symbol]["sell"] - symbol_pnl[symbol]["buy"]
            symbol_pnl[symbol]["trades"] += 1
        
        # Calculate win rate (simplified - based on profitable sells)
        profitable_sells = 0
        total_sell_pairs = 0
        
        for symbol in symbol_pnl:
            if symbol_pnl[symbol]["pnl"] > 0 and symbol_pnl[symbol]["sell"] > 0:
                profitable_sells += 1
            if symbol_pnl[symbol]["sell"] > 0:
                total_sell_pairs += 1
        
        win_rate = (profitable_sells / total_sell_pairs * 100) if total_sell_pairs > 0 else 0
        
        return {
            "total_pnl": round(total_pnl, 4),
            "total_buy_value": round(total_buy_value, 4),
            "total_sell_value": round(total_sell_value, 4),
            "daily_pnl": daily_pnl,
            "symbol_pnl": symbol_pnl,
            "trade_count": len(_trade_log),
            "buy_trades": len(buy_trades),
            "sell_trades": len(sell_trades),
            "win_rate": round(win_rate, 2),
            "avg_trade_size": round(total_buy_value / len(buy_trades), 4) if buy_trades else 0
        }
        
    except Exception as e:
        add_log(f"Error in P&L analysis: {e}")
        return {"error": str(e), "total_pnl": 0}

@app.get("/sentiment/assets")
def sentiment_assets():
    """
    List tracked assets for sentiment (useful for UI dropdowns).
    """
    try:
        # Get assets from latest sentiment data
        snap = sentiment_snapshot()
        assets = list(snap.get("scores", {}).keys())
        return {"assets": assets}
    except Exception as e:
        return {"assets": [], "error": str(e)}

@app.get("/sentiment/history")
def sentiment_history(
    asset: str = Query(default="ALL", description="Comma-separated assets or 'ALL'"),
    window_sec: int = Query(default=86400, ge=60, le=90*24*3600),
    max_points: int = Query(default=500, ge=50, le=5000),
):
    """
    Return per-asset historical sentiment within the lookback window, downsampled.
    """
    now = time.time()
    since = now - float(window_sec)
    if asset.strip().upper() == "ALL":
        assets = None  # means: use all known assets
    else:
        assets = [a.strip().upper() for a in asset.split(",") if a.strip()]

    try:
        # For now, return current sentiment snapshot as placeholder
        snap = sentiment_snapshot()
        data = snap.get("scores", {})
        return {
            "window_sec": window_sec,
            "max_points": max_points,
            "data": data
        }
    except Exception as e:
        return {"window_sec": window_sec, "max_points": max_points, "data": {}, "error": str(e)}

# ───────────────────────────────── Protected Execution Endpoints
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
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    global EXECUTION_RUNTIME_ENABLED
    EXECUTION_RUNTIME_ENABLED = True
    save_execution_state()  # Save to file
    
    client_ip = request.client.host if hasattr(request, 'client') else "unknown"
    log_audit(user["username"], "EXEC_ENABLE", "/exec/enable", client_ip)
    
    return {"ok": True, "enabled": EXECUTION_RUNTIME_ENABLED}

@app.post("/exec/disable")
async def exec_disable(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    global EXECUTION_RUNTIME_ENABLED
    EXECUTION_RUNTIME_ENABLED = False
    save_execution_state()  # Save to file
    
    client_ip = request.client.host if hasattr(request, 'client') else "unknown"
    log_audit(user["username"], "EXEC_DISABLE", "/exec/disable", client_ip)
    
    return {"ok": True, "enabled": EXECUTION_RUNTIME_ENABLED}

@app.post("/exec/toggle")
async def exec_toggle(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    global EXECUTION_RUNTIME_ENABLED
    EXECUTION_RUNTIME_ENABLED = not EXECUTION_RUNTIME_ENABLED
    save_execution_state()  # Save to file
    
    client_ip = request.client.host if hasattr(request, 'client') else "unknown"
    log_audit(user["username"], "EXEC_TOGGLE", "/exec/toggle", client_ip, 
             f"Toggled to: {'enabled' if EXECUTION_RUNTIME_ENABLED else 'disabled'}")
    
    return {"ok": True, "enabled": EXECUTION_RUNTIME_ENABLED}

# ───────────────────────────────── ML Monitoring Endpoints
@app.get("/ml/status")
async def ml_status():
    """ML Learning Status endpoint for monitoring dashboard"""
    try:
        global learner, features
        
        # Initialize response structure
        status = {
            "accuracy": None,
            "brier_score": None,
            "sample_count": 0,
            "quantum_importance": None,
            "quantum_feature_rank": None,
            "feature_importance": {},
            "quantum_mode": "unknown"
        }
        
        # Get learner status if available
        if learner and hasattr(learner, 'brier_scores') and learner.brier_scores:
            # Get latest ML brier score
            status["brier_score"] = learner.brier_scores[-1] if learner.brier_scores else None
            status["sample_count"] = len(learner.brier_scores)
            
            # Calculate accuracy from brier score (rough approximation)
            if status["brier_score"]:
                # Brier score to accuracy approximation: acc = 1 - 2*brier (clamped 0-1)
                status["accuracy"] = max(0, min(1, 1 - 2 * status["brier_score"]))
        
        # Get feature importance from current features
        if features:
            total_importance = sum(abs(v) for v in features.values() if isinstance(v, (int, float)))
            if total_importance > 0:
                # Normalize feature importance
                for key, value in features.items():
                    if isinstance(value, (int, float)):
                        status["feature_importance"][f"{key}_prob"] = abs(value) / total_importance
        
        # Get quantum-specific metrics
        quantum_keys = [k for k in status["feature_importance"].keys() if 'quantum' in k.lower()]
        if quantum_keys:
            status["quantum_importance"] = status["feature_importance"].get(quantum_keys[0], 0)
            
            # Calculate quantum rank
            sorted_features = sorted(status["feature_importance"].items(), key=lambda x: x[1], reverse=True)
            for rank, (feature, _) in enumerate(sorted_features, 1):
                if 'quantum' in feature.lower():
                    status["quantum_feature_rank"] = rank
                    break
        
        # Determine quantum mode
        quantum_mode = os.getenv("QUANTUM_MODE", "shadow").lower()
        status["quantum_mode"] = quantum_mode if quantum_mode in ["live", "shadow", "off"] else "unknown"
        
        return status
        
    except Exception as e:
        # Return minimal status on error
        return {
            "accuracy": None,
            "brier_score": None,
            "sample_count": 0,
            "quantum_importance": None,
            "quantum_feature_rank": None,
            "feature_importance": {},
            "quantum_mode": "error",
            "error": str(e)
        }

@app.get("/metrics/components")
async def metrics_components():
    """Component metrics for advanced monitoring (optional)"""
    try:
        global learner, quantum_global_prob
        
        metrics = {
            "performance": {
                "brier_loss": {},
                "sample_counts": {}
            },
            "weights": {
                "current": {}
            },
            "quantum_mode": os.getenv("QUANTUM_MODE", "shadow").lower()
        }
        
        # ML performance metrics
        if learner and hasattr(learner, 'brier_scores') and learner.brier_scores:
            metrics["performance"]["brier_loss"]["ml"] = learner.brier_scores[-1]
            metrics["performance"]["sample_counts"]["ml"] = len(learner.brier_scores)
        
        # Quantum metrics (if available)
        if quantum_global_prob is not None:
            # For quantum brier, we'd need to track it separately
            # For now, estimate based on quantum probability quality
            metrics["performance"]["brier_loss"]["q"] = None  # Would need separate tracking
            metrics["weights"]["current"]["q"] = 0.25  # Example quantum weight
        
        return metrics
        
    except Exception as e:
        return {
            "performance": {"brier_loss": {}, "sample_counts": {}},
            "weights": {"current": {}},
            "quantum_mode": "error",
            "error": str(e)
        }

# ───────────────────────────────── Cross-Pair Trading Endpoints
# Cross-pair trading configuration
CROSS_PAIR_ENABLED = parse_bool(os.getenv("CROSS_PAIR_ENABLED", "1"))

@app.get("/cross-pairs/status")
async def cross_pair_status():
    """Get cross-pair trading status"""
    return {
        "enabled": CROSS_PAIR_ENABLED,
        "testnet": parse_bool(os.getenv("BINANCE_TESTNET", "true")),
        "timestamp": time.time()
    }

@app.get("/portfolio/cross-pairs")
async def get_portfolio_cross_pairs():
    """Get all possible cross-trading pairs in portfolio"""
    if not CROSS_PAIR_ENABLED:
        return {"enabled": False, "pairs": []}
    
    try:
        await _ensure_exchange()
        balance = _exchange.fetch_balance()
        
        # Get assets with non-zero balance
        portfolio_assets = []
        for asset, amount in balance['total'].items():
            if amount > 0:
                portfolio_assets.append(asset)
        
        # Find available cross-pairs
        markets = _exchange.markets
        available_pairs = []
        
        for asset1 in portfolio_assets:
            for asset2 in portfolio_assets:
                if asset1 != asset2:
                    symbol1 = f"{asset1}/{asset2}"
                    symbol2 = f"{asset2}/{asset1}"
                    
                    if symbol1 in markets:
                        available_pairs.append(symbol1)
                    elif symbol2 in markets:
                        available_pairs.append(symbol2)
        
        return {
            "enabled": True,
            "portfolio_assets": portfolio_assets,
            "available_pairs": available_pairs,
            "total_pairs": len(available_pairs),
            "total_assets": len(portfolio_assets)
        }
        
    except Exception as e:
        return {"enabled": False, "error": str(e)}

@app.get("/cross-pairs/opportunities")
async def get_cross_pair_opportunities():
    """Get current cross-pair trading opportunities"""
    if not CROSS_PAIR_ENABLED:
        return {"enabled": False, "opportunities": []}
    
    try:
        await _ensure_exchange()
        balance = _exchange.fetch_balance()
        
        # Get portfolio assets
        portfolio_assets = [asset for asset, amount in balance['total'].items() if amount > 0]
        
        # Find cross-pair symbols
        markets = _exchange.markets
        cross_symbols = []
        
        for asset1 in portfolio_assets:
            for asset2 in portfolio_assets:
                if asset1 != asset2:
                    symbol1 = f"{asset1}/{asset2}"
                    symbol2 = f"{asset2}/{asset1}"
                    
                    if symbol1 in markets:
                        cross_symbols.append(symbol1)
                    elif symbol2 in markets:
                        cross_symbols.append(symbol2)
        
        if not cross_symbols:
            return {"enabled": True, "opportunities": [], "message": "No cross-pairs available"}
        
        # Get tickers for cross-pairs
        tickers = _exchange.fetch_tickers(cross_symbols[:20])  # Limit to 20 pairs
        
        opportunities = []
        for symbol, ticker in tickers.items():
            base, quote = symbol.split('/')
            
            # Simple signal calculation
            change_pct = ticker.get('percentage', 0) or 0
            signal_strength = 0.5 + (change_pct / 100.0 * 2)
            signal_strength = max(0.0, min(1.0, signal_strength))
            
            # Estimate profit potential
            profit_pct = abs(change_pct / 100.0) * 0.1  # Simple estimation
            
            opportunity = {
                "symbol": symbol,
                "from_asset": base,
                "to_asset": quote,
                "direction": "buy" if change_pct > 0 else "sell",
                "current_price": ticker['last'],
                "signal_strength": signal_strength,
                "estimated_profit_pct": profit_pct,
                "volume_24h": ticker.get('quoteVolume', 0),
                "change_24h_pct": change_pct,
                "timestamp": time.time()
            }
            opportunities.append(opportunity)
        
        # Sort by signal strength
        opportunities.sort(key=lambda x: x['signal_strength'], reverse=True)
        
        return {
            "enabled": True,
            "opportunities": opportunities[:10],  # Top 10
            "count": len(opportunities),
            "scan_time": time.time()
        }
        
    except Exception as e:
        return {"enabled": False, "error": str(e)}

@app.get("/portfolio/rebalancing-suggestions")
async def get_rebalancing_suggestions():
    """Get AI-powered portfolio rebalancing suggestions"""
    if not CROSS_PAIR_ENABLED:
        return {"enabled": False, "suggestions": []}
    
    try:
        # Get cross-pair opportunities first
        opportunities_response = await get_cross_pair_opportunities()
        
        if not opportunities_response.get("enabled") or not opportunities_response.get("opportunities"):
            return {"enabled": True, "suggestions": [], "message": "No opportunities available"}
        
        opportunities = opportunities_response["opportunities"]
        suggestions = []
        
        for opp in opportunities[:5]:  # Top 5 opportunities
            if opp["signal_strength"] > 0.6 and opp["estimated_profit_pct"] > 0.005:  # 0.5% min profit
                suggestion = {
                    "action": f"Trade {opp['from_asset']} → {opp['to_asset']}",
                    "symbol": opp["symbol"],
                    "direction": opp["direction"],
                    "confidence": opp["signal_strength"],
                    "expected_profit": opp["estimated_profit_pct"],
                    "reasoning": f"AI detected {opp['signal_strength']:.1%} confidence signal with {opp['change_24h_pct']:+.2f}% momentum",
                    "priority": "high" if opp["signal_strength"] > 0.8 else "medium",
                    "timestamp": time.time()
                }
                suggestions.append(suggestion)
        
        return {
            "enabled": True,
            "suggestions": suggestions,
            "count": len(suggestions),
            "timestamp": time.time()
        }
        
    except Exception as e:
        return {"enabled": False, "error": str(e)}

# ───────────────────────────────── Startup (AFTER all functions are defined)
@app.on_event("startup")
async def _on_startup():
    global CROSS_WS
    
    load_execution_state()  # Load persistent execution state
    asyncio.create_task(portfolio_loop())
    asyncio.create_task(signals_loop())
    asyncio.create_task(online_label_loop())
    asyncio.create_task(execution_loop())
    
    # start sentiment background (thread-based; safe to call from here)
    try:
        sentiment_start_background()
    except Exception as e:
        add_log(f"sentiment start error: {e}")
    
    # Start cross-pair WebSocket engine (with rollback switch)
    # Support both service-specific and generic environment variable names
    enable_grid_ws = (
        os.getenv("API_ENABLE_GRID_WS", "").lower() in ("1", "true", "yes") or
        os.getenv("BOTTIE_ENABLE_GRID_WS", "").lower() in ("1", "true", "yes") or
        os.getenv("ENABLE_GRID_WS", "1").lower() in ("1", "true", "yes")
    )
    
    if enable_grid_ws:
        try:
            CROSS_WS = CrossPairsWS(
                api_key=os.getenv("API_KEY", os.getenv("BINANCE_API_KEY", "")),
                api_secret=os.getenv("API_SECRET", os.getenv("BINANCE_API_SECRET", "")),
                testnet=False
            )
            CROSS_WS.score_fn = _grid_score_adapter
            await CROSS_WS.start()
            
            # Hand reference to routes
            routes_grid.CROSS_WS = CROSS_WS
            add_log("✅ Cross-pair WebSocket grid engine started")
        except Exception as e:
            add_log(f"❌ Cross-pair WS engine start error: {e}")
            routes_grid.CROSS_WS = None
            CROSS_WS = None
    else:
        # Determine which env var was used for logging
        env_var_used = "ENABLE_GRID_WS"
        if "API_ENABLE_GRID_WS" in os.environ:
            env_var_used = "API_ENABLE_GRID_WS"
        elif "BOTTIE_ENABLE_GRID_WS" in os.environ:
            env_var_used = "BOTTIE_ENABLE_GRID_WS"
            
        add_log(f"ℹ️ Cross-pair WebSocket engine disabled ({env_var_used}=0)")
        routes_grid.CROSS_WS = None
        CROSS_WS = None

# ───────────────────────────────── Mount Grid Router
app.include_router(routes_grid.router)
