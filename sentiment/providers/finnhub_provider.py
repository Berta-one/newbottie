# sentiment/providers/finnhub_provider.py
import os
import time
import logging
from typing import List, Dict, Any, Optional
import requests

log = logging.getLogger("FinnhubProvider")

FINNHUB_KEY = os.getenv("FINNHUB_KEY", "")
FINNHUB_NEWS_URL = "https://finnhub.io/api/v1/news"

# Simple in-memory cache to avoid hammering the API
_cache: Dict[str, Any] = {"ts": 0.0, "items": []}
CACHE_TTL = 60.0  # seconds

DEFAULT_KEYWORDS = {
    "BTC": ["bitcoin", "btc"],
    "ETH": ["ethereum", "eth"],
    "BNB": ["bnb", "binance coin"],
    "XRP": ["xrp", "ripple"],
    "ADA": ["cardano", "ada"],
    "SOL": ["solana", "sol"],
}

def _load_keywords(assets: List[str]) -> Dict[str, List[str]]:
    # In future, let users override with ENV (e.g., SENTIMENT_KEYWORDS_JSON)
    kw = {}
    for a in assets:
        a_up = a.upper().strip()
        kw[a_up] = DEFAULT_KEYWORDS.get(a_up, [a_up])
    return kw

def fetch_crypto_news_raw() -> List[Dict[str, Any]]:
    """Pull recent crypto news from Finnhub, cached briefly."""
    global _cache
    now = time.time()
    if now - _cache["ts"] < CACHE_TTL and _cache["items"]:
        return _cache["items"]

    if not FINNHUB_KEY:
        log.warning("FINNHUB_KEY missing; returning empty news list.")
        _cache = {"ts": now, "items": []}
        return []

    params = {"category": "crypto", "token": FINNHUB_KEY}
    try:
        resp = requests.get(FINNHUB_NEWS_URL, params=params, timeout=10)
        resp.raise_for_status()
        items = resp.json() or []
        # Normalize fields we care about
        out = []
        for it in items:
            headline = (it.get("headline") or "").strip()
            summary = (it.get("summary") or "").strip()
            source = (it.get("source") or "").strip()
            url = (it.get("url") or "").strip()
            ts = it.get("datetime") or 0
            if not headline:
                continue
            out.append({"t": ts, "headline": headline, "summary": summary, "source": source, "url": url})
        _cache = {"ts": now, "items": out}
        return out
    except Exception as e:
        log.error(f"Finnhub news error: {e}")
        return []

def filter_news_by_assets(assets: List[str]) -> Dict[str, List[str]]:
    """Return {BASE: [texts...]} from latest Finnhub crypto news filtered by per-asset keywords."""
    raw = fetch_crypto_news_raw()
    if not raw:
        return {a: [] for a in assets}

    keywords = _load_keywords(assets)
    per_asset: Dict[str, List[str]] = {a.upper(): [] for a in assets}

    for item in raw:
        text = item["headline"]
        blob = f"{text} {item.get('summary','')}".lower()
        for base, kws in keywords.items():
            if any(kw.lower() in blob for kw in kws):
                per_asset[base].append(text)

    return per_asset