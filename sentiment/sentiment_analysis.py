# sentiment/sentiment_analysis.py
# Finnhub-backed crypto news sentiment service.
# Exposes:
#   - SentimentService.set_keywords(base, keywords)
#   - SentimentService.fetch_all()
#   - SentimentService.aggregate() -> { base: {"score": float[-1..1], "n": int} }

from __future__ import annotations

import os
import time
import math
import re
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

import requests


# ----------------------------- Utilities --------------------------------------

_POS_WORDS = {
    "bullish", "surge", "rally", "gain", "gains", "beat", "beats",
    "record", "optimism", "optimistic", "positive", "rebound", "breakout",
    "strong", "soar", "soaring", "recover", "recovery", "improve", "uptrend",
    "upgrade", "accumulate", "buy", "overweight"
}

_NEG_WORDS = {
    "bearish", "drop", "plunge", "fall", "falls", "miss", "misses",
    "crash", "fear", "pessimism", "negative", "selloff", "dump",
    "weak", "collapse", "lawsuit", "hack", "ban", "downgrade",
    "reduce", "sell", "underweight"
}

_WORD_RE = re.compile(r"[A-Za-z']+")

def _simple_sentiment(text: str) -> float:
    """
    Returns a compound sentiment in [-1,1] from a tiny lexicon over headline+summary.
    """
    if not text:
        return 0.0
    words = [w.lower() for w in _WORD_RE.findall(text)]
    if not words:
        return 0.0

    pos = sum(1 for w in words if w in _POS_WORDS)
    neg = sum(1 for w in words if w in _NEG_WORDS)
    total = pos + neg
    if total == 0:
        return 0.0

    raw = (pos - neg) / float(total)  # in [-1,1]
    # mild scaling to avoid extremes on tiny counts
    return max(-1.0, min(1.0, raw * 0.8))


# ----------------------------- Service ----------------------------------------

@dataclass
class _BaseState:
    keywords: List[str] = field(default_factory=list)
    last_fetch_ts: float = 0.0  # epoch seconds (throttle)
    articles: List[Dict[str, Any]] = field(default_factory=list)  # recent cache


