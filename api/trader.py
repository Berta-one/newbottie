# api/trader.py
import os, time, math, asyncio
from typing import Dict, Any, List, Optional, Tuple

# This module expects: a live ccxt exchange passed in (already authenticated)
# and callable helpers to access/update shared state in app.py

try:
    import qiskit  # type: ignore
    _HAS_Q = True
except Exception:
    _HAS_Q = False

# -----------------------
# Env toggles
# -----------------------
TF            = os.getenv("TRADE_TIMEFRAME", "1h")
FAST_EMA      = int(os.getenv("TRADE_FAST_EMA", "12"))
SLOW_EMA      = int(os.getenv("TRADE_SLOW_EMA", "26"))
LOOKBACK      = int(os.getenv("TRADE_LOOKBACK_BARS", "300"))
WATCHLIST_ENV = os.getenv("TRADE_SYMBOLS", "").strip()
WATCHLIST     = [s.strip() for s in WATCHLIST_ENV.split(",") if s.strip()]
QUANTUM_ON    = os.getenv("QUANTUM_ENABLED", "0") not in ("0", "false", "False", "", None)
QUANTUM_WEIGHT= float(os.getenv("QUANTUM_WEIGHT", "0.35"))  # blend weight for quantum score
EMA_WEIGHT    = float(os.getenv("EMA_WEIGHT", "0.65"))

MIN_BARS_OK   = max(SLOW_EMA * 2, 100)

# -----------------------
# Simple TA helpers
# -----------------------
def ema(series: List[float], period: int) -> List[float]:
    if not series or period <= 1:
        return series[:]
    k = 2.0 / (period + 1.0)
    out = []
    ema_val = series[0]
    for x in series:
        ema_val = x * k + ema_val * (1 - k)
        out.append(ema_val)
    return out

def pct_change(series: List[float], n: int) -> float:
    if len(series) < n + 1:
        return 0.0
    a, b = series[-1], series[-1 - n]
    if b == 0:
        return 0.0
    return (a - b) / b

def atr_from_ohlcv(ohlcv: List[List[float]], period: int = 14) -> float:
    # ohlcv: [ts, open, high, low, close, vol]
    if len(ohlcv) < period + 1:
        return 0.0
    trs = []
    for i in range(1, len(ohlcv)):
        h = float(ohlcv[i][2]); l = float(ohlcv[i][3]); c_prev = float(ohlcv[i-1][4])
        tr = max(h - l, abs(h - c_prev), abs(l - c_prev))
        trs.append(tr)
    # simple EMA of TRs
    tr_ema = ema(trs, period)
    return tr_ema[-1] if tr_ema else 0.0

# -----------------------
# Quantum-ish lightweight scorer (optional)
# -----------------------
def _quantum_feature_vector(closes: List[float]) -> List[float]:
    # tiny 4-dim: recent momentum & volatility proxies
    mom1 = pct_change(closes, 3)
    mom2 = pct_change(closes, 8)
    mom3 = pct_change(closes, 21)
    volw = 0.0
    if len(closes) > 21:
        window = closes[-21:]
        mean = sum(window) / len(window)
        var = sum((x - mean) ** 2 for x in window) / max(1, len(window) - 1)
        volw = math.sqrt(var) / mean if mean else 0.0
    # clamp and scale to [-1,1]
    vec = [mom1, mom2, mom3, volw]
    out = []
    for v in vec:
        v = max(min(v, 0.1), -0.1)  # cap extremes
        out.append(v / 0.1)
    return out

