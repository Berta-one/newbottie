# sentiment/sentiment_service.py
"""
Sentiment service with:
- Finnhub news fetch (crypto category)
- VADER scoring
- Rolling window aggregation
- Optional persistent history (JSONL) via SENTIMENT_HISTORY_PATH
- Background poller with start/stop helpers
- API helpers: snapshot(), latest_probs(), aggregate_probs()
"""

from __future__ import annotations

import os
import time
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional

# ----------------------- Config -----------------------

LOG = logging.getLogger("SentimentService")

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "").strip()

SENTIMENT_ENABLED = os.getenv("SENTIMENT_ENABLED", "0").lower() in ("1", "true", "yes")
SENTIMENT_SOURCE = os.getenv("SENTIMENT_SOURCE", "finnhub").lower()
SENTIMENT_WINDOW_S = int(os.getenv("SENTIMENT_WINDOW_S", "900"))
SENTIMENT_TOP_N = int(os.getenv("SENTIMENT_TOP_N", "50"))
SENTIMENT_POLL_S = int(os.getenv("SENTIMENT_POLL_S", "60"))

# Seed assets (bases) we’ll track; can be augmented at runtime via set_keywords()
SENTIMENT_ASSETS = [
    a.strip().upper()
    for a in os.getenv("SENTIMENT_ASSETS", "BTC,ETH,BNB,ADA,XRP,SOL").split(",")
    if a.strip()
]

# Optional persistent history
SENTIMENT_HISTORY_PATH = os.getenv("SENTIMENT_HISTORY_PATH", "").strip()
SENTIMENT_HISTORY_MAX_MB = float(os.getenv("SENTIMENT_HISTORY_MAX_MB", "128"))

# ----------------------- Deps -------------------------

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    _analyzer = SentimentIntensityAnalyzer()
except Exception as e:
    _analyzer = None
    LOG.error("VADER not available: %s", e)

# Optional provider helper (if present in repo)
_filter_news_by_assets = None
try:
    from sentiment.providers.finnhub_provider import filter_news_by_assets as _filter_news_by_assets  # type: ignore
except Exception:
    # We'll fallback to a simple built-in fetcher below.
    pass

# ----------------------- State ------------------------

# Rolling window store: { BASE: [(ts, vader_compound), ...] }
_store: Dict[str, List[List[float]]] = {a: [] for a in SENTIMENT_ASSETS}

# Keywords per base (e.g., {"BTC": ["BTC","Bitcoin"]})
_keywords: Dict[str, List[str]] = {a: [a] for a in SENTIMENT_ASSETS}

# Background task
_task: Optional[asyncio.Task] = None
_lock = asyncio.Lock()

# ----------------------- Utils ------------------------

