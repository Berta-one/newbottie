import os
import time
import logging
from typing import Dict, List, Any, Tuple
import threading

import requests
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# ───────────────────────────────────────────────────────────────────
# ENV / CONFIG
# ───────────────────────────────────────────────────────────────────
# Support both names (some dashboards prefer FINNHUB_KEY)
FINNHUB_API_KEY = (os.getenv("FINNHUB_API_KEY") or os.getenv("FINNHUB_KEY") or "").strip()

SENTIMENT_ENABLED   = os.getenv("SENTIMENT_ENABLED", "1").lower() in ("1", "true", "yes")
SENTIMENT_SOURCE    = os.getenv("SENTIMENT_SOURCE", "finnhub").lower()  # currently only "finnhub"
SENTIMENT_WINDOW_S  = int(os.getenv("SENTIMENT_WINDOW_S", "900"))       # 15 min window
SENTIMENT_POLL_S    = int(os.getenv("SENTIMENT_POLL_S", "60"))          # pull cadence
SENTIMENT_TOP_N     = int(os.getenv("SENTIMENT_TOP_N", "50"))           # cap per-cycle scoring
# Assets we track and their keywords
SENTIMENT_ASSETS = [a.strip().upper() for a in os.getenv(
    "SENTIMENT_ASSETS",
    "BTC,ETH,BNB,ADA,XRP,SOL"
).split(",") if a.strip()]

# Additional keywords can be provided; comma-separated list per asset via ENV:
# e.g. SENTIMENT_KW_BTC="bitcoin,btc,btc-usdt"
def _env_keywords_for(base: str) -> List[str]:
    v = os.getenv(f"SENTIMENT_KW_{base.upper()}", "")
    extra = [x.strip() for x in v.split(",") if x.strip()]
    # Always include the base itself
    return list({base.upper(), base.lower(), base.capitalize(), *extra})

# ───────────────────────────────────────────────────────────────────
# LOGGING
# ───────────────────────────────────────────────────────────────────
log = logging.getLogger("SentimentService")

if not FINNHUB_API_KEY and SENTIMENT_ENABLED:
    log.warning("⚠ FINNHUB_API_KEY / FINNHUB_KEY is missing; sentiment fetch will return neutral scores.")

# ───────────────────────────────────────────────────────────────────
# RUNTIME STATE
# ───────────────────────────────────────────────────────────────────
_analyzer = SentimentIntensityAnalyzer()

# Rolling store: { BASE: [(timestamp, compound), ...] } (comp ∈ [-1,1])
_store: Dict[str, List[Tuple[float, float]]] = {a: [] for a in SENTIMENT_ASSETS}

# Pull throttling and incremental fetch
_last_pull_ts: float = 0.0
_last_seen_time: float = 0.0  # Finnhub timestamps are UNIX seconds
_lock = threading.Lock()

