# reporting/__init__.py
import csv
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger("Reporting")


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def save_trade_log_json(trades: List[Dict[str, Any]], path: str | Path) -> Path:
    """
    Persist executed trades to disk as JSON.
    Each trade dict should include at least:
      {"ts": ISO8601, "symbol": str, "side": "BUY"/"SELL", "qty": float, "price": float, "profit": float?}
    """
    out = Path(path)
    ensure_dir(out.parent)
    with out.open("w", encoding="utf-8") as f:
        json.dump(trades, f, indent=2)
    logger.info("Trade log (JSON) saved: %s (%d rows)", out, len(trades))
    return out


def save_trade_log_csv(trades: List[Dict[str, Any]], path: str | Path) -> Path:
    """
    Persist executed trades to disk as CSV. Flattens keys across all rows.
    """
    out = Path(path)
    ensure_dir(out.parent)
    if not trades:
        with out.open("w", newline="", encoding="utf-8") as f:
            f.write("ts,symbol,side,qty,price,profit\n")
        logger.info("Trade log (CSV) saved with header only: %s", out)
        return out

    # collect all keys seen
    keys: List[str] = []
    seen = set()
    for t in trades:
        for k in t.keys():
            if k not in seen:
                seen.add(k)
                keys.append(k)

    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(trades)

    logger.info("Trade log (CSV) saved: %s (%d rows)", out, len(trades))
    return out


def generate_basic_report(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Basic summary stats over a list of trades.
    """
    if not trades:
        return {
            "total_trades": 0,
            "wins": 0,
            "losses": 0,
            "win_rate": 0.0,
            "total_profit": 0.0,
            "avg_profit": 0.0,
        }

    profits = []
    wins = 0
    for t in trades:
        p = float(t.get("profit", 0.0))
        profits.append(p)
        if p > 0:
            wins += 1

    total = len(trades)
    total_profit = sum(profits)
    avg_profit = total_profit / total if total else 0.0
    losses = total - wins
    win_rate = wins / total if total else 0.0

    return {
        "total_trades": total,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "total_profit": total_profit,
        "avg_profit": avg_profit,
    }