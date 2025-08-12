import os, time, json, hashlib, threading, logging
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# -------------------- ENV --------------------
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "").strip()

SENTIMENT_ENABLED   = os.getenv("SENTIMENT_ENABLED", "1").lower() in ("1","true","yes")
SENTIMENT_SOURCE    = os.getenv("SENTIMENT_SOURCE", "finnhub").lower()  # "finnhub"
SENTIMENT_ASSETS    = [a.strip().upper() for a in os.getenv("SENTIMENT_ASSETS", "BTC,ETH,BNB,ADA,XRP,SOL").split(",") if a.strip()]
SENTIMENT_WINDOW_S  = int(os.getenv("SENTIMENT_WINDOW_S", "900"))       # rolling window for live aggregation
SENTIMENT_TOP_N     = int(os.getenv("SENTIMENT_TOP_N", "50"))           # max texts per cycle per asset
SENTIMENT_FLUSH_SEC = int(os.getenv("SENTIMENT_FLUSH_SEC", "30"))       # flush history buffer to disk
SENTIMENT_BACKFILL_DAYS = int(os.getenv("SENTIMENT_BACKFILL_DAYS", "2"))# days to backfill at startup

SENTIMENT_HISTORY_PATH = os.getenv("SENTIMENT_HISTORY_PATH", "data/sentiment_history.jsonl")

# -------------------- LOG --------------------
log = logging.getLogger("SentimentService")
_analyzer = SentimentIntensityAnalyzer()

# -------------------- In-memory stores --------------------
# Rolling live window (used for current scores displayed in /sentiment)
# {BASE: List[Tuple[timestamp, compound]]}
_window: Dict[str, List[Tuple[float, float]]] = defaultdict(list)

# Append-only buffer to be flushed to history JSONL
# Each entry is a dict written as single line JSON
_buffer_lock = threading.Lock()
_buffer: List[Dict[str, Any]] = []

# Set of seen ids for de-duplication across runtime (and after loading history)
_seen_ids: set = set()

# Allow dashboard to pass/override asset keywords
_keywords: Dict[str, List[str]] = {a: [a] for a in SENTIMENT_ASSETS}

def set_keywords(base: str, words: List[str]) -> None:
    _keywords[base.upper()] = [w for w in (words or []) if w]

# -------------------- Utils --------------------
def _clip(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x

def _to_prob(vader_compound: float) -> float:
    # Map [-1,1] -> [0,1]
    return _clip(0.5 + 0.5 * float(vader_compound), 0.0, 1.0)

def _now() -> float:
    return time.time()

def _mk_id(source: str, raw_id: Optional[str], url: Optional[str], title: str) -> str:
    base = f"{source}|{raw_id or ''}|{url or ''}|{title}".encode("utf-8", "ignore")
    return hashlib.sha256(base).hexdigest()

def _ensure_dir(path: str):
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)

# -------------------- History I/O --------------------
def _append_history(row: Dict[str, Any]) -> None:
    """Add a row to memory buffer; background flusher writes it to disk."""
    with _buffer_lock:
        _buffer.append(row)

def _flush_history():
    """Write buffered rows to JSONL."""
    if not _buffer:
        return
    _ensure_dir(SENTIMENT_HISTORY_PATH)
    # take snapshot
    with _buffer_lock:
        snap = list(_buffer)
        _buffer.clear()
    # append
    try:
        with open(SENTIMENT_HISTORY_PATH, "a", encoding="utf-8") as f:
            for row in snap:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception as e:
        log.error(f"Sentiment history flush error: {e}")