# ───────────────────────────────────────────────────────────────────
# HELPERS
# ───────────────────────────────────────────────────────────────────
def _clip(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x

def _to_prob(vader_compound: float) -> float:
    # Map VADER compound [-1,1] → [0,1]
    return _clip(0.5 + 0.5 * float(vader_compound), 0.0, 1.0)

def _trim_window(now: float):
    cutoff = now - SENTIMENT_WINDOW_S
    for base, arr in _store.items():
        if not arr:
            continue
        # Find first index >= cutoff
        k = 0
        for k in range(len(arr)):
            if arr[k][0] >= cutoff:
                break
        _store[base] = arr[k:] if arr and k < len(arr) else []

def _token() -> str:
    return FINNHUB_API_KEY

def _fetch_finnhub_crypto_news() -> List[Dict[str, Any]]:
    """
    Finnhub: GET /news?category=crypto&token=KEY
    Returns list of news dicts. Each item may include fields: headline, summary, datetime (sec), source, url
    Docs: https://finnhub.io/docs/api/market-news
    """
    key = _token()
    if not key:
        return []
    try:
        resp = requests.get(
            "https://finnhub.io/api/v1/news",
            params={"category": "crypto", "token": key},
            timeout=15,
        )
        # Raise for HTTP errors to catch 401/429/etc.
        resp.raise_for_status()
        data = resp.json()
        # Ensure list
        if isinstance(data, dict):
            # Sometimes returns {"error": "..."}
            log.warning("Finnhub returned an object instead of list: %s", data)
            return []
        if not isinstance(data, list):
            return []
        return data
    except requests.HTTPError as e:
        # Avoid formatting dict directly with % specifiers; convert to string safely
        try:
            msg = e.response.text[:300]
        except Exception:
            msg = str(e)
        log.error("Finnhub news HTTP error: %s", msg)
        return []
    except Exception as e:
        log.error("Finnhub news error: %s", e)
        return []

def _texts_by_asset_from_news(items: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    Partition news texts (headline + summary) into per-asset buckets via simple keyword match.
    """
    buckets: Dict[str, List[str]] = {a: [] for a in SENTIMENT_ASSETS}
    if not items:
        return buckets

    # Precompute keywords per asset
    keywords: Dict[str, List[str]] = {a: _env_keywords_for(a) for a in SENTIMENT_ASSETS}

    for it in items[: 5_000]:  # hard safety
        title = (it.get("headline") or it.get("title") or "")[:1000]
        summ  = (it.get("summary")  or "")[:3000]
        txt   = f"{title} {summ}".strip()
        if not txt:
            continue

        low = txt.lower()
        for base, kws in keywords.items():
            for kw in kws:
                if kw and kw.lower() in low:
                    buckets[base].append(txt)
                    break  # de-dup per asset (one hit is enough)

    return buckets

def _score_texts_into_store(texts_by_asset: Dict[str, List[str]], now: float):
    """
    Score texts with VADER and push (now, compound) into rolling store.
    """
    if not texts_by_asset:
        return
    for base, texts in texts_by_asset.items():
        if not texts:
            continue
        cap = min(SENTIMENT_TOP_N, len(texts))
        for t in texts[:cap]:
            try:
                vs = _analyzer.polarity_scores(str(t))
                comp = float(vs.get("compound", 0.0))
                _store.setdefault(base, []).append((now, comp))
            except Exception:
                # ignore single-text errors
                continue

# ───────────────────────────────────────────────────────────────────
# PUBLIC API (used by FastAPI app)
# ───────────────────────────────────────────────────────────────────
def run_sentiment_cycle() -> Dict[str, Dict[str, float]]:
    """
    Pull latest texts (debounced), score them, trim window, and return
    { BASE: {score:<avg in [-1,1]>, n:int} }.
    """
    if not SENTIMENT_ENABLED:
        # Return neutrals if disabled
        return {a: {"score": 0.0, "n": 0} for a in SENTIMENT_ASSETS}

    now = time.time()

    # Debounce pull to at most once per SENTIMENT_POLL_S
    should_pull = False
    with _lock:
        global _last_pull_ts
        if now - _last_pull_ts >= SENTIMENT_POLL_S:
            _last_pull_ts = now
            should_pull = True

    if should_pull and SENTIMENT_SOURCE == "finnhub":
        items = _fetch_finnhub_crypto_news()

        # Incremental filter by time (avoid re-scoring old items)
        global _last_seen_time
        fresh: List[Dict[str, Any]] = []
        for it in items:
            # Finnhub datetime is UNIX seconds; sometimes 'datetime' or 'time'
            ts = it.get("datetime") or it.get("time")
            try:
                tsf = float(ts) if ts is not None else 0.0
            except Exception:
                tsf = 0.0
            if tsf > _last_seen_time:
                fresh.append(it)

        if fresh:
            # Update marker to the newest we saw
            try:
                newest = max(float(it.get("datetime") or it.get("time") or 0.0) for it in fresh)
                if newest > _last_seen_time:
                    _last_seen_time = newest
            except Exception:
                pass

            texts_by_asset = _texts_by_asset_from_news(fresh)
            _score_texts_into_store(texts_by_asset, now)

    # Trim the rolling window and compute averages
    _trim_window(now)

    out: Dict[str, Dict[str, float]] = {}
    for a, arr in _store.items():
        if not arr:
            out[a] = {"score": 0.0, "n": 0}
            continue
        vals = [v for (_, v) in arr]
        avg = sum(vals) / max(1, len(vals))
        out[a] = {"score": float(avg), "n": int(len(vals))}
    return out

def latest_probs() -> Dict[str, float]:
    """
    Returns per-asset probabilities mapped from compound score to [0,1].
    """
    snap = run_sentiment_cycle()
    return {a: _to_prob(v["score"]) for a, v in snap.items()}

def snapshot() -> Dict[str, Any]:
    """
    Returns a structured snapshot for the API endpoint.
    """
    snap = run_sentiment_cycle()
    # Safe, simple summary line (avoid dict with printf-format)
    try:
        preview = ", ".join(f"{k}:{v['score']:+.2f}({v['n']})" for k, v in list(snap.items())[:6])
        if preview:
            log.info("sentiment snapshot | %s", preview)
    except Exception:
        # Never fail on logging
        pass
    return {"enabled": bool(SENTIMENT_ENABLED), "source": SENTIMENT_SOURCE, "window_sec": int(SENTIMENT_WINDOW_S), "scores": snap}