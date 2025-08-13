#!/usr/bin/env python3
"""
Check which SENTIMENT_KW_<ASSET> env vars are missing/weak, prioritized by:
1) assets in your current live positions (/status), and
2) (optionally) top-N assets by 24h volume on Binance spot.

Outputs:
 - A human-readable report to stdout
 - A patch file with auto-suggested env lines for anything missing

Dependencies:
  pip install ccxt python-dotenv (dotenv optional if you use --env-file)

Examples:
  python check_sentiment_env.py --api https://bottie-1.onrender.com \
                                --env-file sentiment_vars.env \
                                --top 250 --include-stables 0

  python check_sentiment_env.py --env-file .env.render > report.txt
"""

import argparse
import os
import re
import sys
from collections import defaultdict
from typing import Dict, List, Set, Tuple

# Optional imports guarded
try:
    import requests
except Exception:
    requests = None

try:
    from dotenv import dotenv_values
except Exception:
    dotenv_values = None

try:
    import ccxt
except Exception:
    ccxt = None


STABLES = {
    "USDT","USDC","BUSD","TUSD","USDP","FDUSD","DAI","EUR","TRY","BRL",
    "BIDR","AUD","GBP","RUB","UAH","ZAR","ARS","NGN","VAI"
}

def parse_args():
    ap = argparse.ArgumentParser(description="Check SENTIMENT_KW_<ASSET> coverage.")
    ap.add_argument("--api", default=os.getenv("DASHBOARD_API", "").strip(),
                    help="Your backend base URL (e.g. https://bottie-1.onrender.com) to prioritize assets from /status.")
    ap.add_argument("--env-file", default=os.getenv("ENV_FILE", "").strip(),
                    help="Path to a local env file (KEY=VALUE lines). If omitted, uses current process env.")
    ap.add_argument("--include-stables", type=int, default=int(os.getenv("INCLUDE_STABLES", "0")),
                    help="1 to include stablecoins in assets to cover (default 0).")
    ap.add_argument("--top", type=int, default=int(os.getenv("TOP_BY_VOLUME", "0")),
                    help="Top-N bases by 24h quote volume to include (0 = all).")
    ap.add_argument("--patch-out", default=os.getenv("PATCH_OUT", "sentiment_vars_missing.env"),
                    help="Where to write auto-suggested lines for missing assets.")
    ap.add_argument("--timeout", type=float, default=float(os.getenv("HTTP_TIMEOUT", "8.0")),
                    help="HTTP timeout for API calls.")
    return ap.parse_args()