def _quantum_score(features: List[float]) -> float:
    """
    Returns a score in [-1, 1]. If Qiskit unavailable or error, returns 0 (neutral).
    This uses a tiny simulated circuit to map features → probability; lightweight by design.
    """
    if not QUANTUM_ON or not _HAS_Q:
        return 0.0
    try:
        from qiskit import QuantumCircuit
        from qiskit_aer import Aer
        from qiskit.transpiler import PassManager
        # 2-qubit toy ansatz: encode features as rotation angles
        qc = QuantumCircuit(2)
        a, b, c, d = features if len(features) >= 4 else (0, 0, 0, 0)
        qc.ry((a + 1) * math.pi/2, 0)
        qc.ry((b + 1) * math.pi/2, 1)
        qc.cx(0, 1)
        qc.rz((c + 1) * math.pi/2, 0)
        qc.rz((d + 1) * math.pi/2, 1)
        qc.cx(1, 0)
        qc.barrier()
        qc.measure_all()

        backend = Aer.get_backend("aer_simulator")
        tqc = PassManager().run(qc)
        res = backend.run(tqc, shots=512).result()
        counts = res.get_counts()
        p1 = 0.0
        shots = 0
        for bitstr, cnt in counts.items():
            shots += cnt
            if bitstr.endswith("1"):  # look at least significant bit
                p1 += cnt
        prob = (p1 / shots) if shots else 0.5
        # map [0,1] → [-1,1]
        return 2.0 * (prob - 0.5)
    except Exception:
        return 0.0

# -----------------------
# Signal engine
# -----------------------
class SignalEngine:
    """
    Pulls OHLCV, computes EMA crossover + quantum score, blends into final signal.
    """
    def __init__(self, exchange, get_positions_fn, push_signal_fn, log_fn):
        self.ex = exchange
        self.get_positions = get_positions_fn
        self.push_signal = push_signal_fn
        self.log = log_fn

    def _pick_universe(self) -> List[str]:
        uni = set(WATCHLIST)
        # include anything we currently hold
        for sym in self.get_positions().keys():
            uni.add(sym)
        return [s for s in uni if s]

    def _blend(self, ema_score: float, q_score: float) -> float:
        wq = max(0.0, min(1.0, QUANTUM_WEIGHT))
        we = max(0.0, min(1.0, EMA_WEIGHT))
        # normalize weights
        if (wq + we) == 0:
            wq = 0.35; we = 0.65
        total = wq + we
        return (wq * q_score + we * ema_score) / total

    def score_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        try:
            ohlcv = self.ex.fetch_ohlcv(symbol, timeframe=TF, limit=max(LOOKBACK, MIN_BARS_OK))
        except Exception as e:
            self.log(f"fetch_ohlcv fail {symbol}: {e}")
            return None
        if not ohlcv or len(ohlcv) < MIN_BARS_OK:
            return None

        closes = [float(x[4]) for x in ohlcv]
        fema = ema(closes, FAST_EMA)
        sema = ema(closes, SLOW_EMA)
        fval = fema[-1]; sval = sema[-1]

        # EMA crossover score in [-1,1]
        # positive when fast > slow; magnitude scales with spread
        spread = (fval - sval) / sval if sval else 0.0
        spread = max(min(spread, 0.02), -0.02)  # clip 2%
        ema_score = spread / 0.02  # map [-0.02,0.02] → [-1,1]

        q_score = _quantum_score(_quantum_feature_vector(closes)) if QUANTUM_ON else 0.0
        final = self._blend(ema_score, q_score)

        # Discrete signal
        if final > 0.25:
            sig = "BUY"
        elif final < -0.25:
            sig = "SELL"
        else:
            sig = "HOLD"

        conf = min(0.99, max(0.0, abs(final)))  # confidence 0..0.99
        return {
            "symbol": symbol,
            "signal": sig,
            "confidence": conf,
            "ema_score": round(ema_score, 4),
            "q_score": round(q_score, 4),
            "final": round(final, 4),
            "t": int(time.time()),
        }

    async def run(self, interval_s: float = 30.0):
        self.log(f"Signal engine started | TF={TF} | FAST={FAST_EMA} | SLOW={SLOW_EMA} | Q={QUANTUM_ON}")
        while True:
            try:
                uni = self._pick_universe()
                if not uni:
                    await asyncio.sleep(interval_s)
                    continue
                batch: List[Dict[str, Any]] = []
                for sym in uni:
                    r = self.score_symbol(sym)
                    if r:
                        batch.append(r)
                # push newest per symbol
                # you can also filter to top-N by confidence here
                for r in batch:
                    self.push_signal(r)
                self.log(f"signals | n={len(batch)} universe={len(uni)}")
            except Exception as e:
                self.log(f"ERROR signal loop: {e}")
            await asyncio.sleep(interval_s)