#!/usr/bin/env python3
"""
Generate Render-friendly env vars:
  SENTIMENT_KW_<ASSET>="<comma-separated keywords>"

Usage:
  pip install ccxt
  python generate_all_sentiment_vars.py > sentiment_vars.env

Options (env vars before running):
  INCLUDE_STABLES=1        # include stablecoins (default 0 = exclude)
  ONLY_SPOT=1              # only spot markets (default 1)
  TOP_BY_VOLUME=0          # 0 = all assets (default), or N (e.g., 200) to limit to top N by 24h quote volume
"""

import os
import ccxt
from collections import defaultdict

INCLUDE_STABLES = os.getenv("INCLUDE_STABLES", "0").lower() in ("1","true","yes")
ONLY_SPOT       = os.getenv("ONLY_SPOT", "1").lower() in ("1","true","yes")
TOP_BY_VOLUME   = int(os.getenv("TOP_BY_VOLUME", "0"))  # 0 = all

# Customize stablecoins list as you wish
STABLES = {"USDT","USDC","BUSD","TUSD","USDP","DAI","FDUSD","EUR","TRY","BRL","BIDR","AUD","GBP","RUB","UAH","ZAR","ARS","NGN","VAI"}

def kw(asset: str) -> list:
    """
    Build a rich keyword set for a given asset symbol.
    We'll add multiple formats so news/Twitter APIs catch most mentions.
    """
    a = asset.lower()
    return list(dict.fromkeys([
        a,
        f"{a}-usdt", f"{a}/usdt", f"{a}usdt",
        f"{a}-usd",  f"{a}/usd",  f"{a}usd",
        f"{a} price", f"{a} crypto", f"{a} coin", f"{a} token",
        f"#{a}",
    ]))

def safe_join(parts):
    # Ensure no quotes inside values; Render env editor likes plain strings
    s = ", ".join(parts)
    return s.replace('"', "'")

def main():
    ex = ccxt.binance()
    ex.load_markets()

    # Gather assets + basic volumes to optionally rank
    base_assets = set()
    quote_assets = set()
    asset_volume = defaultdict(float)  # rough 24h quoteVolume tally by base

    for sym, m in ex.markets.items():
        if not m.get("active", True):
            continue
        if ONLY_SPOT and not m.get("spot", False):
            continue

        base = m["base"]
        quote = m["quote"]

        # exclude stables if requested
        if not INCLUDE_STABLES:
            if base in STABLES:
                continue
            if quote in STABLES:
                # keep base (tradable) but don't add quote to sentiment assets
                pass

        base_assets.add(base)
        quote_assets.add(quote)

        # accumulate quote volume to roughly rank popularity importance
        try:
            qv = float(m.get("info", {}).get("quoteVolume", 0.0))
        except Exception:
            qv = 0.0
        asset_volume[base] += qv

    # If TOP_BY_VOLUME set, keep only the top-N bases by summed quote volume
    assets = sorted(base_assets)
    if TOP_BY_VOLUME > 0:
        assets = [a for a,_ in sorted(asset_volume.items(), key=lambda x: x[1], reverse=True)[:TOP_BY_VOLUME]]

    # Build keywords; add baseId (Binance internal) when present for extra recall
    # Also add a few cross-pair generic forms.
    printed = set()
    for asset in assets:
        # enrich with baseId if it looks meaningful
        # (Binance's baseId is sometimes identical to lower symbol; harmless to include)
        lower_id = None
        for m in ex.markets.values():
            if m.get("base") == asset:
                lower_id = str(m.get("baseId") or "").lower() or None
                break

        words = kw(asset)
        if lower_id and lower_id != asset.lower():
            words.append(lower_id)

        # extra generics
        a = asset.lower()
        words.extend([
            f"{a} pair", f"{a} trading",
            f"{a} news", f"{a} analysis",
        ])

        # dedupe while preserving order
        words = list(dict.fromkeys([w.strip() for w in words if w.strip()]))

        line = f'SENTIMENT_KW_{asset}="{safe_join(words)}"'
        if line not in printed:
            print(line)
            printed.add(line)

if __name__ == "__main__":
    main()
