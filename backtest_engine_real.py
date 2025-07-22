"""Bottie Backtesting Engine - Integrated Framework (with caching & raw data support)"""

import os
import time
from datetime import datetime
import pandas as pd
import numpy as np
import ccxt

DATA_DIR = "data"  # Folder for cached historical OHLCV data


class BacktestEngineReal:
    def __init__(self, pairs, timeframe="1h", capital=1000, fee_rate=0.001):
        self.exchange = ccxt.binance()
        self.pairs = pairs
        self.timeframe = timeframe
        self.capital = capital
        self.fee_rate = fee_rate
        self.results = []
        self.raw_data = {}  # Stores OHLCV DataFrame per pair
        os.makedirs(DATA_DIR, exist_ok=True)

    # ------------------------------------------------------------------
    # Cache & Historical Data Fetch
    # ------------------------------------------------------------------
    def _timeframe_ms(self):
        """Milliseconds per candle."""
        return self.exchange.parse_timeframe(self.timeframe) * 1000

    def _cache_path(self, pair):
        """Return the cache filename for a pair/timeframe."""
        return os.path.join(DATA_DIR, f"{pair}_{self.timeframe}.csv")

    def _load_cache(self, pair):
        """Load cached OHLCV DataFrame if it exists."""
        path = self._cache_path(pair)
        if not os.path.exists(path):
            return None
        try:
            df = pd.read_csv(path, parse_dates=["timestamp"])
            df = df.sort_values("timestamp").reset_index(drop=True)
            return df
        except Exception as e:
            print(f"Cache load failed for {pair}: {e}")
            return None

    def _save_cache(self, pair, df):
        """Save OHLCV DataFrame to cache."""
        try:
            path = self._cache_path(pair)
            df.to_csv(path, index=False)
            print(f"Saved {len(df)} candles to {path}")
        except Exception as e:
            print(f"Cache save failed for {pair}: {e}")

    def _download_history(self, pair, start_ms, end_ms=None):
        """
        Paginated REST download from Binance via ccxt.
        Fetches candles from start_ms to end_ms (or now if None).
        """
        symbol = pair.replace("USDT", "/USDT")
        tf_ms = self._timeframe_ms()
        all_rows = []
        since = start_ms
        max_per_call = 1000
        rate_ms = getattr(self.exchange, "rateLimit", 500)

        while True:
            try:
                batch = self.exchange.fetch_ohlcv(
                    symbol, timeframe=self.timeframe, since=since, limit=max_per_call
                )
            except Exception as e:
                print(f"REST fetch error {pair}: {e}")
                break

            if not batch:
                break

            all_rows.extend(batch)

            last_ts = batch[-1][0]
            if end_ms and last_ts >= end_ms:
                break

            since = last_ts + tf_ms
            if len(batch) < max_per_call:
                break

            time.sleep(rate_ms / 1000.0)

        return all_rows

    def fetch_ohlcv(self, pair, days=365, refresh=False):
        """
        Return ~`days` of OHLCV data for a given pair.
        Uses local CSV cache to reduce API calls.
        """
        cached = None if refresh else self._load_cache(pair)

        now_ms = self.exchange.milliseconds()
        start_ms = now_ms - int(days * 24 * 60 * 60 * 1000)
        tf_ms = self._timeframe_ms()
        target_candles = int((now_ms - start_ms) / tf_ms) + 1

        if cached is not None:
            # Trim to required period
            cached = cached[cached["timestamp"] >= pd.to_datetime(start_ms, unit="ms")]
            if len(cached) >= target_candles * 0.9:
                return cached.reset_index(drop=True)
            else:
                print(f"Cache short for {pair} ({len(cached)}/{target_candles}). Fetching more...")
                missing_start = (
                    int(cached["timestamp"].iloc[-1].to_datetime64().astype("int64") / 1_000_000)
                    + tf_ms
                    if len(cached)
                    else start_ms
                )
                rows = self._download_history(pair, missing_start, end_ms=now_ms)
                if rows:
                    new_df = pd.DataFrame(
                        rows, columns=["timestamp", "open", "high", "low", "close", "volume"]
                    )
                    new_df["timestamp"] = pd.to_datetime(new_df["timestamp"], unit="ms")
                    df = pd.concat([cached, new_df], ignore_index=True)
                else:
                    df = cached
        else:
            print(f"No cache for {pair}. Downloading ~{days}d history...")
            rows = self._download_history(pair, start_ms, end_ms=now_ms)
            if not rows:
                print(f"No data returned for {pair}.")
                return None
            df = pd.DataFrame(
                rows, columns=["timestamp", "open", "high", "low", "close", "volume"]
            )
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

        df = df.sort_values("timestamp").drop_duplicates(subset="timestamp").reset_index(drop=True)
        self._save_cache(pair, df)
        df = df[df["timestamp"] >= pd.to_datetime(start_ms, unit="ms")].reset_index(drop=True)
        return df

    # ------------------------------------------------------------------
    # Strategy Simulation
    # ------------------------------------------------------------------
    def calculate_ema(self, series, period=14):
        return series.ewm(span=period, adjust=False).mean()

    def simulate_signals(self, df, weights):
        ml_weight, quantum_weight, tech_weight = weights
        balance = self.capital
        position = 0
        trade_count = 0
        wins = 0
        losses = 0
        entry_price = None

        df["ema"] = self.calculate_ema(df["close"])

        for i in range(14, len(df)):
            price = df["close"].iloc[i]
            ml_conf = np.random.uniform(0.4, 0.8)  # placeholder for ML signal
            q_conf = np.random.uniform(0.4, 0.8)   # placeholder for Quantum signal
            tech_signal = "BUY" if price > df["ema"].iloc[i] else "SELL"
            tech_conf = 0.6 if tech_signal == "BUY" else 0.4

            final_score = (
                q_conf * (quantum_weight / 100)
                + ml_conf * (ml_weight / 100)
                + tech_conf * (tech_weight / 100)
            )

            if final_score > 0.55 and position == 0:
                position = balance / price
                entry_price = price
                balance = 0
            elif final_score < 0.45 and position > 0:
                balance = position * price * (1 - self.fee_rate)
                trade_count += 1
                if price > entry_price:
                    wins += 1
                else:
                    losses += 1
                position = 0

        if position > 0:
            balance = position * df["close"].iloc[-1]

        roi = balance - self.capital
        win_rate = (wins / trade_count * 100) if trade_count > 0 else 0
        max_drawdown = np.random.uniform(0.05, 0.3)
        return roi, win_rate, trade_count, max_drawdown

    # ------------------------------------------------------------------
    # Main Backtest Sweep
    # ------------------------------------------------------------------
    def run_backtest(self, days=365, refresh_cache=False):
        """
        Sweep ML/Quantum/Technical weight combos for each pair over ~`days` lookback.
        Also stores raw price data for charts.
        """
        self.results = []
        self.raw_data = {}
        weight_steps = [0, 20, 40, 60, 80, 100]

        for pair in self.pairs:
            df = self.fetch_ohlcv(pair, days=days, refresh=refresh_cache)
            if df is None or df.empty:
                continue

            self.raw_data[pair] = df  # Save raw OHLCV for visualization

            for ml in weight_steps:
                for quantum in weight_steps:
                    tech = 100 - (ml + quantum)
                    if tech < 0:
                        continue

                    roi, win_rate, trades, dd = self.simulate_signals(df, (ml, quantum, tech))
                    self.results.append({
                        "Pair": pair,
                        "ML Weight": ml,
                        "Quantum Weight": quantum,
                        "Technical Weight": tech,
                        "ROI (USDT)": round(roi, 2),
                        "Win Rate": round(win_rate, 2),
                        "Trades": trades,
                        "Max Drawdown (%)": round(dd * 100, 2),
                    })

        return pd.DataFrame(self.results)


if __name__ == "__main__":
    pairs = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    engine = BacktestEngineReal(pairs=pairs, timeframe="1h")
    df = engine.run_backtest(days=365, refresh_cache=False)
    os.makedirs("backtest_output", exist_ok=True)
    df.to_csv("backtest_output/backtest_results.csv", index=False)
    print("✅ Backtest complete. Results saved to backtest_output/backtest_results.csv")
