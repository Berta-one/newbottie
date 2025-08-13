# api/cross_pairs.py
import os, time, math, asyncio, logging, random
from typing import Dict, List, Any, Optional, Tuple, Set
from collections import defaultdict
import numpy as np
import ccxt.pro as ccxtpro

log = logging.getLogger("CrossPairsWS")

PRIMARY_QUOTE = os.getenv("PRIMARY_QUOTE", "USDT").upper()
EXCHANGE_ID = os.getenv("EXCHANGE_ID", "binance").lower()
MAX_COLS = int(os.getenv("GRID_MAX_COLS", "80"))
STABLES = [s.strip().upper() for s in os.getenv("GRID_STABLES", "USDT,USDC,BUSD,DAI").split(",") if s.strip()]
SCAN_FILTER = os.getenv("TRADE_SYMBOLS", "")

# Dynamic trade thresholds (more flexible than a single min-conf)
TRADE_CONF_FLOOR = float(os.getenv("TRADE_CONF_FLOOR", "0.50")) # lower bound (≤ SELL)
TRADE_CONF_CEIL = float(os.getenv("TRADE_CONF_CEIL", "0.80")) # upper bound (≥ BUY)

EMA_WEIGHT = float(os.getenv("EMA_WEIGHT", "0.40"))
ML_WEIGHT = float(os.getenv("ML_WEIGHT", "0.30"))
QUANTUM_WEIGHT = float(os.getenv("QUANTUM_WEIGHT", "0.20"))
SENTIMENT_WEIGHT = float(os.getenv("SENTIMENT_WEIGHT", "0.10"))

ENABLE_GRID_WS = os.getenv("ENABLE_GRID_WS", "1").lower() in ("1","true","yes")

def _truthy(x: str) -> bool:
    return str(x).lower() in ("1","true","yes","on")

