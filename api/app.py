# api/app.py — LIVE spot (Binance), true WAC cost-basis, signals (EMA+quantum), execution with guards
import os
import time
import math
import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ---------------------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------------------
try:
    import ccxt  # exchange connectivity
except Exception as e:
    raise RuntimeError(f"ccxt not installed. Add to requirements.txt: {e}")

# Optional quantum libs (signals only). If missing, signals fall back to EMA.
try:
    import qiskit  # noqa: F401
    _HAS_QISKIT = True
except Exception:
    _HAS_QISKIT = False

# ---------------------------------------------------------------------------------------
# Config (Render/Heroku/… → Environment)
# ---------------------------------------------------------------------------------------
NETLIFY_URL       = os.getenv("NETLIFY_URL", "*")

EXCHANGE_ID       = os.getenv("EXCHANGE_ID", "binance").lower()
API_KEY           = os.getenv("API_KEY", os.getenv("BINANCE_API_KEY", ""))
API_SECRET        = os.getenv("API_SECRET", os.getenv("BINANCE_API_SECRET", ""))

# You said Binance only; the following are unused but kept for compatibility
API_PASSPHRASE    = os.getenv("API_PASSPHRASE", "")
API_UID           = os.getenv("API_UID", "")

PRIMARY_QUOTE     = os.getenv("PRIMARY_QUOTE", "USDT")
LOOP_SLEEP_S      = float(os.getenv("LOOP_SLEEP_S", "7.0"))
LOG_LEVEL         = os.getenv("LOG_LEVEL", "INFO").upper()

# Cost-basis options
COST_LOOKBACK_DAYS     = int(os.getenv("COST_BASIS_LOOKBACK_DAYS", "120"))
MAX_TRADES_PER_SYMBOL  = int(os.getenv("MAX_TRADES_PER_SYMBOL", "1000"))
FEE_IN_COST_BASIS      = os.getenv("FEE_IN_COST_BASIS", "1").lower() not in ("0", "false", "")
COST_CACHE_TTL_SEC     = int(os.getenv("COST_CACHE_TTL_SEC", "600"))

# Signals (EMA + optional quantum)
TRADE_SIGNALS_ENABLED  = os.getenv("TRADE_SIGNALS", "1").lower() not in ("0", "false", "")
TRADE_TIMEFRAME        = os.getenv("TRADE_TIMEFRAME", "1h")
TRADE_FAST_EMA         = int(os.getenv("TRADE_FAST_EMA", "12"))
TRADE_SLOW_EMA         = int(os.getenv("TRADE_SLOW_EMA", "26"))
TRADE_LOOKBACK_BARS    = int(os.getenv("TRADE_LOOKBACK_BARS", "300"))
SIGNAL_INTERVAL_S      = float(os.getenv("SIGNAL_INTERVAL_S", "30"))

QUANTUM_ENABLED        = os.getenv("QUANTUM_ENABLED", "0").lower() not in ("0", "false", "")
QUANTUM_WEIGHT         = float(os.getenv("QUANTUM_WEIGHT", "0.35"))
EMA_WEIGHT             = float(os.getenv("EMA_WEIGHT", "0.65"))
WATCHLIST_ENV          = os.getenv("TRADE_SYMBOLS", "").strip()
WATCHLIST              = [s.strip() for s in WATCHLIST_ENV.split(",") if s.strip()]

# Execution / risk
TRADE_ENABLED          = os.getenv("TRADE_ENABLED", "0").lower() not in ("0", "false", "")
TRADE_MIN_CONF         = float(os.getenv("TRADE_MIN_CONF", "0.55"))           # require this confidence to act
TRADE_QUOTE_PER_ORDER  = float(os.getenv("TRADE_QUOTE_PER_ORDER", "100"))     # spend per BUY (in PRIMARY_QUOTE)
MAX_SPEND_PER_SYMBOL   = float(os.getenv("MAX_SPEND_PER_SYMBOL", "1000"))     # cap total notional per symbol
MAX_OPEN_POSITIONS     = int(os.getenv("MAX_OPEN_POSITIONS", "10"))           # across all symbols
SELL_FRACTION          = float(os.getenv("SELL_FRACTION", "1.0"))             # fraction to sell on SELL signal (1.0 = all)
EXECUTION_INTERVAL_S   = float(os.getenv("EXECUTION_INTERVAL_S", "20"))       # execution loop pace

