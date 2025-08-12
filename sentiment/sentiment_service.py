# sentiment/sentiment_service.py
import os
import time
import json
import logging
import asyncio
from typing import Dict, List, Any, Iterable, Optional
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# === Environment ===
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "").strip()
SENTIMENT_ENABLED = os.getenv("SENTIMENT_ENABLED", "0").lower() in ("1", "true", "yes")
SENTIMENT_SOURCE = os.getenv("SENTIMENT_SOURCE", "finnhub").lower()
SENTIMENT_WINDOW_S = int(os.getenv("SENTIMENT_WINDOW_S", "900"))
SENTIMENT_ASSETS = [a.strip().upper() for a in os.getenv("SENTIMENT_ASSETS", "BTC,ETH,BNB,ADA,XRP,SOL").split(",") if a.strip()]
SENTIMENT_TOP_N = int(os.getenv("SENTIMENT_TOP_N", "50"))
SENTIMENT_HISTORY_PATH = os.getenv("SENTIMENT_HISTORY_PATH", "").strip()
SENTIMENT_POLL_S = int(os.getenv("SENTIMENT_POLL_S", "60"))

log = logging.getLogger("SentimentService")
_analyzer = SentimentIntensityAnalyzer()

# Rolling window store: { BASE: [(ts, score), ...] }
_store: Dict[str, List[Any]] = {a: [] for a in SENTIMENT_ASSETS}

# === Load history on boot (best effort) ===
if SENTIMENT_HISTORY_PATH and os.path.exists(SENTIMENT_HISTORY_PATH):
    try:
        with open(SENTIMENT_HISTORY_PATH, "r") as f:
            for line in f:
                if not line.strip():
                    continue
                rec = json.loads(line)
                base = (rec.get("asset") or "").upper()
                ts = float(rec.get("ts", 0))
                score = float(rec.get("score", 0))
                if base:
                    _store.setdefault(base, []).append((ts, score))
        log.info(f"Loaded sentiment history from {SENTIMENT_HISTORY_PATH}")
    except Exception as e:
        log.error(f"Failed to load sentiment history: {e}")