class CrossPairsWS:
    """
    Maintains:
      rows = assets you hold (balances>0) + stables
      cols = scan universe (bounded)
      symbols = resolved tradable symbols intersecting rows × cols
      tickers = streaming last prices via WS
      matrix = computed signals per (base, quote)
    """
    def __init__(self, api_key: str = "", api_secret: str = "", testnet: bool = False):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.ex: Optional[ccxtpro.binance] = None

        self.rows: List[str] = []
        self.cols: List[str] = []
        self.symbols: List[str] = []
        self.market_map: Dict[str, Any] = {}
        self.tickers: Dict[str, Dict[str, Any]] = {}

        # matrix[base][quote] = {...signal parts...}
        self.matrix: Dict[str, Dict[str, Dict[str, Any]]] = defaultdict(dict)

        self._stop = False
        self._max_batch = 50
        self._last_rows_cols_ts = 0
        self._rows_cols_ttl = 180 # refresh rows/cols every 3 min to reflect balances

        # scoring hook provided by app
        self.score_fn = None # def score_fn(symbol:str, price:float)->Dict[str,float]

    async def start(self):
        if not ENABLE_GRID_WS:
            log.warning("[WS] Grid WS disabled by ENABLE_GRID_WS=0")
            return

        self.ex = ccxtpro.binance({
            "apiKey": self.api_key,
            "secret": self.api_secret,
            "enableRateLimit": True,
            "options": {"defaultType": "spot"},
        })
        await self.ex.load_markets()
        self.market_map = self.ex.markets
        log.info(f"[WS] Loaded {len(self.market_map)} markets")

        await self._refresh_rows_and_cols(force=True)
        await self._resolve_symbols()

        asyncio.create_task(self._ws_cycle())
        asyncio.create_task(self._periodic_rescan())

    async def stop(self):
        self._stop = True
        if self.ex:
            try:
                await self.ex.close()
            except Exception:
                pass

    async def _periodic_rescan(self):
        # periodically refresh rows/cols and potential symbols set
        while not self._stop:
            try:
                await asyncio.sleep(60)
                await self._refresh_rows_and_cols()
                await self._resolve_symbols()
            except Exception as e:
                log.debug(f"[WS] periodic rescan err: {e}")

    async def _refresh_rows_and_cols(self, force=False):
        now = time.time()
        if not force and (now - self._last_rows_cols_ts) < self._rows_cols_ttl:
            return
        self._last_rows_cols_ts = now

        # refresh balances via REST
        rows: Set[str] = set()
        try:
            bal = await self.ex.fetch_balance()
            for asset, qty in (bal.get("total") or {}).items():
                try:
                    if float(qty) > 0:
                        rows.add(asset.upper())
                except Exception:
                    pass
        except Exception as e:
            log.warning(f"[WS] fetch_balance failed: {e}")

        rows.update(STABLES)
        self.rows = sorted(rows)

        # columns: from whitelist or from markets
        if SCAN_FILTER.strip():
            cols_set = set()
            for sym in [s.strip().upper() for s in SCAN_FILTER.split(",") if s.strip()]:
                try:
                    base, quote = sym.split("/")
                    cols_set.add(base); cols_set.add(quote)
                except Exception:
                    pass
            self.cols = sorted(list(cols_set))[:MAX_COLS]
        else:
            bases, quotes = set(), set()
            for m in self.market_map.values():
                if m.get("spot", True) and m.get("active", True):
                    bases.add(m["base"].upper()); quotes.add(m["quote"].upper())
            common = [PRIMARY_QUOTE] + [x for x in (bases | quotes) if x != PRIMARY_QUOTE]
            self.cols = common[:MAX_COLS]

        log.info(f"[WS] rows={len(self.rows)} cols={len(self.cols)}")

    async def _resolve_symbols(self):
        found = set()
        for base in self.rows:
            for quote in self.cols:
                if base == quote:
                    continue
                s1, s2 = f"{base}/{quote}", f"{quote}/{base}"
                if s1 in self.market_map and self.market_map[s1].get("active", True):
                    found.add(s1)
                elif s2 in self.market_map and self.market_map[s2].get("active", True):
                    found.add(s2)
        self.symbols = sorted(found)
        log.info(f"[WS] resolved {len(self.symbols)} symbols for maxi-grid")

    async def _ws_cycle(self):
        if not self.symbols:
            log.warning("[WS] no symbols to watch")
            return

        # batching to avoid throttling
        batches = [self.symbols[i:i+self._max_batch] for i in range(0, len(self.symbols), self._max_batch)]
        backoff = 1.0

        while not self._stop:
            try:
                for batch in batches:
                    if self._stop: break
                    # watch a batch; tolerate individual failures
                    results = await asyncio.gather(
                        *[self.ex.watch_ticker(sym) for sym in batch],
                        return_exceptions=True
                    )
                    now = int(time.time())
                    for sym, res in zip(batch, results):
                        if isinstance(res, Exception):
                            # swallow & continue
                            continue
                        if not res: # empty
                            continue
                        self.tickers[sym] = res
                        self._update_matrix_from_ticker(sym, res, now)

                backoff = 1.0 # success resets backoff
            except Exception as e:
                log.warning(f"[WS] cycle error: {e} (reconnecting)")
                await asyncio.sleep(backoff + random.random()*0.3)
                backoff = min(backoff * 2, 20.0)
                # try to reopen the connection
                try:
                    await self.ex.close()
                except Exception:
                    pass
                try:
                    self.ex = ccxtpro.binance({
                        "apiKey": self.api_key,
                        "secret": self.api_secret,
                        "enableRateLimit": True,
                        "options": {"defaultType": "spot"},
                    })
                    await self.ex.load_markets()
                    self.market_map = self.ex.markets
                except Exception as e2:
                    log.error(f"[WS] reconnect failed: {e2}")

    def _blend_prob(self, parts: Dict[str, Optional[float]]) -> float:
        vals, wts = [], []
        for key, w in (("ema", EMA_WEIGHT), ("ml", ML_WEIGHT), ("q", QUANTUM_WEIGHT), ("sent", SENTIMENT_WEIGHT)):
            v = parts.get(key)
            if isinstance(v, (int, float)):
                vals.append(float(v)); wts.append(w)
        if not wts:
            return 0.5
        w = np.array(wts, dtype=float)
        w = w / max(1e-12, w.sum())
        return float((w * np.array(vals, dtype=float)).sum())

    def _update_matrix_from_ticker(self, symbol: str, tk: Dict[str, Any], now: int):
        last = float(tk.get("last") or tk.get("close") or 0.0)
        if last <= 0:
            return

        parts = {"ema": None, "ml": None, "q": None, "sent": None, "final_prob": None}
        if self.score_fn:
            try:
                got = self.score_fn(symbol, last) or {}
                parts.update(got)
            except Exception as e:
                log.debug(f"[WS] score_fn error {symbol}: {e}")

        fp = parts.get("final_prob")
        if fp is None:
            fp = self._blend_prob(parts)

        # dynamic thresholds: SELL ≤ floor, BUY ≥ ceil
        thr_sell = float(TRADE_CONF_FLOOR)
        thr_buy = float(TRADE_CONF_CEIL)
        if fp >= thr_buy:
            signal, conf = "BUY", fp
        elif fp <= thr_sell:
            signal, conf = "SELL", 1.0 - fp
        else:
            signal, conf = "HOLD", abs(fp - 0.5) * 2.0

        try:
            base, quote = symbol.split("/")
        except Exception:
            return

        self.matrix[base][quote] = {
            "symbol": symbol,
            "signal": signal,
            "conf": float(conf),
            "ema": parts.get("ema"),
            "ml": parts.get("ml"),
            "q": parts.get("q"),
            "sent": parts.get("sent"),
            "final_prob": float(fp),
            "thr_buy": float(thr_buy),
            "thr_sell": float(thr_sell),
            "last": float(last),
            "t": int(now),
        }

    def snapshot_matrix(self) -> Dict[str, Any]:
        return {
            "rows": self.rows,
            "cols": self.cols,
            "ts": int(time.time()),
            "matrix": self.matrix,
        }

    # Legacy compatibility methods
    def get_portfolio_assets(self) -> List[str]:
        """Returns assets with balances > 0"""
        return self.rows.copy()

    def get_scan_assets(self) -> List[str]:
        """Returns scan universe assets"""
        return self.cols.copy()

    def get_matrix_data(self) -> Dict[str, Any]:
        """Returns full matrix snapshot"""
        return self.snapshot_matrix()