# ---------------------------------------------------------------------------------------
# App + CORS
# ---------------------------------------------------------------------------------------
log = logging.getLogger("BottieAPI")
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")

app = FastAPI(title="Bottie API", version="1.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[NETLIFY_URL] if NETLIFY_URL != "*" else ["*"],
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------------------
# In-memory state
# ---------------------------------------------------------------------------------------
_started = time.time()
_equity_series: List[Dict[str, Any]] = []                  # [{"t": ts, "v": float}]
_positions: Dict[str, Dict[str, float]] = {}               # {"SYM/QUOTE": {"qty":..., "avg_px":..., "last_px":...}}
_signals: List[Dict[str, Any]] = []                        # [{"symbol":..., "signal":..., "confidence":..., "t":...}]
_orders: List[Dict[str, Any]] = []                         # basic order log
_logs: List[str] = []                                      # recent log lines
_cost_basis_cache: Dict[str, Dict[str, float]] = {}        # symbol -> {"ts":..., "qty":..., "avg_px":...}
_trade_enabled_flag: bool = bool(TRADE_ENABLED)            # runtime kill-switch (toggle via endpoints)

def add_log(msg: str):
    msg = msg.strip()
    _logs.append(msg)
    if len(_logs) > 1000:
        del _logs[:-1000]
    log.info(msg)

def _push_order(rec: Dict[str, Any]):
    _orders.append(rec)
    if len(_orders) > 500:
        del _orders[:-300]

def _get_positions_copy() -> Dict[str, Dict[str, float]]:
    return dict(_positions)

def _push_signal(sig: Dict[str, Any]):
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

# ---------------------------------------------------------------------------------------
# Optional quantum detection info (for /health cosmetics)
# ---------------------------------------------------------------------------------------
def _detect_quantum() -> Dict[str, str]:
    if not QUANTUM_ENABLED:
        return {"kind": "disabled", "backend": "n/a"}
    if _HAS_QISKIT:
        return {"kind": "qiskit", "backend": os.getenv("QUANTUM_BACKEND", "aer_simulator")}
    return {"kind": "unavailable", "backend": "none"}

# ---------------------------------------------------------------------------------------
# Exchange (LIVE spot)
# ---------------------------------------------------------------------------------------
_exchange: Optional[ccxt.Exchange] = None

def _init_exchange() -> ccxt.Exchange:
    if not API_KEY or not API_SECRET:
        raise RuntimeError("API_KEY / API_SECRET missing.")
    if EXCHANGE_ID != "binance":
        raise RuntimeError("This deployment is locked to Binance spot.")

    klass = getattr(ccxt, EXCHANGE_ID)
    params = {"apiKey": API_KEY, "secret": API_SECRET, "enableRateLimit": True}
    ex = klass(params)
    # Force spot
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

# ---------------------------------------------------------------------------------------
# Helpers (balances, symbols, tickers)
# ---------------------------------------------------------------------------------------
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
    seen, pr = set(), []
    for q in ordered:
        if q not in seen:
            seen.add(q)
            pr.append(q)
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

# ---------------------------------------------------------------------------------------
# Cost-basis (true avg entry) via WAC
# ---------------------------------------------------------------------------------------
def _ms_since(days: int) -> int:
    return int((time.time() - days * 86400) * 1000)

def _compute_cost_basis_for_symbol(symbol: str) -> Optional[Tuple[float, float]]:
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
    base_ccy, quote_ccy = symbol.split("/")[0].upper(), symbol.split("/")[1].upper()

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
            if fee_ccy == quote_ccy:
                eff_cost_add = fee_cost
            elif fee_ccy == base_ccy:
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

# ---------------------------------------------------------------------------------------
# Portfolio valuation loop
# ---------------------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------------------
# Signals (EMA + optional quantum toy scorer)
# ---------------------------------------------------------------------------------------
def _ema(series: List[float], period: int) -> List[float]:
    if not series or period <= 1:
        return series[:]
    k = 2.0 / (period + 1.0)
    out: List[float] = []
    ema_val = series[0]
    for x in series:
        ema_val = x * k + ema_val * (1 - k)
        out.append(ema_val)
    return out

def _pct_change(series: List[float], n: int) -> float:
    if len(series) < n + 1:
        return 0.0
    a, b = series[-1], series[-1 - n]
    return 0.0 if b == 0 else (a - b) / b

def _quantum_feature_vector(closes: List[float]) -> List[float]:
    mom1 = _pct_change(closes, 3)
    mom2 = _pct_change(closes, 8)
    mom3 = _pct_change(closes, 21)
    volw = 0.0
    if len(closes) > 21:
        window = closes[-21:]
        mean = sum(window) / len(window)
        var = sum((x - mean) ** 2 for x in window) / max(1, len(window) - 1)
        volw = math.sqrt(var) / mean if mean else 0.0
    vec = [mom1, mom2, mom3, volw]
    out: List[float] = []
    for v in vec:
        v = max(min(v, 0.1), -0.1)
        out.append(v / 0.1)  # [-1,1]
    return out

def _quantum_score(features: List[float]) -> float:
    if not QUANTUM_ENABLED or not _HAS_QISKIT:
        return 0.0
    try:
        from qiskit import QuantumCircuit
        from qiskit_aer import Aer
        from qiskit.transpiler import PassManager

        qc = QuantumCircuit(2)
        a, b, c, d = (features + [0, 0, 0, 0])[:4]
        qc.ry((a + 1) * math.pi / 2, 0)
        qc.ry((b + 1) * math.pi / 2, 1)
        qc.cx(0, 1)
        qc.rz((c + 1) * math.pi / 2, 0)
        qc.rz((d + 1) * math.pi / 2, 1)
        qc.cx(1, 0)
        qc.barrier()
        qc.measure_all()

        backend = Aer.get_backend("aer_simulator")
        tqc = PassManager().run(qc)
        res = backend.run(tqc, shots=512).result()
        counts = res.get_counts()
        shots = sum(counts.values())
        p1 = sum(cnt for bitstr, cnt in counts.items() if bitstr.endswith("1"))
        prob = (p1 / shots) if shots else 0.5
        return 2.0 * (prob - 0.5)
    except Exception:
        return 0.0

def _blend_scores(ema_score: float, q_score: float) -> float:
    wq = max(0.0, min(1.0, QUANTUM_WEIGHT))
    we = max(0.0, min(1.0, EMA_WEIGHT))
    if (wq + we) <= 0:
        wq, we = 0.35, 0.65
    total = wq + we
    return (wq * q_score + we * ema_score) / total

async def signals_loop():
    await _ensure_exchange()
    assert _exchange is not None
    min_bars_ok = max(TRADE_SLOW_EMA * 2, 100)
    add_log(
        f"Signal loop started | TF={TRADE_TIMEFRAME} | FAST={TRADE_FAST_EMA} | "
        f"SLOW={TRADE_SLOW_EMA} | Q={QUANTUM_ENABLED}"
    )
    while True:
        try:
            uni = set(WATCHLIST)
            for sym in _get_positions_copy().keys():
                uni.add(sym)
            uni = [s for s in uni if s]

            for symbol in uni:
                try:
                    ohlcv = _exchange.fetch_ohlcv(symbol, timeframe=TRADE_TIMEFRAME,
                                                  limit=max(TRADE_LOOKBACK_BARS, min_bars_ok))
                except Exception as e:
                    add_log(f"fetch_ohlcv fail {symbol}: {e}")
                    continue
                if not ohlcv or len(ohlcv) < min_bars_ok:
                    continue

                closes = [float(x[4]) for x in ohlcv]
                fema = _ema(closes, TRADE_FAST_EMA)
                sema = _ema(closes, TRADE_SLOW_EMA)
                fval = fema[-1]; sval = sema[-1]

                spread = (fval - sval) / sval if sval else 0.0
                spread = max(min(spread, 0.02), -0.02)
                ema_score = spread / 0.02

                q_score = _quantum_score(_quantum_feature_vector(closes))
                final = _blend_scores(ema_score, q_score)

                if final > 0.25:
                    sig = "BUY"
                elif final < -0.25:
                    sig = "SELL"
                else:
                    sig = "HOLD"

                conf = min(0.99, max(0.0, abs(final)))
                _push_signal({
                    "symbol": symbol,
                    "signal": sig,
                    "confidence": conf,
                    "ema_score": round(ema_score, 4),
                    "q_score": round(q_score, 4),
                    "final": round(final, 4),
                    "t": int(time.time()),
                })

            add_log(f"signals | n={len(uni)} scanned")
        except Exception as e:
            add_log(f"ERROR signal loop: {e}")

        await asyncio.sleep(SIGNAL_INTERVAL_S)

# ---------------------------------------------------------------------------------------
# Execution helpers (Binance constraints)
# ---------------------------------------------------------------------------------------
def _round_step(value: float, step: Optional[float], precision: Optional[int]) -> float:
    if step and step > 0:
        return math.floor(value / step) * step
    if precision is not None:
        p = max(0, int(precision))
        return float(f"{value:.{p}f}")
    return value

def _binance_amount_limit(symbol: str) -> Tuple[Optional[float], Optional[float], Optional[int]]:
    """Return (min_amount_step, min_amount, amount_precision_decimals)"""
    assert _exchange is not None
    m = _exchange.markets.get(symbol, {})
    step = None
    min_amt = None
    prec = None
    try:
        prec = m.get("precision", {}).get("amount")
    except Exception:
        prec = None
    try:
        min_amt = m.get("limits", {}).get("amount", {}).get("min")
    except Exception:
        min_amt = None
    try:
        # Try to read raw filters for finer control
        info = m.get("info", {})
        for f in info.get("filters", []):
            if f.get("filterType") == "LOT_SIZE":
                step = float(f.get("stepSize"))
                if "minQty" in f:
                    min_amt = max(float(f["minQty"]), float(min_amt or 0))
                break
    except Exception:
        step = step or None
    return step, min_amt, prec

def _binance_cost_min(symbol: str) -> Optional[float]:
    """Return min notional (quote) if known."""
    assert _exchange is not None
    m = _exchange.markets.get(symbol, {})
    try:
        # ccxt normalized
        cost_min = m.get("limits", {}).get("cost", {}).get("min")
        if cost_min:
            return float(cost_min)
        # raw filter fallback
        info = m.get("info", {})
        for f in info.get("filters", []):
            if f.get("filterType") in ("MIN_NOTIONAL", "NOTIONAL"):
                if "minNotional" in f:
                    return float(f["minNotional"])
                if "minNotional" in f.get("applyMinToMarket", {}):
                    return float(f["applyMinToMarket"]["minNotional"])
    except Exception:
        pass
    return None

def _latest_signal_for(symbol: str) -> Optional[Dict[str, Any]]:
    for s in reversed(_signals):
        if s.get("symbol") == symbol:
            return s
    return None

# ---------------------------------------------------------------------------------------
# Execution loop (market orders with guards)
# ---------------------------------------------------------------------------------------
async def execution_loop():
    await _ensure_exchange()
    assert _exchange is not None
    add_log("Execution loop started")

    while True:
        try:
            if not _trade_enabled_flag:
                await asyncio.sleep(EXECUTION_INTERVAL_S)
                continue

            # current valuation snapshot
            # (positions already refreshed by portfolio_loop)
            open_syms = [sym for sym, pos in _positions.items() if pos.get("qty", 0.0) > 0]
            if len(open_syms) >= MAX_OPEN_POSITIONS:
                add_log("execution: max open positions reached; skipping buys")
                # Selling still allowed

            # consider universe = held symbols + watchlist
            uni = set(WATCHLIST)
            uni.update(_positions.keys())

            for symbol in list(uni):
                sig = _latest_signal_for(symbol)
                if not sig:
                    continue
                side = sig["signal"]
                conf = float(sig.get("confidence", 0.0))
                if conf < TRADE_MIN_CONF:
                    continue

                # need price & market info
                ticker = _exchange.fetch_ticker(symbol) or {}
                price = float(ticker.get("last") or ticker.get("close") or 0.0)
                if price <= 0:
                    continue

                # compute current notional exposure on this symbol
                pos = _positions.get(symbol, {})
                cur_qty = float(pos.get("qty", 0.0))
                cur_value = cur_qty * price

                cost_min = _binance_cost_min(symbol) or 0.0
                step, min_amt, prec = _binance_amount_limit(symbol)

                # BUY logic
                if side == "BUY":
                    if len(open_syms) >= MAX_OPEN_POSITIONS and cur_qty <= 0:
                        continue  # can't open new
                    # respect per-symbol cap
                    remaining_cap = max(0.0, MAX_SPEND_PER_SYMBOL - cur_value)
                    budget_quote = min(TRADE_QUOTE_PER_ORDER, remaining_cap)
                    # also respect free quote balance
                    try:
                        bal = _exchange.fetch_balance() or {}
                        free_quote = float((bal.get("free") or {}).get(PRIMARY_QUOTE, 0.0))
                        budget_quote = min(budget_quote, free_quote)
                    except Exception:
                        pass

                    if budget_quote <= 0.0:
                        continue
                    if cost_min and budget_quote < cost_min:
                        # if budget below min notional, try to bump up to min if we have free quote
                        try:
                            bal = _exchange.fetch_balance() or {}
                            free_quote = float((bal.get("free") or {}).get(PRIMARY_QUOTE, 0.0))
                        except Exception:
                            free_quote = 0.0
                        if free_quote >= cost_min:
                            budget_quote = cost_min
                        else:
                            continue

                    amount = budget_quote / price
                    # apply amount constraints
                    amount = _round_step(amount, step, prec)
                    if min_amt and amount < min_amt:
                        # try snap to min
                        amount = min_amt
                    if amount <= 0:
                        continue

                    # place market buy
                    try:
                        order = _exchange.create_order(symbol, "market", "buy", amount)
                        _push_order({
                            "symbol": symbol, "side": "buy", "amount": amount, "px": price,
                            "t": int(time.time()), "order": order
                        })
                        add_log(f"BUY {symbol} amount={amount} ~{budget_quote:.2f} {PRIMARY_QUOTE}")
                        if symbol not in open_syms:
                            open_syms.append(symbol)
                    except Exception as e:
                        add_log(f"ORDER BUY FAIL {symbol}: {e}")

                # SELL logic
                elif side == "SELL":
                    if cur_qty <= 0:
                        continue
                    sell_amt = max(0.0, min(cur_qty, cur_qty * SELL_FRACTION))
                    sell_amt = _round_step(sell_amt, step, prec)
                    if min_amt and sell_amt < min_amt:
                        # if position is smaller than min, try to close all if allowed
                        if cur_qty >= min_amt:
                            sell_amt = cur_qty  # dump all
                        else:
                            continue
                    if sell_amt <= 0:
                        continue
                    try:
                        order = _exchange.create_order(symbol, "market", "sell", sell_amt)
                        _push_order({
                            "symbol": symbol, "side": "sell", "amount": sell_amt, "px": price,
                            "t": int(time.time()), "order": order
                        })
                        add_log(f"SELL {symbol} amount={sell_amt} ~{sell_amt*price:.2f} {PRIMARY_QUOTE}")
                        if sell_amt >= cur_qty and symbol in open_syms:
                            open_syms.remove(symbol)
                    except Exception as e:
                        add_log(f"ORDER SELL FAIL {symbol}: {e}")

                # HOLD → no action

        except Exception as e:
            add_log(f"ERROR execution loop: {e}")

        await asyncio.sleep(EXECUTION_INTERVAL_S)

# ---------------------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------------------
@app.on_event("startup")
async def _on_startup():
    asyncio.create_task(portfolio_loop())
    if TRADE_SIGNALS_ENABLED:
        asyncio.create_task(signals_loop())
    if _trade_enabled_flag:
        asyncio.create_task(execution_loop())

# ---------------------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------------------
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
        "trading": {"enabled": _trade_enabled_flag},
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
        "orders_count": len(_orders),
    }