def _clip(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x

def _to_prob(vader_compound: float) -> float:
    """Map VADER compound [-1,1] -> [0,1]."""
    return _clip(0.5 + 0.5 * float(vader_compound), 0.0, 1.0)

def _trim_window(now: float) -> None:
    cutoff = now - SENTIMENT_WINDOW_S
    for base, arr in list(_store.items()):
        if not arr:
            continue
        # arr is sorted by append-time; find first >= cutoff
        j = 0
        for j in range(len(arr)):
            if arr[j][0] >= cutoff:
                break
        _store[base] = arr[j:] if arr else []

def _ensure_asset(base: str) -> None:
    base = base.upper()
    if base not in _store:
        _store[base] = []
    if base not in _keywords:
        _keywords[base] = [base]

def set_keywords(base: str, keywords: List[str]) -> None:
    """
    Public API to set/extend the tracked keywords for a given base (BTC, ETH, …).
    """
    base = base.upper()
    _ensure_asset(base)
    clean = [k.strip() for k in keywords if k and k.strip()]
    if clean:
        _keywords[base] = clean

# -------------------- Finnhub fallback ----------------

def _finnhub_fetch_texts_builtin(assets: List[str]) -> Dict[str, List[str]]:
    """
    Simple Finnhub fetcher if a provider helper is not available.
    Pulls the global crypto news list, then filters by keywords.
    """
    import requests
    out: Dict[str, List[str]] = {a: [] for a in assets}
    if not FINNHUB_API_KEY:
        return out

    url = f"https://finnhub.io/api/v1/news?category=crypto&token={FINNHUB_API_KEY}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        items = resp.json() or []
        if not isinstance(items, list):
            return out

        # Build a simple text blob per article
        texts: List[str] = []
        for it in items[:200]:  # cap raw fetch volume
            title = (it.get("headline") or "") if isinstance(it, dict) else ""
            summary = (it.get("summary") or "") if isinstance(it, dict) else ""
            source = (it.get("source") or "") if isinstance(it, dict) else ""
            txt = " ".join([title, summary, source]).strip()
            if txt:
                texts.append(txt)

        # Keyword filter to assets
        for base in assets:
            kws = _keywords.get(base.upper(), [base.upper()])
            base_texts = []
            for t in texts:
                T = t.lower()
                if any(kw.lower() in T for kw in kws):
                    base_texts.append(t)
            out[base] = base_texts
    except Exception as e:
        LOG.error("Finnhub builtin fetch failed: %s", e)
    return out

def _fetch_texts(assets: List[str]) -> Dict[str, List[str]]:
    """
    Fetch/prepare texts per base symbol.
    Currently supports 'finnhub' source.
    """
    if SENTIMENT_SOURCE != "finnhub":
        return {a: [] for a in assets}

    if not FINNHUB_API_KEY:
        LOG.warning("FINNHUB_API_KEY missing; sentiment fetch will be empty.")
        return {a: [] for a in assets}

    # Prefer repo provider if present
    if _filter_news_by_assets is not None:
        try:
            return _filter_news_by_assets(assets)  # type: ignore
        except Exception as e:
            LOG.error("Provider filter_news_by_assets failed: %s", e)

    # Fallback builtin method
    return _finnhub_fetch_texts_builtin(assets)

# -------------------- Aggregations --------------------

def _aggregate_internal(now: Optional[float] = None) -> Dict[str, Dict[str, float]]:
    """
    Compute average compound per base over the current rolling window.
    Returns { BASE: {score: float[-1..1], n: int} }
    """
    if now is None:
        now = time.time()
    _trim_window(now)

    out: Dict[str, Dict[str, float]] = {}
    for base, arr in _store.items():
        if not arr:
            out[base] = {"score": 0.0, "n": 0}
            continue
        vals = [float(v) for (_, v) in arr]
        avg = sum(vals) / max(1, len(vals))
        out[base] = {"score": avg, "n": len(vals)}
    return out

def aggregate_probs() -> Dict[str, float]:
    """
    Public API used by your backend:
    Returns per-base probabilities ∈ [0,1],
    mapped from VADER compound scores.
    """
    snap = _aggregate_internal()
    return {b: _to_prob(v["score"]) for b, v in snap.items()}

def latest_probs() -> Dict[str, float]:
    """
    Alias kept for compatibility with existing imports.
    """
    return aggregate_probs()

def snapshot() -> Dict[str, Any]:
    """
    Public API for /sentiment endpoint response.
    Includes source, window size and per-base scores.
    """
    snap = _aggregate_internal()
    return {
        "source": SENTIMENT_SOURCE,
        "window_sec": SENTIMENT_WINDOW_S,
        "scores": snap,
    }

# ------------------ History persistence ----------------

def _append_history_jsonl(snap: Dict[str, Any]) -> None:
    """
    Append a snapshot to JSONL history if SENTIMENT_HISTORY_PATH is set.
    Each line: {"ts": <unix>, "scores": {...}}
    """
    path = SENTIMENT_HISTORY_PATH
    if not path:
        return
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        rec = {"ts": int(time.time()), "scores": snap.get("scores", {})}
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        # crude cap by size
        try:
            sz_mb = os.path.getsize(path) / (1024 * 1024)
            if sz_mb > SENTIMENT_HISTORY_MAX_MB:
                # truncate oldest half
                with open(path, "r", encoding="utf-8") as fr:
                    lines = fr.readlines()
                mid = len(lines) // 2
                with open(path, "w", encoding="utf-8") as fw:
                    fw.writelines(lines[mid:])
        except Exception:
            pass
    except Exception as e:
        LOG.error("Failed to append sentiment history: %s", e)

# ------------------- Public cycle API -------------------

def run_sentiment_cycle() -> Dict[str, Dict[str, float]]:
    """
    Non-async one-shot pull + score + aggregate.
    Returns {base: {score, n}}
    """
    if not SENTIMENT_ENABLED or _analyzer is None:
        return {a: {"score": 0.0, "n": 0} for a in _store.keys()}

    now = time.time()
    texts_by_asset = _fetch_texts(list(_store.keys()))
    for base, texts in texts_by_asset.items():
        if not texts:
            continue
        # Score top-N texts
        for t in texts[: max(1, SENTIMENT_TOP_N)]:
            try:
                vs = _analyzer.polarity_scores(t or "")
                comp = float(vs.get("compound", 0.0))
                _ensure_asset(base)
                _store[base].append([now, comp])
            except Exception:
                continue

    _trim_window(now)
    snap = _aggregate_internal(now)
    _append_history_jsonl({"scores": snap})
    return snap

# -------------------- Background poller ----------------

async def _poller() -> None:
    """
    Async poller that keeps updating the rolling window and history.
    """
    LOG.info("Sentiment poller started | source=%s | window=%ss | poll=%ss",
             SENTIMENT_SOURCE, SENTIMENT_WINDOW_S, SENTIMENT_POLL_S)

    while True:
        try:
            async with _lock:
                run_sentiment_cycle()
        except Exception as e:
            LOG.error("Sentiment poller error: %s", e)
        await asyncio.sleep(max(5, SENTIMENT_POLL_S))

def start_background() -> Optional[asyncio.Task]:
    """
    Start the background poller; safe to call multiple times.
    Returns the asyncio.Task or None if disabled.
    """
    global _task
    if not SENTIMENT_ENABLED:
        LOG.info("Sentiment disabled by env; background not started.")
        return None
    if _analyzer is None:
        LOG.error("VADER analyzer missing; cannot start background.")
        return None
    if _task and not _task.done():
        return _task
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    _task = loop.create_task(_poller())
    return _task

def stop_background() -> None:
    """
    Stop the background poller if running.
    """
    global _task
    if _task and not _task.done():
        _task.cancel()
        _task = None