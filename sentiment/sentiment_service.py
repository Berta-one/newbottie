# sentiment/sentiment_service.py
import os, time, json, logging, threading
from typing import Dict, List, Any, Optional
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

log = logging.getLogger("SentimentService")

# ── Config
FINNHUB_API_KEY = (os.getenv("FINNHUB_API_KEY") or "").strip()
SENTIMENT_ENABLED = os.getenv("SENTIMENT_ENABLED", "0").lower() in ("1","true","yes")
SENTIMENT_SOURCE  = os.getenv("SENTIMENT_SOURCE", "finnhub").lower()
SENTIMENT_WINDOW_S = int(os.getenv("SENTIMENT_WINDOW_S", "900"))
SENTIMENT_ASSETS = [a.strip().upper() for a in os.getenv("SENTIMENT_ASSETS","BTC,ETH,BNB,ADA,XRP,SOL").split(",") if a.strip()]
SENTIMENT_TOP_N = int(os.getenv("SENTIMENT_TOP_N", "50"))
SENTIMENT_POLL_S = int(os.getenv("SENTIMENT_POLL_S", "60"))
SENTIMENT_HISTORY_PATH = os.getenv("SENTIMENT_HISTORY_PATH", "").strip()  # optional JSONL persistence

if not FINNHUB_API_KEY and SENTIMENT_SOURCE == "finnhub":
    log.warning("⚠ FINNHUB_API_KEY is missing! News pull will be empty.")

_analyzer = SentimentIntensityAnalyzer()

# Rolling store: { BASE: [(ts, compound in [-1,1])...] }
_store: Dict[str, List[Any]] = {a: [] for a in SENTIMENT_ASSETS}

_bg_thread: Optional[threading.Thread] = None
_bg_stop = threading.Event()

def _clip(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x

def _to_prob(vader_compound: float) -> float:
    # map [-1,1] -> [0,1]
    return _clip(0.5 + 0.5 * float(vader_compound), 0.0, 1.0)

def _trim_window(now: float):
    cutoff = now - SENTIMENT_WINDOW_S
    for a, arr in list(_store.items()):
        j = 0
        for j in range(len(arr)):
            if arr[j][0] >= cutoff:
                break
        _store[a] = arr[j:] if arr else []

def _fetch_texts(assets: List[str]) -> Dict[str, List[str]]:
    if SENTIMENT_SOURCE == "finnhub":
        from sentiment.providers.finnhub_provider import filter_news_by_assets
        return filter_news_by_assets(assets)
    return {a: [] for a in assets}

def _persist(asset: str, ts: float, compound: float, text: str):
    if not SENTIMENT_HISTORY_PATH:
        return
    try:
        os.makedirs(os.path.dirname(SENTIMENT_HISTORY_PATH), exist_ok=True)
        with open(SENTIMENT_HISTORY_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps({"t": ts, "asset": asset, "compound": compound, "text": text}) + "\n")
    except Exception as e:
        log.debug(f"history persist fail: {e}")

def run_sentiment_cycle() -> Dict[str, Dict[str, float]]:
    """
    Pull latest texts, score, push to rolling window.
    Returns { BASE: {score:<avg in [-1,1]>, n:int} }
    """
    if not SENTIMENT_ENABLED:
        return {a: {"score": 0.0, "n": 0} for a in SENTIMENT_ASSETS}

    now = time.time()
    texts_by_asset = _fetch_texts(SENTIMENT_ASSETS)

    for base, texts in texts_by_asset.items():
        if not texts:
            log.debug(f"[Sentiment] {base}: 0 texts")
            continue
        used = 0
        for t in texts[:SENTIMENT_TOP_N]:
            vs = _analyzer.polarity_scores(t)
            comp = float(vs.get("compound", 0.0))
            _store.setdefault(base, []).append((now, comp))
            _persist(base, now, comp, t)
            used += 1
        log.debug(f"[Sentiment] {base}: added {used} texts (window={SENTIMENT_WINDOW_S}s)")

    _trim_window(now)
    out: Dict[str, Dict[str, float]] = {}
    for a, arr in _store.items():
        if not arr:
            out[a] = {"score": 0.0, "n": 0}
            continue
        vals = [v for (_, v) in arr]
        out[a] = {"score": sum(vals) / max(1, len(vals)), "n": len(vals)}
    return out

def latest_probs() -> Dict[str, float]:
    """Per-asset probabilities mapped to [0,1]. Ensures a fresh pull."""
    snap = run_sentiment_cycle()
    return {a: _to_prob(v["score"]) for a, v in snap.items()}

def aggregate_probs() -> Dict[str, float]:
    """Alias used by some imports; same as latest_probs()."""
    return latest_probs()

def snapshot() -> Dict[str, Any]:
    """One-shot pull + summary (used by /sentiment endpoint)."""
    scores = run_sentiment_cycle()
    return {
        "source": SENTIMENT_SOURCE,
        "window_sec": SENTIMENT_WINDOW_S,
        "scores": scores
    }

# background worker -----------------------------------------------------------
def _worker():
    log.info(f"Sentiment background loop started | source={SENTIMENT_SOURCE} | poll={SENTIMENT_POLL_S}s")
    while not _bg_stop.is_set():
        try:
            run_sentiment_cycle()
        except Exception as e:
            log.warning(f"sentiment loop error: {e}")
        _bg_stop.wait(SENTIMENT_POLL_S)
    log.info("Sentiment background loop stopped")

def start_background():
    """Start background poller (idempotent)."""
    global _bg_thread
    if _bg_thread and _bg_thread.is_alive():
        return
    _bg_stop.clear()
    _bg_thread = threading.Thread(target=_worker, name="sentiment-loop", daemon=True)
    _bg_thread.start()

def stop_background():
    _bg_stop.set()

def set_keywords(asset: str, keywords: List[str]) -> None:
    """
    Compatibility function for setting keywords (not implemented in this version).
    Keywords are configured via environment variables SENTIMENT_KW_<ASSET>.
    """
    log.info(f"set_keywords called for {asset} with {keywords} - use environment variables instead")
    pass