def _clip(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x

def _to_prob(vader_compound: float) -> float:
    return _clip(0.5 + 0.5 * vader_compound, 0.0, 1.0)

def _trim_window(now: float):
    cutoff = now - SENTIMENT_WINDOW_S
    for a in list(_store.keys()):
        arr = _store[a]
        k = 0
        for k in range(len(arr)):
            if arr[k][0] >= cutoff:
                break
        _store[a] = arr[k:] if arr else []

def _save_history(asset: str, ts: float, score: float):
    if not SENTIMENT_HISTORY_PATH:
        return
    try:
        os.makedirs(os.path.dirname(SENTIMENT_HISTORY_PATH), exist_ok=True)
        with open(SENTIMENT_HISTORY_PATH, "a") as f:
            f.write(json.dumps({"asset": asset, "ts": ts, "score": score}) + "\n")
    except Exception as e:
        log.error(f"Failed to write sentiment history: {e}")

def _fetch_texts(assets: List[str]) -> Dict[str, List[str]]:
    if SENTIMENT_SOURCE == "finnhub":
        from sentiment.providers.finnhub_provider import filter_news_by_assets
        return filter_news_by_assets(assets)
    return {a: [] for a in assets}

def run_sentiment_cycle() -> Dict[str, Dict[str, float]]:
    """
    Pull latest texts, push VADER scores into rolling window (and disk).
    Return { BASE: {score:<avg in [-1,1]>, n:int} } for current window.
    """
    if not SENTIMENT_ENABLED:
        return {a: {"score": 0.0, "n": 0} for a in SENTIMENT_ASSETS}

    now = time.time()
    texts_by_asset = _fetch_texts(SENTIMENT_ASSETS)
    for base, texts in texts_by_asset.items():
        if not texts:
            continue
        for t in texts[:SENTIMENT_TOP_N]:
            vs = _analyzer.polarity_scores(t)
            comp = float(vs.get("compound", 0.0))
            base_u = base.upper()
            _store.setdefault(base_u, []).append((now, comp))
            _save_history(base_u, now, comp)

    _trim_window(now)

    out: Dict[str, Dict[str, float]] = {}
    for a, arr in _store.items():
        if not arr:
            out[a] = {"score": 0.0, "n": 0}
            continue
        vals = [v for (_, v) in arr]
        avg = sum(vals) / max(1, len(vals))
        out[a] = {"score": avg, "n": len(vals)}
    return out

def latest_probs() -> Dict[str, float]:
    snap = run_sentiment_cycle()
    return {a: _to_prob(v["score"]) for a, v in snap.items()}

def snapshot() -> Dict[str, Any]:
    snap = run_sentiment_cycle()
    return {
        "source": SENTIMENT_SOURCE,
        "window_sec": SENTIMENT_WINDOW_S,
        "scores": snap
    }

def list_assets() -> List[str]:
    seen = set(_store.keys()) | set(SENTIMENT_ASSETS)
    return sorted(seen)

def history_points(
    assets: Optional[Iterable[str]] = None,
    since: Optional[float] = None,
    until: Optional[float] = None,
    max_points: int = 1000
) -> Dict[str, List[Dict[str, float]]]:
    assets_u = [a.upper() for a in (assets or list_assets())]
    since = float(since) if since is not None else 0.0
    until = float(until) if until is not None else time.time()

    by_asset: Dict[str, List[Dict[str, float]]] = {a: [] for a in assets_u}
    if SENTIMENT_HISTORY_PATH and os.path.exists(SENTIMENT_HISTORY_PATH):
        try:
            with open(SENTIMENT_HISTORY_PATH, "r") as f:
                for line in f:
                    if not line.strip():
                        continue
                    rec = json.loads(line)
                    a = (rec.get("asset") or "").upper()
                    if a not in by_asset:
                        continue
                    ts = float(rec.get("ts", 0))
                    if ts < since or ts > until:
                        continue
                    score = float(rec.get("score", 0))
                    by_asset[a].append({"t": ts, "score": score, "prob": _to_prob(score)})
        except Exception as e:
            log.error(f"Failed reading history file: {e}")

    for a in assets_u:
        arr = _store.get(a, [])
        for ts, score in arr:
            if ts < since or ts > until:
                continue
            by_asset[a].append({"t": ts, "score": score, "prob": _to_prob(score)})

    for a in assets_u:
        pts = sorted(by_asset[a], key=lambda r: r["t"])
        n = len(pts)
        if n > max_points > 0:
            stride = max(1, n // max_points)
            by_asset[a] = [pts[i] for i in range(0, n, stride)][:max_points]
        else:
            by_asset[a] = pts

    return by_asset

# ===== Background polling support (so app.py can just call start_background) ====
_bg_task: Optional[asyncio.Task] = None
_stop_flag = asyncio.Event()

async def _bg_loop(poll_s: Optional[int] = None):
    if not SENTIMENT_ENABLED:
        log.info("Sentiment disabled; background loop idling.")
        return
    ps = int(poll_s or SENTIMENT_POLL_S)
    log.info(f"Sentiment background loop started (poll={ps}s, source={SENTIMENT_SOURCE})")
    while not _stop_flag.is_set():
        try:
            run_sentiment_cycle()
        except Exception as e:
            log.error(f"Sentiment cycle error: {e}")
        try:
            await asyncio.wait_for(_stop_flag.wait(), timeout=ps)
        except asyncio.TimeoutError:
            pass
    log.info("Sentiment background loop stopped.")

def start_background(poll_s: Optional[int] = None):
    global _bg_task, _stop_flag
    if _bg_task and not _bg_task.done():
        return _bg_task
    _stop_flag = asyncio.Event()
    loop = asyncio.get_event_loop()
    _bg_task = loop.create_task(_bg_loop(poll_s=poll_s))
    return _bg_task

def stop_background():
    _stop_flag.set()