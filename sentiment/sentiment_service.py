# sentiment/sentiment_service.py
import os
import time
import json
import logging
from typing import Dict, List, Any
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# === Environment Variables ===
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "").strip()
SENTIMENT_ENABLED = os.getenv("SENTIMENT_ENABLED", "0") not in ("0", "false", "False", "", None)
SENTIMENT_SOURCE = os.getenv("SENTIMENT_SOURCE", "finnhub").lower()
SENTIMENT_WINDOW_S = int(os.getenv("SENTIMENT_WINDOW_S", "900"))
SENTIMENT_ASSETS = [a.strip().upper() for a in os.getenv("SENTIMENT_ASSETS", "BTC,ETH,BNB,ADA,XRP,SOL").split(",") if a.strip()]
SENTIMENT_TOP_N = int(os.getenv("SENTIMENT_TOP_N", "50"))
SENTIMENT_HISTORY_PATH = os.getenv("SENTIMENT_HISTORY_PATH", "").strip()

log = logging.getLogger("SentimentService")
_analyzer = SentimentIntensityAnalyzer()

# Rolling window store: { BASE: [(ts, score), ...] }
_store: Dict[str, List[Any]] = {a: [] for a in SENTIMENT_ASSETS}

# === Load history if file exists ===
if SENTIMENT_HISTORY_PATH and os.path.exists(SENTIMENT_HISTORY_PATH):
    try:
        with open(SENTIMENT_HISTORY_PATH, "r") as f:
            for line in f:
                rec = json.loads(line)
                base = rec.get("asset")
                ts = rec.get("ts")
                score = rec.get("score")
                if base in _store:
                    _store[base].append((ts, score))
        log.info(f"Loaded sentiment history from {SENTIMENT_HISTORY_PATH}")
    except Exception as e:
        log.error(f"Failed to load sentiment history: {e}")

def _clip(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x

def _to_prob(vader_compound: float) -> float:
    return _clip(0.5 + 0.5 * vader_compound, 0.0, 1.0)

def _trim_window(now: float):
    cutoff = now - SENTIMENT_WINDOW_S
    for a in _store.keys():
        arr = _store[a]
        j = 0
        for j in range(len(arr)):
            if arr[j][0] >= cutoff:
                break
        _store[a] = arr[j:] if arr else []

def _save_history(asset: str, ts: float, score: float):
    """Append sentiment data to history file."""
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
            _store.setdefault(base, []).append((now, comp))
            _save_history(base, now, comp)

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
    return {"window_sec": SENTIMENT_WINDOW_S, "scores": snap}