def _load_history(max_days: int = 30) -> None:
    """Bootstrap from history file; repopulate window + seen ids."""
    if not os.path.isfile(SENTIMENT_HISTORY_PATH):
        return
    cutoff = _now() - max_days * 86400
    try:
        with open(SENTIMENT_HISTORY_PATH, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    row = json.loads(line)
                    ts = float(row.get("ts", 0))
                    if ts >= cutoff:
                        base = str(row.get("base", "")).upper()
                        comp = float(row.get("compound", 0))
                        _window[base].append((ts, comp))
                    mid = row.get("id")
                    if mid:
                        _seen_ids.add(mid)
                except Exception:
                    continue
    except Exception as e:
        log.error(f"Sentiment history load error: {e}")

def _trim_window(now_ts: float) -> None:
    cutoff = now_ts - SENTIMENT_WINDOW_S
    for base, arr in _window.items():
        # keep only within window
        _window[base] = [(t, c) for (t, c) in arr if t >= cutoff]

# -------------------- Providers --------------------
def _fetch_from_finnhub(assets: List[str], backfill: Optional[Tuple[str, str]] = None) -> Dict[str, List[Dict[str, Any]]]:
    """
    Returns {BASE: [news_item, ...]}
    news_item: {title, summary, url, source, ts, id?}
    If backfill=(from_date, to_date) use YYYY-MM-DD strings.
    """
    if not FINNHUB_API_KEY:
        log.warning("FINNHUB_API_KEY missing; provider will return empty.")
        return {a: [] for a in assets}
    try:
        from sentiment.providers.finnhub_provider import fetch_news
    except Exception as e:
        log.error(f"Finnhub provider import error: {e}")
        return {a: [] for a in assets}
    return fetch_news(assets, FINNHUB_API_KEY, backfill=backfill)

def _source_fetch(assets: List[str], backfill: Optional[Tuple[str, str]] = None) -> Dict[str, List[Dict[str, Any]]]:
    if SENTIMENT_SOURCE == "finnhub":
        return _fetch_from_finnhub(assets, backfill=backfill)
    return {a: [] for a in assets}

# -------------------- Core public API --------------------
def run_cycle() -> Dict[str, Dict[str, float]]:
    """
    Pull new items (no backfill), score, append to window/history (dedup),
    return snapshot as {BASE: {score, n}} with score in [-1, 1].
    """
    if not SENTIMENT_ENABLED:
        return {a: {"score": 0.0, "n": 0} for a in SENTIMENT_ASSETS}

    assets = sorted(set(list(_keywords.keys()) + SENTIMENT_ASSETS))
    now_ts = _now()
    out: Dict[str, Dict[str, float]] = {}

    # fetch latest (no backfill)
    texts_by_asset = _source_fetch(assets)

    for base, items in texts_by_asset.items():
        if not items:
            continue
        # score top-N
        count = 0
        for it in items:
            if count >= SENTIMENT_TOP_N:
                break
            title = (it.get("title") or "").strip()
            if not title:
                continue
            nid = _mk_id(it.get("source", "finnhub"), it.get("id"), it.get("url"), title)
            if nid in _seen_ids:
                continue
            _seen_ids.add(nid)

            vs = _analyzer.polarity_scores(title)
            comp = float(vs.get("compound", 0.0))

            # update window
            _window[base].append((now_ts, comp))

            # queue for history
            _append_history({
                "id": nid,
                "ts": now_ts,
                "base": base,
                "title": title,
                "url": it.get("url"),
                "source": it.get("source", "finnhub"),
                "compound": comp
            })
            count += 1

    _trim_window(now_ts)

    # aggregate per base
    for base, arr in _window.items():
        if not arr:
            out[base] = {"score": 0.0, "n": 0}
            continue
        vals = [c for (_, c) in arr]
        avg = sum(vals) / max(1, len(vals))
        out[base] = {"score": avg, "n": len(vals)}
    return out

def aggregate_probs() -> Dict[str, float]:
    snap = run_cycle()
    return {base: _to_prob(v["score"]) for base, v in snap.items()}

def snapshot() -> Dict[str, Any]:
    # return a richer object for the UI
    snap = run_cycle()
    return {
        "enabled": SENTIMENT_ENABLED,
        "source": SENTIMENT_SOURCE,
        "window_sec": SENTIMENT_WINDOW_S,
        "scores": snap
    }

# -------------------- Backfill & flusher threads --------------------
def _flusher_daemon():
    while True:
        try:
            _flush_history()
        except Exception as e:
            log.error(f"Sentiment flusher error: {e}")
        time.sleep(max(5, SENTIMENT_FLUSH_SEC))

def _backfill_startup(days: int):
    # Build YYYY-MM-DD range (UTC)
    import datetime as dt
    to_dt = dt.datetime.utcnow().date()
    from_dt = to_dt - dt.timedelta(days=max(0, int(days)))
    backfill = (from_dt.isoformat(), to_dt.isoformat())

    assets = sorted(set(list(_keywords.keys()) + SENTIMENT_ASSETS))
    news = _source_fetch(assets, backfill=backfill)
    now_ts = _now()

    added = 0
    for base, items in news.items():
        for it in items:
            title = (it.get("title") or "").strip()
            if not title:
                continue
            nid = _mk_id(it.get("source", "finnhub"), it.get("id"), it.get("url"), title)
            if nid in _seen_ids:
                continue
            _seen_ids.add(nid)
            # score
            vs = _analyzer.polarity_scores(title)
            comp = float(vs.get("compound", 0.0))
            # push to window (use its original ts if present)
            ts = float(it.get("ts") or now_ts)
            _window[base].append((ts, comp))
            # queue for history
            _append_history({
                "id": nid, "ts": ts, "base": base, "title": title,
                "url": it.get("url"), "source": it.get("source", "finnhub"),
                "compound": comp
            })
            added += 1
    log.info(f"Sentiment backfill added {added} items from last {days} days.")

def start_background():
    """Call this once at API startup."""
    # load recent history (30 days cap) and keep “live” window consistent
    _load_history(max_days=max(7, SENTIMENT_BACKFILL_DAYS))
    # optional backfill (fresh pull)
    if SENTIMENT_ENABLED and SENTIMENT_SOURCE == "finnhub" and FINNHUB_API_KEY:
        try:
            if SENTIMENT_BACKFILL_DAYS > 0:
                threading.Thread(target=_backfill_startup, args=(SENTIMENT_BACKFILL_DAYS,), daemon=True).start()
        except Exception as e:
            log.error(f"Sentiment backfill error: {e}")
    # start flusher
    threading.Thread(target=_flusher_daemon, daemon=True).start()