@app.get("/signals")
def signals():
    latest: Dict[str, Dict[str, Any]] = {}
    for s in _signals:
        sym = s.get("symbol")
        if not sym:
            continue
        if sym not in latest or s.get("t", 0) >= latest[sym].get("t", 0):
            latest[sym] = s
    return {"signals": list(latest.values())}

@app.get("/orders")
def orders():
    return {"orders": _orders[-200:]}

@app.get("/logs/last")
def logs_last():
    return {"logs": _logs[-300:]}

@app.get("/costbasis")
def costbasis():
    out: Dict[str, Any] = {}
    for sym, entry in _cost_basis_cache.items():
        out[sym] = {
            "qty": entry["qty"],
            "avg_px": entry["avg_px"],
            "age_sec": round(time.time() - entry["ts"], 1),
        }
    return out

# Kill-switch controls
@app.get("/trade/status")
def trade_status():
    return {"enabled": _trade_enabled_flag}

@app.get("/trade/enable")
def trade_enable():
    global _trade_enabled_flag
    _trade_enabled_flag = True
    # start loop if not already running (best-effort)
    asyncio.create_task(execution_loop())
    return {"enabled": True}

@app.get("/trade/disable")
def trade_disable():
    global _trade_enabled_flag
    _trade_enabled_flag = False
    return {"enabled": False}