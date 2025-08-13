# sentiment/providers/finnhub_provider.py
import os, re, logging, requests
from typing import Dict, List

log = logging.getLogger("FinnhubProvider")

API_KEY = (os.getenv("FINNHUB_API_KEY") or os.getenv("FINNHUB_KEY") or "").strip()

# sane defaults; can be overridden via SENTIMENT_KW_<ASSET>
DEFAULT_KW = {
    "BTC": ["bitcoin","btc","btc/usdt","btc-usdt","btc price"],
    "ETH": ["ethereum","eth","eth/usdt","eth-usdt","ether price"],
    "BNB": ["binance coin","bnb","bnb/usdt","bnb-usdt"],
    "ADA": ["cardano","ada","ada/usdt","ada-usdt"],
    "XRP": ["ripple","xrp","xrp/usdt","xrp-usdt"],
    "SOL": ["solana","sol","sol/usdt","sol-usdt"],
}

def _kw_for(asset: str) -> List[str]:
    raw = os.getenv(f"SENTIMENT_KW_{asset.upper()}", "")
    if raw.strip():
        return [x.strip().lower() for x in raw.split(",") if x.strip()]
    return DEFAULT_KW.get(asset.upper(), [asset.lower()])

def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()

def _fetch_recent_news(limit: int = 100) -> List[Dict]:
    if not API_KEY:
        log.warning("FINNHUB_API_KEY/FINNHUB_KEY missing; returning no news")
        return []
    out: List[Dict] = []
    try:
        for cat in ("general","crypto"):
            url = f"https://finnhub.io/api/v1/news?category={cat}&token={API_KEY}"
            r = requests.get(url, timeout=8)
            if r.ok:
                out.extend(r.json()[:limit])
    except Exception as e:
        log.warning(f"Finnhub fetch error: {e}")
    return out[:limit]

def filter_news_by_assets(assets: List[str]) -> Dict[str, List[str]]:
    news = _fetch_recent_news(limit=int(os.getenv("FINNHUB_NEWS_LIMIT","50")))
    by_asset = {a.upper(): [] for a in assets}
    if not news:
        return by_asset

    texts = []
    for n in news:
        t = _norm(n.get("headline") or n.get("summary") or "")
        if t:
            texts.append(t)

    for a in assets:
        kws = _kw_for(a)
        bucket = []
        for t in texts:
            if any(kw in t for kw in kws):
                bucket.append(t)
                if len(bucket) >= 100:
                    break
        by_asset[a.upper()] = bucket
    for a in assets:
        log.debug(f"[Finnhub] {a}: {len(by_asset[a])} matches (kw={_kw_for(a)[:4]}...)")
    return by_asset