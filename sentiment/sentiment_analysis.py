# sentiment/sentiment_analysis.py
# Async news fetch (CryptoPanic, optional Twitter) + VADER sentiment scoring
import os, time, asyncio, logging, re
from typing import List, Dict, Any, Optional, Tuple
import httpx
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

log = logging.getLogger("Sentiment")

# ENV
CRYPTOPANIC_TOKEN   = os.getenv("CRYPTOPANIC_TOKEN", "").strip()
TWITTER_BEARER      = os.getenv("TWITTER_BEARER", "").strip()
SENTIMENT_WINDOW_S  = int(os.getenv("SENTIMENT_WINDOW_S", "900"))  # 15min window
SENTIMENT_TOP_N     = int(os.getenv("SENTIMENT_TOP_N", "50"))      # max headlines per pass
SENTIMENT_LANG      = os.getenv("SENTIMENT_LANG", "en").lower()

# Map symbol base -> query keywords (extend as needed)
DEFAULT_KEYWORDS = {
    "BTC": ["bitcoin", "btc"],
    "ETH": ["ethereum", "eth"],
    "BNB": ["bnb", "binance coin"],
    "SOL": ["solana", "sol"],
    "ADA": ["cardano", "ada"],
    "XRP": ["xrp", "ripple"],
    "DOGE": ["dogecoin", "doge"],
    "DOT": ["polkadot", "dot"],
    "AVAX": ["avalanche", "avax"],
    "MATIC": ["polygon", "matic"],
    "LTC": ["litecoin", "ltc"],
    "LINK": ["chainlink", "link"],
}

HEADLINE_RX = re.compile(r"\s+")

class SentimentService:
    """
    Maintains rolling sentiment per asset base symbol using:
      - CryptoPanic news (if CRYPTOPANIC_TOKEN provided)
      - Twitter recent search (if TWITTER_BEARER provided)
    Text scoring via VADER → compound in [-1,1]. We aggregate per-asset over a window.
    """

    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
        self._last_pull: Dict[str, float] = {}
        # state: base -> [{"t": epoch, "score": float, "src": "news"|"tweet"}]
        self._events: Dict[str, List[Dict[str, Any]]] = {}
        # user may supply extra keywords at runtime
        self._keywords: Dict[str, List[str]] = dict(DEFAULT_KEYWORDS)

    def set_keywords(self, base: str, words: List[str]):
        self._keywords[base.upper()] = words

    def bases(self) -> List[str]:
        return sorted(self._keywords.keys())

    async def fetch_all(self):
        """Fetch and score for all configured bases."""
        bases = self.bases()
        # parallelize across bases
        async with httpx.AsyncClient(timeout=20.0) as client:
            tasks = [self._update_for_base(client, b) for b in bases]
            await asyncio.gather(*tasks, return_exceptions=True)
        self._prune_old()

    async def _update_for_base(self, client: httpx.AsyncClient, base: str):
        now = time.time()
        last = self._last_pull.get(base, 0.0)
        # limit pulls to at most once per minute per base
        if now - last < 60:
            return
        self._last_pull[base] = now

        events: List[Dict[str, Any]] = []
        kws = self._keywords.get(base, [base])

        # CryptoPanic
        if CRYPTOPANIC_TOKEN:
            try:
                news = await self._fetch_cryptopanic(client, kws)
                for h in news[:SENTIMENT_TOP_N]:
                    sc = self._score_text(h)
                    events.append({"t": now, "score": sc, "src": "news", "text": h})
            except Exception as e:
                log.info(f"CryptoPanic fetch error for {base}: {e}")

        # Twitter
        if TWITTER_BEARER:
            try:
                tweets = await self._fetch_twitter(client, kws)
                for t in tweets[:SENTIMENT_TOP_N]:
                    sc = self._score_text(t)
                    events.append({"t": now, "score": sc, "src": "tweet", "text": t})
            except Exception as e:
                log.info(f"Twitter fetch error for {base}: {e}")

        # if no sources configured, keep quiet; caller may fall back to 0.0 sentiment
        if events:
            buf = self._events.setdefault(base, [])
            buf.extend(events)
            # soft limit buffer size
            if len(buf) > 1000:
                del buf[:-600]

    async def _fetch_cryptopanic(self, client: httpx.AsyncClient, keywords: List[str]) -> List[str]:
        # CryptoPanic API: https://cryptopanic.com/developers/api/
        # Endpoint: GET /api/v1/posts/?auth={TOKEN}&currencies=BTC,ETH&kind=news&filter=rising
        qs = ",".join({k.upper() for k in keywords})
        url = f"https://cryptopanic.com/api/v1/posts/"
        params = {
            "auth": CRYPTOPANIC_TOKEN,
            "kind": "news",
            "filter": "rising",
            "currencies": qs,
            "public": "true",
        }
        r = await client.get(url, params=params)
        r.raise_for_status()
        data = r.json()
        headlines: List[str] = []
        for p in data.get("results", []):
            t = p.get("title") or ""
            if SENTIMENT_LANG and (p.get("language") or "").lower() not in ("", SENTIMENT_LANG):
                continue
            t = HEADLINE_RX.sub(" ", t).strip()
            if t:
                headlines.append(t)
        return headlines

    async def _fetch_twitter(self, client: httpx.AsyncClient, keywords: List[str]) -> List[str]:
        # Twitter API v2 recent search
        # Endpoint: GET /2/tweets/search/recent?query=...
        # Requires bearer token
        query = " OR ".join([f'("{k}") lang:{SENTIMENT_LANG}' for k in keywords])
        url = "https://api.twitter.com/2/tweets/search/recent"
        headers = {"Authorization": f"Bearer {TWITTER_BEARER}"}
        params = {
            "query": query,
            "max_results": "50",
            "tweet.fields": "lang",
        }
        r = await client.get(url, headers=headers, params=params)
        if r.status_code == 401:
            # invalid token → silent
            return []
        r.raise_for_status()
        j = r.json()
        out: List[str] = []
        for tw in j.get("data", []):
            if SENTIMENT_LANG and (tw.get("lang") or "").lower() != SENTIMENT_LANG:
                continue
            txt = HEADLINE_RX.sub(" ", tw.get("text") or "").strip()
            if txt:
                out.append(txt)
        return out

    def _score_text(self, text: str) -> float:
        # VADER compound ∈ [-1,1]
        try:
            sc = self.analyzer.polarity_scores(text)
            return float(sc.get("compound", 0.0))
        except Exception:
            return 0.0

    def aggregate(self) -> Dict[str, Dict[str, float]]:
        """
        Returns per-base rolling average and sample count over SENTIMENT_WINDOW_S.
        { base: {"score": float in [-1,1], "n": int } }
        """
        now = time.time()
        out: Dict[str, Dict[str, float]] = {}
        for base, evs in self._events.items():
            xs = [e["score"] for e in evs if now - e["t"] <= SENTIMENT_WINDOW_S]
            if not xs:
                out[base] = {"score": 0.0, "n": 0}
            else:
                out[base] = {"score": sum(xs) / len(xs), "n": len(xs)}
        return out

    def _prune_old(self):
        now = time.time()
        for base, evs in list(self._events.items()):
            self._events[base] = [e for e in evs if now - e["t"] <= (SENTIMENT_WINDOW_S * 3)]