def load_env_dict(path: str) -> Dict[str,str]:
    """
    Load env vars from a file if provided, else from os.environ.
    Accepts lines of form KEY="value" or KEY=value; ignores blank/comment lines.
    """
    if path:
        if dotenv_values is not None:
            vals = dotenv_values(path)
            # dotenv returns a dict with raw strings; normalize to str
            return {k: (v if v is not None else "") for k,v in vals.items()}
        # Fallback: simple parser
        env = {}
        with open(path, "r", encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if not ln or ln.startswith("#"):
                    continue
                m = re.match(r'^([A-Za-z0-9_]+)=(.*)$', ln)
                if not m:
                    continue
                k, v = m.group(1), m.group(2).strip()
                # strip surrounding quotes if present
                if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                    v = v[1:-1]
                env[k] = v
        return env
    # default to current process env
    return dict(os.environ)

def fetch_positions_assets(api_base: str, timeout: float=8.0) -> Set[str]:
    """
    Hit /status to discover which assets you hold (prioritization).
    Returns asset tickers (BASE symbols), e.g., {"BTC","ETH"}.
    """
    out: Set[str] = set()
    if not api_base or requests is None:
        return out
    try:
        r = requests.get(f"{api_base.rstrip('/')}/status", timeout=timeout)
        if r.ok:
            data = r.json()
            positions = data.get("positions") or {}
            for sym, pos in positions.items():
                # sym like "BTC/USDT" -> take base
                if isinstance(sym, str) and "/" in sym:
                    base = sym.split("/")[0].strip().upper()
                    if base:
                        out.add(base)
    except Exception:
        pass
    return out

def kw(asset: str) -> List[str]:
    a = asset.lower()
    return list(dict.fromkeys([
        a,
        f"{a}-usdt", f"{a}/usdt", f"{a}usdt",
        f"{a}-usd", f"{a}/usd", f"{a}usd",
        f"{a} price", f"{a} crypto", f"{a} coin", f"{a} token",
        f"#{a}",
        f"{a} pair", f"{a} trading",
        f"{a} news", f"{a} analysis",
    ]))

def gather_binance_bases(include_stables: bool, top_n: int) -> List[str]:
    if ccxt is None:
        return []
    ex = ccxt.binance()
    ex.load_markets()
    bases: Set[str] = set()
    vol = defaultdict(float)

    for m in ex.markets.values():
        if not m.get("active", True):
            continue
        if not m.get("spot", False):
            continue
        base = m.get("base")
        quote = m.get("quote")
        if not include_stables and (base in STABLES or quote in STABLES):
            # Skip pairs involving stables unless explicitly included
            continue
        if base:
            bases.add(base)
            try:
                qv = float(m.get("info", {}).get("quoteVolume", 0.0))
            except Exception:
                qv = 0.0
            vol[base] += qv

    if top_n and top_n > 0:
        ranked = [a for a,_ in sorted(vol.items(), key=lambda x: x[1], reverse=True)[:top_n]]
        # Ensure we don't accidentally drop an empty set
        return ranked or list(sorted(bases))
    return list(sorted(bases))

def inspect_env(env: Dict[str,str], assets: List[str]) -> Tuple[List[str], List[str], Dict[str, List[str]]]:
    """
    Returns:
      missing: assets with no env var
      weak: assets whose value has < 3 comma-separated items
      parsed: asset -> list of keywords (for info)
    """
    missing, weak = [], []
    parsed: Dict[str, List[str]] = {}
    for a in assets:
        key = f"SENTIMENT_KW_{a}"
        val = env.get(key, "").strip()
        if not val:
            missing.append(a)
            continue
        items = [x.strip() for x in val.split(",") if x.strip()]
        parsed[a] = items
        if len(items) < 3:
            weak.append(a)
    return missing, weak, parsed

def suggest_line(asset: str, markets=None) -> str:
    # try to add baseId if meaningful
    base_id = None
    if markets:
        for m in markets.values():
            if m.get("base") == asset:
                base_id = (m.get("baseId") or "").lower()
                if base_id == asset.lower():
                    base_id = None
                break
    items = kw(asset)
    if base_id:
        items.append(base_id)
    # de-dupe
    items = list(dict.fromkeys(items))
    # Render-friendly: no inner double-quotes
    value = ", ".join(items).replace('"', "'")
    return f'SENTIMENT_KW_{asset}="{value}"'

def main():
    args = parse_args()

    # Load env vars
    env = load_env_dict(args.env_file)

    # Discover assets to check
    prioritized = fetch_positions_assets(args.api, timeout=args.timeout)
    markets = None
    binance_assets = []
    if ccxt is not None:
        ex = ccxt.binance()
        ex.load_markets()
        markets = ex.markets
        binance_assets = gather_binance_bases(args.include_stables == 1, args.top)

    # union (prioritized first)
    all_assets = list(dict.fromkeys(list(prioritized) + binance_assets))

    if not all_assets:
        print("No assets discovered. (Hint: provide --api and/or install ccxt for Binance markets.)", file=sys.stderr)
        sys.exit(2)

    # Inspect
    missing, weak, parsed = inspect_env(env, all_assets)

    # Report
    print("\n=== SENTIMENT ENV COVERAGE REPORT ===\n")
    print(f"Assets from /status (prioritized): {sorted(prioritized) if prioritized else '—'}")
    print(f"Assets from Binance (spot, filtered): {len(binance_assets)}")
    print(f"Total checked: {len(all_assets)}")
    print(f"Missing: {len(missing)}")
    print(f"Weak (<3 items): {len(weak)}\n")

    if missing:
        print("Missing variables (examples):")
        preview = missing[:20]
        print(", ".join(preview) + (" ..." if len(missing) > 20 else ""))
        print()

    if weak:
        print("Weak variables:", ", ".join(weak[:50]) + (" ..." if len(weak) > 50 else ""))
        print()

    # Write patch file
    patch_path = args.patch_out
    with open(patch_path, "w", encoding="utf-8") as f:
        for asset in missing:
            f.write(suggest_line(asset, markets) + "\n")

    print(f"Suggested lines for ALL missing assets written to: {patch_path}")
    print("Paste that file into Render → Environment → (bulk add).")
    print("\nDone.\n")

if __name__ == "__main__":
    main()