class SentimentService:
    """
    Finnhub crypto news → per-base sentiment.
    - Set FINNHUB_API_KEY in environment.
    - Optionally tune:
        SENTIMENT_WINDOW_S (default 900)  : rolling window to keep recent articles
        FINNHUB_MIN_INTERVAL_S (default 45): throttle per base fetch interval
        FINNHUB_NEWS_LIMIT (default 50)    : how many latest items to pull per fetch
    - Public methods:
        set_keywords(base, keywords)
        fetch_all()
        aggregate() -> { base: {"score": float[-1..1], "n": int} }
    """
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._by_base: Dict[str, _BaseState] = {}

        self.api_key = (os.getenv("FINNHUB_API_KEY") or "").strip()

        # Configs
        self.window_s = int(os.getenv("SENTIMENT_WINDOW_S", "900"))  # 15 min
        self.min_interval_s = int(os.getenv("FINNHUB_MIN_INTERVAL_S", "45"))
        self.news_limit = int(os.getenv("FINNHUB_NEWS_LIMIT", "50"))

        # Endpoint (Finnhub crypto/general news)
        # Docs: https://finnhub.io/docs/api/news
        # category can be: general, forex, crypto, merger, ...
        self.news_url = "https://finnhub.io/api/v1/news"

    # -------------------- Public API --------------------

    def set_keywords(self, base: str, keywords: List[str]) -> None:
        """
        Register/replace the keywords associated with a BASE asset (e.g., "BTC", "ETH").
        """
        base = base.upper().strip()
        kws = sorted({k.strip() for k in keywords if k and k.strip()})
        if not base or not kws:
            return
        with self._lock:
            st = self._by_base.get(base) or _BaseState()
            st.keywords = kws
            self._by_base[base] = st

    def fetch_all(self) -> None:
        """
        Poll Finnhub for each base we track (throttled), keep only recent-window articles.
        """
        if not self.api_key:
            # no key: skip quietly — the caller can handle absence (neutral)
            return

        now = time.time()
        bases = []
        with self._lock:
            bases = list(self._by_base.keys())

        for base in bases:
            try:
                with self._lock:
                    st = self._by_base.get(base)
                    if not st:
                        continue
                    # throttle per base
                    if now - st.last_fetch_ts < self.min_interval_s:
                        continue
                    st.last_fetch_ts = now

                # pull latest category=crypto news
                # NOTE: Finnhub /news does not support symbol filtering; we filter client-side.
                params = {
                    "category": "crypto",
                    "token": self.api_key,
                }
                # Safe timeout; Render free tier can be spiky — keep < 10s.
                r = requests.get(self.news_url, params=params, timeout=8)
                if r.status_code != 200:
                    # tolerate 4xx/5xx briefly; keep old cache
                    continue
                items = r.json()
                if not isinstance(items, list):
                    continue

                # Prepare filters
                with self._lock:
                    st = self._by_base.get(base)
                    if not st:
                        continue
                    kws = st.keywords or [base]

                base_upper = base.upper()
                # Simple relevance filter: mention of BASE or any keyword in title or summary
                new_articles: List[Dict[str, Any]] = []
                for it in items[: self.news_limit]:
                    title = (it.get("headline") or it.get("title") or "")[:500]
                    summary = (it.get("summary") or it.get("source") or "")[:1000]
                    ts = it.get("datetime") or it.get("time") or it.get("published_at")
                    # Finnhub returns unix seconds in "datetime"
                    try:
                        art_ts = float(ts) if ts is not None else now
                        if art_ts > 10_000_000_000:  # millis → seconds
                            art_ts = art_ts / 1000.0
                    except Exception:
                        art_ts = now

                    blob = f"{title} {summary}".strip()
                    if not blob:
                        continue

                    txt_upper = blob.upper()
                    if base_upper in txt_upper or any(k.upper() in txt_upper for k in kws):
                        # keep article within window_s
                        if now - art_ts <= max(60.0, float(self.window_s) * 2.0):
                            score = _simple_sentiment(blob)
                            new_articles.append({
                                "ts": art_ts,
                                "title": title,
                                "summary": summary,
                                "score": float(score),
                            })

                # merge, drop stale (older than window_s), de-dup by (title, ts)
                with self._lock:
                    st = self._by_base.get(base)
                    if not st:
                        continue
                    merged = (st.articles or []) + new_articles
                    # de-dup
                    seen = set()
                    deduped: List[Dict[str, Any]] = []
                    for a in merged:
                        key = (a.get("title") or "", int(a.get("ts") or 0))
                        if key in seen:
                            continue
                        seen.add(key)
                        deduped.append(a)
                    # drop stale
                    fresh = [a for a in deduped if now - float(a.get("ts", 0.0)) <= self.window_s]
                    st.articles = sorted(fresh, key=lambda x: x.get("ts", 0.0), reverse=True)

            except requests.exceptions.RequestException:
                # transient network issue; keep old cache
                continue
            except Exception:
                # never sink the caller; keep old cache
                continue

    def aggregate(self) -> Dict[str, Dict[str, Any]]:
        """
        Returns per-base {"score": float[-1..1], "n": int} over the rolling window.
        """
        out: Dict[str, Dict[str, Any]] = {}
        now = time.time()
        with self._lock:
            for base, st in self._by_base.items():
                arts = [a for a in (st.articles or []) if now - float(a.get("ts", 0.0)) <= self.window_s]
                n = len(arts)
                if n == 0:
                    out[base] = {"score": 0.0, "n": 0}
                    continue
                avg = sum(float(a.get("score", 0.0)) for a in arts) / float(n)
                # clip to [-1,1]
                avg = max(-1.0, min(1.0, avg))
                out[base] = {"score": float(avg), "n": int(n)}
        return out
