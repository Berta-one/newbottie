# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Hybrid Quantum Crypto Trading Bot (Final)
=======================================
Consolidated, deploymentfriendly Streamlit application that brings together:

 Authentication gate (envdriven password)
 Portfolio + trade history + GBP conversions
 Performance analytics (last 100 trades, PnL)
 MultiStrategy market scanner (Quantum + ML + Technical)
 AutoTrader controls + background scanner thread
 Manual Trade ticket
 Historical Backtesting (w/ ccxt, 1y cache) *no weightapply buttons*
 System Health dashboard (CPU/Mem/Threads)
 Settings (risk, strategy, notifications, etc.)
 Live log view

Robust import/fallback pattern lets the app run even when some modules or API
keys are missing. Designed to operate on Railway (or local)  handles the $PORT
injection that Railway provides and prevents the Streamlit autoport error.

***IMPORTANT***
- Requires Python 3.9+ (3.12 OK) and Streamlit 1.32+.
- For live Binance trading set BINANCE_API_KEY / BINANCE_API_SECRET env vars.
- USE_TESTNET="true" to route to Binance Testnet (safety default recommended when first running!).
- For Railway, do *not* pass --server.port=$PORT literally; allow the platform to inject PORT env.

Author: Bottie Build (ChatGPT assist)
"""
from portfolio_value_fix import get_unified_portfolio_value, debug_portfolio_calculation
from quantum_trader import quantum_trader

import os
import sys
import time
import threading
import traceback
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import psutil
import streamlit as st

# Unified _display_logs function
def _display_logs(limit=50, log_file=None, refresh_interval=None):
    """
    Display recent logs in the Streamlit dashboard.
    If log_file is provided, display from file; otherwise, use session logs.
    If refresh_interval is set, auto-refreshes every `refresh_interval` seconds.
    """
    logs = []

    if log_file:
        if not os.path.exists(log_file):
            st.info("No logs available yet.")
            return
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                logs = lines[-limit:] if limit else lines
        except Exception as e:
            st.error(f"Error reading logs: {e}")
            return
    else:
        logs = st.session_state.get("logs", [])
        logs = logs[-limit:] if limit else logs

    logs = list(reversed(logs))

    for log in logs:
        if "ERROR" in log or "FAIL" in log:
            st.error(log)
        elif "WARNING" in log:
            st.warning(log)
        elif "SUCCESS" in log or "..." in log:
            st.success(log)
        else:
            st.text(log)

    # Optional: auto-refresh with refresh_interval
    if refresh_interval is not None:
        time.sleep(refresh_interval)
        st.experimental_rerun()

# Add these lines at the top of hybrid_bot.py (around line 10-20)
from portfolio_value_fix import get_unified_portfolio_value, debug_portfolio_calculation
from quantum_trader import quantum_trader

# ------------------------------------------------------------------
# Streamlit page config must happen *early*.
# ------------------------------------------------------------------
st.set_page_config(
    page_title="Hybrid Quantum Trading Bot",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------------
# ENV / Railway PORT PATCH
# ------------------------------------------------------------------
# Railway injects $PORT. Streamlit reads STREAMLIT_SERVER_PORT; if it contains
# "$PORT" literal we must fix that or Streamlit errors out.
port_env = os.getenv("STREAMLIT_SERVER_PORT", "")
if port_env == "$PORT" and "PORT" in os.environ:
    os.environ["STREAMLIT_SERVER_PORT"] = os.environ["PORT"]
    os.environ.setdefault("STREAMLIT_SERVER_ADDRESS", "0.0.0.0")

# ------------------------------------------------------------------
# Authentication -----------------------------------------------------------------
# A lightweight password gate. Provide DASHBOARD_PASSWORD env var.
# ---------------------------------------------------------------------------------

def require_authentication() -> bool:
    """Return True once the user passes the password gate.

    Uses st.session_state.authenticated.
    """
    if st.session_state.get("authenticated", False):
        return True

    pw_env = os.getenv("DASHBOARD_PASSWORD", "")
    if pw_env == "":
        # No password configured  authenticate automatically (dev mode)
        st.session_state.authenticated = True
        return True

    st.warning(" Enter dashboard password to continue.")
    pw = st.text_input("Password", type="password", key="_auth_pw")
    if st.button("Login", key="_auth_btn"):
        if pw == pw_env:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error(" Incorrect password.")
    st.stop()  # Halt until authenticated

# Enforce auth now (stops script if not passed)
require_authentication()

# ------------------------------------------------------------------
# Notification stubs (override if your notifications.py present)
# ------------------------------------------------------------------
try:
    from notifications import (
        get_notification_system,
        notify_system,
        notify_error,
        notify_trade,
        notify_trade_close,
        notify_signal,
        send_test_notification,
        get_notification_status,
    )  # type: ignore
    _notify_stub = False
except Exception:  # noqa: BLE001
    _notify_stub = True

    def get_notification_status():  # noqa: D401
        return {
            "enabled": False,
            "configured": False,
            "types": {"trades": False, "signals": False, "system": False, "errors": False},
            "emails_sent_hour": 0,
            "queue_size": 0,
            "to_emails": [],
        }

    def notify_system(evt, msg):  # noqa: ARG001
        print(f"[NOTIFY_SYSTEM] {evt}: {msg}")

    def notify_error(ctx, err, extra=None):  # noqa: ARG001
        print(f"[NOTIFY_ERROR] {ctx}: {err} :: {extra}")

    def notify_trade(data):  # noqa: ARG001
        print(f"[NOTIFY_TRADE] {data}")

    def notify_trade_close(data):  # noqa: ARG001
        print(f"[NOTIFY_TRADE_CLOSE] {data}")

    def notify_signal(data):  # noqa: ARG001
        print(f"[NOTIFY_SIGNAL] {data}")

    def send_test_notification():
        print("[NOTIFY_TEST] Sent.")
        return True


# ------------------------------------------------------------------
# Safe dynamic imports for optional modules
# ------------------------------------------------------------------
IMPORT_TARGETS = [
    ("portfolio_manager", "PortfolioManager"),
    ("trade_executor", "TradeExecutor"),
    ("risk_manager", "RiskManager"),
    ("position_monitor", "PositionMonitor"),
    ("market_analyzer", "MarketAnalyzer"),
    ("quantum_trading_integration", "QuantumTrader"),
    ("quantum_trader", "QuantumTraderClass"),
    ("ensemble_signal_engine", "EnsembleSignalEngine"),
    ("advanced_market_intelligence", "AdvancedMarketIntelligence"),
    ("adaptive_risk_system", "AdaptiveRiskManager"),
    ("enhanced_ml_strategy", "MLEnhancedStrategy"),
    ("advanced_ml_strategy", "AdvancedMLStrategy"),
]

# Optional Backtesting integration
try:
    from backtesting_integration import BacktestingIntegration
    BACKTESTING_AVAILABLE = True
except Exception:
    BacktestingIntegration = None  # type: ignore
    BACKTESTING_AVAILABLE = False

MODULES: Dict[str, Any] = {}
QT_IMPORT_ERROR: Optional[str] = None
QT_STATUS: str = ""

for mod_path, cls_name in IMPORT_TARGETS:
    try:
        mod = __import__(mod_path, fromlist=[cls_name])
        MODULES[cls_name] = getattr(mod, cls_name)
    except Exception as e:  # noqa: BLE001
        MODULES[cls_name] = None
        print(f" Optional module {cls_name} not available: {e}")
        if cls_name == "QuantumTrader" and isinstance(e, ImportError):
            QT_IMPORT_ERROR = str(e)

# Binance Client import separately (often installed via python-binance)
try:
    from binance.client import Client  # type: ignore
except Exception:  # noqa: BLE001
    Client = None

# Quantum stack (prefer full, fallback math sim)
try:
    from quantum_engine import QuantumAnalyzer as QuantumAnalyzerFull
except Exception:
    QuantumAnalyzerFull = None

try:
    from quantum_engine_fallback import QuantumAnalyzer as QuantumAnalyzerFB
except Exception:
    QuantumAnalyzerFB = None

# Instantiate the preferred analyzer, fallback if necessary
if QuantumAnalyzerFull is not None:
    QuantumAnalyzer = QuantumAnalyzerFull
    print("Using QuantumAnalyzerFull")
elif QuantumAnalyzerFB is not None:
    QuantumAnalyzer = QuantumAnalyzerFB
    print("Using FallbackQuantumAnalyzer")
else:
    raise ImportError("No QuantumAnalyzer implementation available!")


# ------------------------------------------------------------------
# Fallback Implementations -------------------------------------------------------
# These keep the UI usable without live connections.
# ---------------------------------------------------------------------------------

class FallbackPortfolioManager:
    def __init__(self):
        self._live = False
        self._last_update = datetime.utcnow()
        self.portfolio = {
            "USDT": {"balance": 10000.0, "free": 10000.0, "locked": 0.0, "price": 1.0, "value": 10000.0, "change": 0.0},
            "BTC": {"balance": 0.2, "free": 0.2, "locked": 0.0, "price": 65000.0, "value": 13000.0, "change": 2.5},
            "ETH": {"balance": 1.0, "free": 1.0, "locked": 0.0, "price": 3000.0, "value": 3000.0, "change": 1.2},
        }

    def get_portfolio(self):
        return self.portfolio

    def total_value(self):
        return sum(v["value"] for v in self.portfolio.values())

    def last_updated(self):
        return self._last_update.strftime("%H:%M:%S")

    def refresh_portfolio(self):  # noqa: D401
        self._last_update = datetime.utcnow()
        return self.portfolio

    def is_live(self):  # noqa: D401
        return False

    def get_connection_status(self):  # noqa: D401
        return " Using demo data - Portfolio Manager not available"

    def get_trade_history(self, symbol=None, limit=10):  # noqa: ARG002,D401
        return [
            {"symbol": "BTCUSDT", "side": "BUY", "quantity": 0.0002, "price": 65000, "value": 13.0, "commission": 0.01, "time": "11:33:06"},
            {"symbol": "ETHUSDT", "side": "SELL", "quantity": 0.01, "price": 3000, "value": 30.0, "commission": 0.01, "time": "11:31:58"},
        ]


class FallbackMarketAnalyzer:
    def __init__(self, client=None):  # noqa: ARG002
        pass

    def get_trading_pairs(self):
        return [
            "BTCUSDT",
            "ETHUSDT",
            "BNBUSDT",
            "XRPUSDT",
            "ADAUSDT",
            "SOLUSDT",
            "DOTUSDT",
            "LINKUSDT",
            "AVAXUSDT",
            "MATICUSDT",
        ]

    def get_price(self, symbol):  # noqa: D401
        prices = {
            "BTCUSDT": 65000.0,
            "ETHUSDT": 3000.0,
            "BNBUSDT": 600.0,
            "XRPUSDT": 0.6,
            "ADAUSDT": 0.4,
            "SOLUSDT": 100.0,
        }
        return prices.get(symbol, 10.0)

    def get_latest_rsi(self, symbol):  # noqa: ARG002
        return float(np.random.uniform(25, 75))

    def get_latest_momentum(self, symbol):  # noqa: ARG002
        return float(np.random.uniform(-5, 5))

    def get_volatility(self, symbol):  # noqa: ARG002
        return float(np.random.uniform(0.02, 0.08))

    def analyze_market_signals(self, symbols):
        sigs = {}
        for s in symbols:
            rs = self.get_latest_rsi(s)
            conf = float(np.random.uniform(0.5, 0.9))
            sig = "BUY" if rs < 35 else "SELL" if rs > 65 else "HOLD"
            sigs[s] = {"signal": sig, "confidence": conf, "rsi": rs, "price": self.get_price(s)}
        return sigs


class FallbackQuantumAnalyzer:
    def generate_quantum_signal(self, market_data):  # noqa: ARG002
        return {
            "decision": np.random.choice(["BUY", "SELL", "HOLD"]),
            "confidence": float(np.random.uniform(0.5, 0.8)),
            "distribution": {"BUY": 0.4, "SELL": 0.3, "HOLD": 0.3},
        }


class FallbackTradeExecutor:
    def __init__(self, client=None, risk_mgr=None, log_callback=None):  # noqa: ARG002
        self.mock_balance = 10000.0
        self.log_callback = log_callback or (lambda msg: print(msg))

    def manual_trade(self, symbol, qty=None, sl_mult=1.5, tp_mult=3.0, trade_amount_usd=None):  # noqa: ARG002
        # Demo fills @ mock price
        mock_price = FallbackMarketAnalyzer().get_price(symbol)
        if trade_amount_usd is not None:
            qty = trade_amount_usd / mock_price
        if qty is None:
            qty = 10 / mock_price
        cost = qty * mock_price
        self.mock_balance -= cost
        msg = f"DEMO TRADE: {symbol} {qty:.8f} @ {mock_price:.4f} (${cost:.2f}) SLx{sl_mult} TPx{tp_mult}"
        self.log_callback(msg)
        return {
            "status": "DEMO",
            "message": msg,
            "symbol": symbol,
            "qty": qty,
            "price": mock_price,
            "usd": cost,
        }

    def auto_execute(self, signal, total_balance=None, open_positions=0, sl_mult=1.5, tp_mult=3.0):  # noqa: ARG002
        sym = signal.get("symbol", "BTCUSDT")
        return self.manual_trade(sym, trade_amount_usd=25.0, sl_mult=sl_mult, tp_mult=tp_mult)

    def get_active_orders(self):  # noqa: D401
        return {}

    def cancel_order(self, symbol):  # noqa: D401
        return f"DEMO CANCEL {symbol}"

    def get_connection_status(self):  # noqa: D401
        return f"DEMO Balance: ${self.mock_balance:.2f}"

    def get_account_summary(self):  # noqa: D401
        return {
            "total_usdt": self.mock_balance,
            "tradeable_usdt": self.mock_balance * 0.9,
            "can_trade": True,
            "demo_mode": True,
        }


class FallbackQuantumTrader:
    """Fallback quantum trader when Qiskit/QTrader is unavailable."""

    def __init__(self, client=None):  # noqa: D401,ARG002
        self.client = client
        self.analyzer = FallbackQuantumAnalyzer() if FallbackQuantumAnalyzer else None

    def evaluate_signal(self, market_data):  # noqa: ARG002
        if self.analyzer:
            return self.analyzer.generate_quantum_signal(market_data)
        return {"decision": "HOLD", "confidence": 0.0, "distribution": {}}

    def execute_quantum_trade(self, symbol, market_data, quantity):  # noqa: ARG002
        signal = self.evaluate_signal(market_data)
        return {"status": "DISABLED", "reason": "Quantum Trader unavailable", "signal": signal}

    def get_connection_status(self):  # noqa: D401
        return " Quantum Trader disabled (missing Qiskit)"


# ------------------------------------------------------------------
# Binance Client setup -----------------------------------------------------------
# ------------------------------------------------------------------

def setup_binance_client():
    if Client is None:
        return None, " Binance client library not installed"

    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    if not api_key or not api_secret:
        return None, " API keys not configured - demo mode"

    try:
        client = Client(api_key, api_secret)
        # Testnet?
        if os.getenv("USE_TESTNET", "false").lower() == "true":
            client.API_URL = "https://testnet.binance.vision/api"
        client.get_server_time()  # sanity call
        mode = " TESTNET" if os.getenv("USE_TESTNET", "false").lower() == "true" else " LIVE"
        return client, f"... Connected to Binance {mode}"
    except Exception as e:  # noqa: BLE001
        return None, f" Connection failed: {e}"

def adjust_quantity(symbol: str, qty: float, client) -> float:
    """Adjust quantity to comply with Binance LOT_SIZE filter."""
    try:
        info = client.get_symbol_info(symbol)
        if info and 'filters' in info:
            for f in info['filters']:
                if f['filterType'] == 'LOT_SIZE':
                    step_size = float(f['stepSize'])
                    # Determine precision from step size (e.g., 0.000001 -> 6 decimals)
                    precision = len(str(step_size).split('.')[-1].rstrip('0'))
                    return round(qty, precision)
    except Exception as e:
        print(f"[adjust_quantity] Error: {e}")
    return qty

# ------------------------------------------------------------------
# Component initialization -------------------------------------------------------
# ------------------------------------------------------------------

def initialize_components():
    comps: Dict[str, Any] = {}

    client, client_status = setup_binance_client()

    # Risk Manager ------------------------------------------------
    if MODULES.get("RiskManager") is not None:
        try:
            comps["risk_mgr"] = MODULES["RiskManager"](os.getenv("RISK_PROFILE", "BALANCED"))
        except Exception as e:  # noqa: BLE001
            print(f"RiskManager init failed: {e}")
            comps["risk_mgr"] = None
    else:
        comps["risk_mgr"] = None

    # Portfolio Manager -------------------------------------------
    portfolio_mgr = None
    if MODULES.get("PortfolioManager") and client:
        try:
            portfolio_mgr = MODULES["PortfolioManager"](api_key=os.getenv("BINANCE_API_KEY"), api_secret=os.getenv("BINANCE_API_SECRET"))
        except Exception as e:  # noqa: BLE001
            print(f"PortfolioManager failed: {e}")
    if portfolio_mgr is None:
        portfolio_mgr = FallbackPortfolioManager()
    comps["portfolio_mgr"] = portfolio_mgr

    # Market Analyzer --------------------------------------------
    market_analyzer = None
    if MODULES.get("MarketAnalyzer") and client:
        try:
            market_analyzer = MODULES["MarketAnalyzer"](client)
        except Exception as e:  # noqa: BLE001
            print(f"MarketAnalyzer failed: {e}")
    if market_analyzer is None:
        market_analyzer = FallbackMarketAnalyzer(client)
    comps["market_analyzer"] = market_analyzer

    # Trade Executor ---------------------------------------------
    trade_exec = None
    if MODULES.get("TradeExecutor") and client:
        try:
            trade_exec = MODULES["TradeExecutor"](client, comps["risk_mgr"], log_callback=_log_append)
        except Exception as e:  # noqa: BLE001
            print(f"TradeExecutor failed: {e}")
    if trade_exec is None:
        trade_exec = FallbackTradeExecutor(client, comps["risk_mgr"], log_callback=_log_append)
    comps["trade_exec"] = trade_exec

    # Quantum -----------------------------------------------------
    if MODULES.get("QuantumAnalyzer") is not None:
        try:
            comps["quantum_analyzer"] = MODULES["QuantumAnalyzer"]()
        except Exception as e:  # noqa: BLE001
            print(f"QuantumAnalyzer failed: {e}")
            if FallbackQuantumAnalyzer:
                comps["quantum_analyzer"] = FallbackQuantumAnalyzer()
            else:
                comps["quantum_analyzer"] = None
    else:
        if FallbackQuantumAnalyzer:
            comps["quantum_analyzer"] = FallbackQuantumAnalyzer()
        else:
            comps["quantum_analyzer"] = None

    # Quantum Trader wrapper -------------------------------------
    global QT_STATUS
    if MODULES.get("QuantumTrader") and client:
        try:
            comps["quantum_trader"] = MODULES["QuantumTrader"](client)
            QT_STATUS = "... Quantum Trader active"
        except Exception as e:  # noqa: BLE001
            print(f"QuantumTrader failed: {e}")
            QT_STATUS = f" Quantum Trader error: {e}"
            comps["quantum_trader"] = FallbackQuantumTrader(client)
    else:
        if QT_IMPORT_ERROR:
            QT_STATUS = f" Quantum Trader disabled - {QT_IMPORT_ERROR}"
        else:
            QT_STATUS = " Quantum Trader unavailable"
        comps["quantum_trader"] = FallbackQuantumTrader(client)

    # Ensemble Engine --------------------------------------------
    if MODULES.get("EnsembleSignalEngine") and client and comps["quantum_trader"]:
        try:
            comps["ensemble_engine"] = MODULES["EnsembleSignalEngine"](client, comps["quantum_trader"], market_analyzer)
        except Exception as e:  # noqa: BLE001
            print(f"EnsembleSignalEngine failed: {e}")
            comps["ensemble_engine"] = None
    else:
        comps["ensemble_engine"] = None

    return comps, client, client_status


# ------------------------------------------------------------------
# Logging helpers -------------------------------------------------------------
# ------------------------------------------------------------------

def _init_logs():
    if "logs" not in st.session_state:
        st.session_state["logs"] = []


def _log_append(msg: str):
    _init_logs()
    stamp = datetime.utcnow().strftime("%H:%M:%S")
    st.session_state["logs"].append(f"[{stamp}] {msg}")


_init_logs()

# ------------------------------------------------------------------
# Global component initialization (only once) --------------------------------
# ------------------------------------------------------------------
if "_components_initialized" not in st.session_state:
    _log_append("Initializing components")
    COMPONENTS, BINANCE_CLIENT, CLIENT_STATUS = initialize_components()
    st.session_state["_components_initialized"] = True
    st.session_state["_client_status"] = CLIENT_STATUS
    st.session_state["_qt_status"] = QT_STATUS
else:
    # Reuse from session
    COMPONENTS = st.session_state.get("_components_cache")
    if COMPONENTS is None:
        COMPONENTS, BINANCE_CLIENT, CLIENT_STATUS = initialize_components()
    else:
        CLIENT_STATUS = st.session_state.get("_client_status", "")
        QT_STATUS = st.session_state.get("_qt_status", "")

    st.session_state["_components_cache"] = COMPONENTS

# Guarantee we have comps
if COMPONENTS is None:
    COMPONENTS, BINANCE_CLIENT, CLIENT_STATUS = initialize_components()
    st.session_state["_components_cache"] = COMPONENTS
    st.session_state["_qt_status"] = QT_STATUS

# ------------------------------------------------------------------
# Session defaults for risk
# ------------------------------------------------------------------
for k, v in {
    "sl_mult": 1.5,
    "tp_mult": 3.0,
    "risk_pct": 2.0,
    "max_positions": 5,
}.items():
    st.session_state.setdefault(k, v)

# ------------------------------------------------------------------
# Background AutoScanner -----------------------------------------------------
# ------------------------------------------------------------------

class AutoScanner:
    def __init__(self, market_analyzer, scan_interval=300):
        self.market_analyzer = market_analyzer
        self.scan_interval = scan_interval
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.last_scan_results: Dict[str, Any] = {}
        self.scan_count = 0

    def start_scanning(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._scan_loop, daemon=True)
            self.thread.start()

    def stop_scanning(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)

    def _scan_loop(self):
        while self.running:
            try:
                self.scan_count += 1
                symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT"]
                sigs = self.market_analyzer.analyze_market_signals(symbols)
                strong = {s: d for s, d in sigs.items() if d.get("confidence", 0) > 0.6 and d.get("signal") != "HOLD"}
                self.last_scan_results = {
                    "timestamp": datetime.utcnow(),
                    "total_scanned": len(symbols),
                    "signals_found": len(strong),
                    "strong_signals": strong,
                    "scan_number": self.scan_count,
                }
                time.sleep(self.scan_interval)
            except Exception as e:  # noqa: BLE001
                print(f"Scanner error: {e}")
                time.sleep(30)

    def get_latest_results(self):  # noqa: D401
        return self.last_scan_results

    def is_running(self):  # noqa: D401
        return self.running


if "auto_scanner" not in st.session_state:
    st.session_state["auto_scanner"] = AutoScanner(COMPONENTS["market_analyzer"], scan_interval=st.session_state.get("scan_interval", 300))


# ------------------------------------------------------------------
# Utility: system health
# ------------------------------------------------------------------

def get_system_health():
    return {
        "CPU": f"{psutil.cpu_percent()}%",
        "Memory": f"{psutil.virtual_memory().percent}%",
        "Threads": threading.active_count(),
    }


# ------------------------------------------------------------------
# Utility: FX (USD->GBP) ------------------------------------------------------
# ------------------------------------------------------------------
_USD_GBP_CACHE = {"rate": 0.79, "ts": 0.0}


def get_usd_to_gbp_rate(force_refresh: bool = False) -> float:
    import requests
    if not force_refresh:
        age = time.time() - _USD_GBP_CACHE["ts"]
        if age < 300:
            return _USD_GBP_CACHE["rate"]
    try:
        resp = requests.get("https://api.exchangerate.host/latest?base=USD&symbols=GBP", timeout=5)
        if resp.ok:
            data = resp.json()
            if "rates" in data and "GBP" in data["rates"]:
                rate = float(data["rates"]["GBP"])
                _USD_GBP_CACHE.update({"rate": rate, "ts": time.time()})
                return rate
            else:
                print(f"FX API response missing 'rates': {data}")
    except Exception as e:
        print(f"FX rate error: {e}")
    return _USD_GBP_CACHE["rate"]


# ------------------------------------------------------------------
# Trade Log helpers -----------------------------------------------------------
# ------------------------------------------------------------------
TRADE_LOG_PATH = Path("trade_log.csv")


def record_trade(symbol: str, side: str, qty: float, price: float, usd: float, source: str):
    """Append a trade row to trade_log.csv and session logs."""
    row = {
        "timestamp": datetime.utcnow().isoformat(),
        "symbol": symbol,
        "side": side,
        "quantity": qty,
        "price": price,
        "usd": usd,
        "source": source,
    }
    try:
        df = pd.DataFrame([row])
        header = not TRADE_LOG_PATH.exists()
        df.to_csv(TRADE_LOG_PATH, mode="a", header=header, index=False)
    except Exception as e:  # noqa: BLE001
        _log_append(f"Trade log write error: {e}")
    _log_append(f"TRADE {side} {symbol} {qty} @{price} (${usd:.2f}) via {source}")
    try:
        notify_trade(row)
    except Exception:  # noqa: BLE001
        pass


def load_trade_log(limit: int = 100) -> pd.DataFrame:
    if not TRADE_LOG_PATH.exists():
        return pd.DataFrame(columns=["timestamp", "symbol", "side", "quantity", "price", "usd", "source"])
    try:
        df = pd.read_csv(TRADE_LOG_PATH, parse_dates=["timestamp"])
    except Exception as e:  # noqa: BLE001
        _log_append(f"Trade log read error: {e}")
        return pd.DataFrame(columns=["timestamp", "symbol", "side", "quantity", "price", "usd", "source"])
    if limit and len(df) > limit:
        df = df.tail(limit)
    return df


# Approx PnL aggregator -------------------------------------------------------
# This is a *very* rough realized PnL: pair up BUY with later SELL qty up to same size.

def compute_realized_pnl(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.assign(pnl_usd=[])  # type: ignore
    # Ensure numeric
    df = df.copy()
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0.0)
    df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0.0)
    # group by symbol and match FIFO
    out_rows = []
    for sym, g in df.sort_values("timestamp").groupby("symbol"):
        long_qty = 0.0
        avg_entry = 0.0
        for _, r in g.iterrows():
            side = r["side"].upper()
            qty = r["quantity"]
            price = r["price"]
            pnl = 0.0
            if side.startswith("BUY"):
                # adjust avg entry
                total_cost = avg_entry * long_qty + price * qty
                long_qty += qty
                if long_qty > 0:
                    avg_entry = total_cost / long_qty
            elif side.startswith("SELL"):
                if long_qty <= 0:
                    pnl = 0.0  # flat -> short not supported
                else:
                    sell_qty = min(qty, long_qty)
                    pnl = (price - avg_entry) * sell_qty
                    long_qty -= sell_qty
                    if long_qty <= 0:
                        avg_entry = 0.0
            out_rows.append({**r.to_dict(), "pnl_usd": pnl})
    return pd.DataFrame(out_rows)


# ------------------------------------------------------------------
# TAB RENDER FUNCTIONS =========================================================
# ------------------------------------------------------------------

# ---- DASHBOARD ---------------------------------------------------------------

def render_dashboard():
    st.header(" Hybrid Quantum Crypto Trading Bot Dashboard")
    st.info(st.session_state.get("_client_status", ""))
    qt_msg = st.session_state.get("_qt_status", "")
    if qt_msg and qt_msg.startswith(""):
        st.warning(qt_msg)

    # Quick Stats row
    col1, col2, col3, col4 = st.columns(4)

    # Get portfolio values safely
    try:
        portfolio = COMPONENTS["portfolio_mgr"].get_portfolio()
        total_usd, total_gbp, asset_count = get_unified_portfolio_value(portfolio)
    except Exception:
        total_usd, total_gbp, asset_count = 0.0, 0.0, 0

    with col1:
        st.metric(" Portfolio Value (USD)", f"${total_usd:,.2f}")
    with col2:
        st.metric(" Portfolio Value (GBP)", f"£{total_gbp:,.2f}")
    with col3:
        st.metric(" Total Assets", asset_count)
    with col4:
        health = get_system_health()
        st.metric(" CPU Usage", health.get("CPU", "N/A"))

    st.markdown("---")
    st.subheader("Recent Log Activity")
    _display_logs(limit=15, log_file="logs.txt", refresh_interval=15)

# ---- PORTFOLIO ---------------------------------------------------------------

def render_portfolio():
    st.header(" Portfolio Overview")
    pm = COMPONENTS["portfolio_mgr"]
    try:
        portfolio = pm.get_portfolio()
    except Exception:
        portfolio = {}

    if portfolio:
        total_usd, total_gbp, asset_count = get_unified_portfolio_value(portfolio)
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.metric("Total Value (USD)", f"${total_usd:,.2f}")
        with col2:
            st.metric("Total Value (GBP)", f"£{total_gbp:,.2f}")
        with col3:
            st.metric("Total Assets", asset_count)
        with col1:
            st.info(pm.get_connection_status())
        with col2:
            if st.button(" Refresh Portfolio", key="pf_refresh"):
                with st.spinner("Refreshing"):
                    try:
                        pm.refresh_portfolio()
                    except Exception as e:
                        st.error(f"Error: {e}")
                st.rerun()
        with col3:
            st.caption(f"Last updated: {pm.last_updated()}")

        # Allocation pie (significant assets)
        sig = {k: v for k, v in portfolio.items() if v.get("value", 0) > 1.0}
        if len(sig) > 1:
            import plotly.express as px  # local import
            fig = px.pie(
                values=[d["value"] for d in sig.values()],
                names=list(sig.keys()),
                title="Portfolio Allocation (Assets > $1)",
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No portfolio data available.")

    st.markdown("---")
    st.subheader(" Recent Trade History (last 100)")
    trade_df = _get_recent_trades(limit=100)
    if trade_df.empty:
        st.info("No trades found.")
    else:
        rate = get_usd_to_gbp_rate()
        trade_df = trade_df.copy()
        trade_df["GBP"] = trade_df["usd"] * rate
        trade_df["timestamp"] = pd.to_datetime(trade_df["timestamp"]).dt.tz_localize(None)
        st.dataframe(trade_df, use_container_width=True)

        st.warning("No portfolio data available.")

    # Helper: unify trade history from portfolio_mgr + trade_log.csv

def _get_recent_trades(limit=100) -> pd.DataFrame:
    # From trade_log.csv
    log_df = load_trade_log(limit=limit)
    # From portfolio_mgr (fallback demonstration fields)
    try:
        hist = COMPONENTS["portfolio_mgr"].get_trade_history(limit=limit)
        hist_df = pd.DataFrame(hist)
        if not hist_df.empty:
            # Standardize
            hist_df.rename(columns={"time": "timestamp", "quantity": "quantity", "value": "usd"}, inplace=True)
            hist_df["timestamp"] = pd.to_datetime(hist_df["timestamp"], errors="coerce")
            hist_df["usd"] = hist_df.get("usd", hist_df.get("value", 0))
        else:
            hist_df = pd.DataFrame(columns=["timestamp", "symbol", "side", "quantity", "price", "usd", "commission"])
    except Exception:
        hist_df = pd.DataFrame(columns=["timestamp", "symbol", "side", "quantity", "price", "usd", "commission"])

    # Combine / dedupe
    cols = ["timestamp", "symbol", "side", "quantity", "price", "usd", "source"]
    log_df = log_df[cols] if not log_df.empty else pd.DataFrame(columns=cols)
    hist_df = hist_df.reindex(columns=cols, fill_value=None)
    combo = pd.concat([log_df, hist_df], ignore_index=True)
    combo = combo.sort_values("timestamp").dropna(subset=["timestamp"]).tail(limit)
    return combo.reset_index(drop=True)


# ---- PERFORMANCE -------------------------------------------------------------

def render_performance():
    st.header(" Performance")
    df = load_trade_log(limit=1000)  # load bigger then trim after grouping
    if df.empty:
        st.info("No trade data yet. Execute some trades.")
        return

    df_pnl = compute_realized_pnl(df)
    rate = get_usd_to_gbp_rate()
    df_pnl["pnl_gbp"] = df_pnl["pnl_usd"] * rate

    st.subheader("Realized PnL (FIFO approx)")
    st.dataframe(df_pnl.tail(100), use_container_width=True)

    total_pnl = df_pnl["pnl_usd"].sum()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total PnL (USD)", f"${total_pnl:,.2f}", delta=None)
    with col2:
        st.metric("Total PnL (GBP)", f"GBP {total_pnl*rate:,.2f}")
    with col3:
        wins = (df_pnl["pnl_usd"] > 0).sum()
        total = len(df_pnl)
        wr = wins/total*100 if total>0 else 0
        st.metric("Win Rate", f"{wr:.1f}%")

    st.markdown("---")
    st.subheader("Equity Curve (Cumulative PnL USD)")
    df_pnl["cum_pnl"] = df_pnl["pnl_usd"].cumsum()
    import plotly.graph_objects as go  # local import

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_pnl["timestamp"], y=df_pnl["cum_pnl"], mode="lines", name="Cumulative PnL"))
    fig.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig, use_container_width=True)

# ---- MULTISTRATEGY ----------------------------------------------------------
# Rekey all widgets with "ms_" prefix to avoid collisions.

MS_DEFAULTS = {
    "ms_weight_quantum": 30,
    "ms_weight_ml": 30,
    "ms_weight_technical": 40,
    "ms_min_conf": 0.65,
    "ms_max_pairs": 20,
    "ms_scan_mode": "Top Volume Pairs",
    "ms_show_only_signals": True,
    "ms_latest_signals": [],
    "ms_last_scan_time": None,
    "ms_manual_scan_requested": False,
}
for _k, _v in MS_DEFAULTS.items():
    st.session_state.setdefault(_k, _v)


def render_multi_strategy():
    st.header(" Multi-Strategy Market Scanner")
    st.caption("Quantum + ML + Technical Analysis across selected pairs.")
    qt_msg = st.session_state.get("_qt_status", "")
    if qt_msg and qt_msg.startswith(""):
        st.warning(qt_msg)

    # -------------------------------------------------
    # Configuration Section
    # -------------------------------------------------
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("**Strategy Weights (Auto-balanced to 100%)**")
        
        subcol1, subcol2, subcol3 = st.columns(3)
        with subcol1:
            quantum_weight = st.slider(
                "Quantum Weight", 0, 100, st.session_state['ms_weight_quantum'],
                key="ms_quantum_weight"
            )
        with subcol2:
            ml_weight = st.slider(
                "ML Weight", 0, 100, st.session_state['ms_weight_ml'],
                key="ms_ml_weight"
            )
        with subcol3:
            technical_weight = st.slider(
                "Technical Weight", 0, 100, st.session_state['ms_weight_technical'],
                key="ms_technical_weight"
            )
        
        # Auto-balance weights to exactly 100
        total = quantum_weight + ml_weight + technical_weight
        if total <= 0:
            quantum_weight, ml_weight, technical_weight = 0, 0, 100
        else:
            quantum_weight = int((quantum_weight / total) * 100)
            ml_weight = int((ml_weight / total) * 100)
            technical_weight = 100 - quantum_weight - ml_weight
        
        # Persist
        st.session_state['ms_weight_quantum'] = quantum_weight
        st.session_state['ms_weight_ml'] = ml_weight
        st.session_state['ms_weight_technical'] = technical_weight
        
        # Visual weight display
        weight_col1, weight_col2, weight_col3 = st.columns(3)
        with weight_col1:
            st.metric("Quantum", f"{quantum_weight}%")
            st.progress(quantum_weight / 100)
        with weight_col2:
            st.metric("ML", f"{ml_weight}%")
            st.progress(ml_weight / 100)
        with weight_col3:
            st.metric("Technical", f"{technical_weight}%")
            st.progress(technical_weight / 100)
        
        # Presets
        preset_col1, preset_col2, preset_col3, preset_col4 = st.columns(4)
        with preset_col1:
            if st.button(" Quantum Focus", key="ms_preset_quantum"):
                st.session_state['ms_weight_quantum'] = 60
                st.session_state['ms_weight_ml'] = 20
                st.session_state['ms_weight_technical'] = 20
        with preset_col2:
            if st.button(" ML Focus", key="ms_preset_ml"):
                st.session_state['ms_weight_quantum'] = 20
                st.session_state['ms_weight_ml'] = 60
                st.session_state['ms_weight_technical'] = 20
        with preset_col3:
            if st.button(" Technical Focus", key="ms_preset_technical"):
                st.session_state['ms_weight_quantum'] = 20
                st.session_state['ms_weight_ml'] = 20
                st.session_state['ms_weight_technical'] = 60
        with preset_col4:
            if st.button(" Balanced", key="ms_preset_balanced"):
                st.session_state['ms_weight_quantum'] = 33
                st.session_state['ms_weight_ml'] = 33
                st.session_state['ms_weight_technical'] = 34
    
    with col2:
        st.session_state['ms_min_conf'] = st.slider(
            "Min Confidence", 0.5, 1.0, float(st.session_state['ms_min_conf']),
            0.01, key="ms_min_conf_slider"
        )
        st.session_state['ms_max_pairs'] = st.slider(
            "Max Pairs to Scan", 5, 50, int(st.session_state['ms_max_pairs']),
            5, key="ms_max_pairs_slider"
        )
        st.session_state['ms_scan_mode'] = st.selectbox(
            "Scan Mode",
            ["Top Volume Pairs", "Portfolio + Major Pairs", "All USDT Pairs", "Custom Selection"],
            key="ms_scan_mode_select",
            index=[
                "Top Volume Pairs",
                "Portfolio + Major Pairs", 
                "All USDT Pairs",
                "Custom Selection"
            ].index(st.session_state['ms_scan_mode'])
        )
    
    # -------------------------------------------------
    # Pair Selection Logic
    # -------------------------------------------------
    all_pairs = COMPONENTS['market_analyzer'].get_trading_pairs()
    max_pairs = st.session_state['ms_max_pairs']
    scan_mode = st.session_state['ms_scan_mode']
    
    if scan_mode == "Top Volume Pairs":
        trading_pairs = all_pairs[:max_pairs]
    elif scan_mode == "Portfolio + Major Pairs":
        try:
            portfolio = COMPONENTS['portfolio_mgr'].get_portfolio()
            portfolio_pairs = [
                f"{asset}USDT" for asset in portfolio.keys() if asset not in ["USDT", "BUSD"]
            ]
        except Exception:
            portfolio_pairs = []
        major_pairs = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'ADAUSDT']
        trading_pairs = list(dict.fromkeys(portfolio_pairs + major_pairs))[:max_pairs]
    elif scan_mode == "All USDT Pairs":
        trading_pairs = [pair for pair in all_pairs if pair.endswith('USDT')][:max_pairs]
    else:  # Custom Selection
        trading_pairs = st.multiselect(
            "Select Trading Pairs",
            all_pairs,
            default=['BTCUSDT', 'ETHUSDT', 'BNBUSDT'],
            key="ms_custom_pairs"
        )[:max_pairs]
    
    # -------------------------------------------------
    # Scan Controls
    # -------------------------------------------------
    scan_col1, scan_col2, scan_col3 = st.columns(3)
    with scan_col1:
        if st.button(" Scan All Pairs", type="primary", key="ms_scan_button"):
            st.session_state['ms_manual_scan_requested'] = True
    with scan_col2:
        if st.button(" Refresh Signals", key="ms_refresh_button"):
            st.session_state['ms_manual_scan_requested'] = True
    with scan_col3:
        st.session_state['ms_show_only_signals'] = st.checkbox(
            "Show Only Strong Signals",
            value=st.session_state['ms_show_only_signals'],
            key="ms_show_only_signals_check"
        )
    
    # -------------------------------------------------
    # Scanning process
    # -------------------------------------------------
    if st.session_state.get('ms_manual_scan_requested', False):
        progress_bar = st.progress(0.0)
        status_text = st.empty()
        signals_data = []
        
        for i, symbol in enumerate(trading_pairs):
            try:
                progress = (i + 1) / len(trading_pairs)
                progress_bar.progress(progress)
                status_text.text(f"Analyzing {symbol}... ({i+1}/{len(trading_pairs)})")
                
                # Pull data
                rsi = COMPONENTS['market_analyzer'].get_latest_rsi(symbol)
                momentum = COMPONENTS['market_analyzer'].get_latest_momentum(symbol)
                volatility = COMPONENTS['market_analyzer'].get_volatility(symbol)
                price = COMPONENTS['market_analyzer'].get_price(symbol)
                
                # Heuristic signal logic
                quantum_decision = "HOLD"
                quantum_conf = 0.5
                if rsi < 30 and momentum > 3:
                    quantum_decision = "BUY"
                    quantum_conf = 0.75
                elif rsi > 70 and momentum < -3:
                    quantum_decision = "SELL"
                    quantum_conf = 0.75
                elif abs(momentum) > 5:
                    quantum_decision = "BUY" if momentum > 0 else "SELL"
                    quantum_conf = 0.65
                
                # ML simulation (more conservative)
                ml_decision = quantum_decision
                ml_conf = quantum_conf * 0.9
                
                # Technical analysis
                tech_decision = quantum_decision
                tech_conf = min(quantum_conf * 1.1, 1.0)
                
                # Final ensemble decision
                weights = {
                    "quantum": st.session_state['ms_weight_quantum'],
                    "ml": st.session_state['ms_weight_ml'],
                    "technical": st.session_state['ms_weight_technical']
                }
                final_conf = (
                    quantum_conf * weights['quantum'] +
                    ml_conf * weights['ml'] +
                    tech_conf * weights['technical']
                ) / 100.0
                
                min_conf = st.session_state['ms_min_conf']
                final_decision = quantum_decision if final_conf >= min_conf else "HOLD"
                
                signal = {
                    "symbol": symbol,
                    "quantum": {"decision": quantum_decision, "confidence": quantum_conf},
                    "ml": {"decision": ml_decision, "confidence": ml_conf},
                    "technical": {"decision": tech_decision, "confidence": tech_conf},
                    "final": {"decision": final_decision, "confidence": final_conf},
                    "price": price,
                    "rsi": rsi,
                    "momentum": momentum,
                    "volatility": volatility
                }
                signals_data.append(signal)
                
                # Notify strong signals
                if final_decision in ("BUY", "SELL") and final_conf >= 0.8:
                    try:
                        notify_signal({
                            'symbol': symbol,
                            'signal': final_decision,
                            'confidence': final_conf,
                            'price': price,
                            'rsi': rsi,
                            'momentum': momentum,
                            'volatility': volatility
                        })
                    except Exception:
                        pass
            except Exception as e:
                _append_log(f"Error analyzing {symbol}: {e}")
        
        progress_bar.empty()
        status_text.empty()
        
        st.session_state['ms_latest_signals'] = signals_data
        st.session_state['ms_manual_scan_requested'] = False
        st.session_state['ms_last_scan_time'] = datetime.utcnow()
    
    # -------------------------------------------------
    # Display Results
    # -------------------------------------------------
    signals_data = st.session_state.get('ms_latest_signals', [])
    min_conf = st.session_state['ms_min_conf']
    show_only_signals = st.session_state['ms_show_only_signals']
    
    if signals_data:
        # Filter
        if show_only_signals:
            filtered_signals = [
                s for s in signals_data
                if s['final']['decision'] != 'HOLD' and s['final']['confidence'] >= min_conf
            ]
        else:
            filtered_signals = signals_data
        
        if filtered_signals:
            st.subheader(f" Analysis Results ({len(filtered_signals)} pairs)")
            
            # DataFrame
            signals_df = []
            for s in filtered_signals:
                signals_df.append({
                    "Symbol": s["symbol"],
                    "Price": f"${s.get('price', 0):.4f}",
                    "Final Signal": s['final']['decision'],
                    "Confidence": f"{s['final']['confidence']:.3f}",
                    "Quantum": f"{s['quantum']['decision']} ({s['quantum']['confidence']:.2f})",
                    "ML": f"{s['ml']['decision']} ({s['ml']['confidence']:.2f})",
                    "Technical": f"{s['technical']['decision']} ({s['technical']['confidence']:.2f})",
                    "RSI": f"{s.get('rsi', 50):.1f}",
                    "Momentum": f"{s.get('momentum', 0):.2f}%",
                    "Volatility": f"{s.get('volatility', 0):.3f}"
                })
            df = pd.DataFrame(signals_df)
            
            # Style the dataframe
            def color_signals(val):
                if 'BUY' in str(val):
                    return 'background-color: #90EE90'
                if 'SELL' in str(val):
                    return 'background-color: #FFB6C1'
                return 'background-color: #F0F0F0'
            
            styled_df = df.style.applymap(color_signals, subset=['Final Signal'])
            st.dataframe(styled_df, use_container_width=True)
            
            # -------------------------------------------------
            # Quick Trading Interface
            # -------------------------------------------------
            st.subheader(" Quick Trading Interface")
            
            import hashlib
            def create_unique_button_key(action, symbol, index):
                unique_string = f"{action}_{symbol}_{index}_{int(time.time()*1000)}"
                return f"{action}_{hashlib.md5(unique_string.encode()).hexdigest()[:8]}"
            
            strong_buy_signals = [s for s in filtered_signals if s['final']['decision'] == 'BUY']
            strong_sell_signals = [s for s in filtered_signals if s['final']['decision'] == 'SELL']
            
            if strong_buy_signals or strong_sell_signals:
                trade_col1, trade_col2 = st.columns(2)
                
                with trade_col1:
                    if strong_buy_signals:
                        st.write("** Strong BUY Signals:**")
                        for i, sig in enumerate(strong_buy_signals[:5]):
                            _sym = sig['symbol']
                            _conf = sig['final']['confidence']
                            _price = sig.get('price', 0)
                            if _price > 0:
                                sc1, sc2 = st.columns([3, 1])
                                with sc1:
                                    st.write(f"**{_sym}** - ${_price:.4f} (Conf: {_conf:.3f})")
                                with sc2:
                                    if st.button(" Buy", key=create_unique_button_key("ms_buy", _sym, i)):
                                        st.session_state['ms_selected_trade'] = {
                                            'symbol': _sym,
                                            'action': 'BUY',
                                            'price': _price,
                                            'confidence': _conf,
                                            'timestamp': datetime.utcnow(),
                                            'source': 'multi_strategy'
                                        }
                                        st.success(f"Selected {_sym} for BUY")
                                        st.rerun()
                
                with trade_col2:
                    if strong_sell_signals:
                        st.write("** Strong SELL Signals:**")
                        for i, sig in enumerate(strong_sell_signals[:5]):
                            _sym = sig['symbol']
                            _conf = sig['final']['confidence']
                            _price = sig.get('price', 0)
                            if _price > 0:
                                sc1, sc2 = st.columns([3, 1])
                                with sc1:
                                    st.write(f"**{_sym}** - ${_price:.4f} (Conf: {_conf:.3f})")
                                with sc2:
                                    if st.button(" Sell", key=create_unique_button_key("ms_sell", _sym, i)):
                                        st.session_state['ms_selected_trade'] = {
                                            'symbol': _sym,
                                            'action': 'SELL',
                                            'price': _price,
                                            'confidence': _conf,
                                            'timestamp': datetime.utcnow(),
                                            'source': 'multi_strategy'
                                        }
                                        st.success(f"Selected {_sym} for SELL")
                                        st.rerun()
            
            # -------------------------------------------------
            # Execute Selected Trade
            # -------------------------------------------------
            if (
                'ms_selected_trade' in st.session_state and
                st.session_state['ms_selected_trade'].get('source') == 'multi_strategy'
            ):
                trade = st.session_state['ms_selected_trade']
                st.divider()
                st.subheader(f" Execute Trade: {trade['action']} {trade['symbol']}")
                
                exec_col1, exec_col2, exec_col3 = st.columns(3)
                with exec_col1:
                    st.info(f"**Symbol:** {trade['symbol']}")
                    st.info(f"**Action:** {trade['action']}")
                    st.info(f"**Price:** ${trade['price']:.4f}")
                    st.info(f"**Confidence:** {trade['confidence']:.3f}")
                
                with exec_col2:
                    quantity = st.number_input(
                        "Quantity",
                        min_value=0.0001,
                        step=0.0001,
                        format="%.6f",
                        key="ms_strategy_quantity"
                    )
                    if quantity > 0:
                        trade_value = quantity * trade['price']
                        est_fee = trade_value * 0.001
                        st.info(f"Trade Value: ${trade_value:.2f}")
                        st.caption(f"Est. Fee: ${est_fee:.2f}")
                
                with exec_col3:
                    if st.button(" Execute Trade", type="primary", key="ms_strategy_execute"):
                        if quantity > 0:
                            try:
                                result = COMPONENTS['trade_exec'].manual_trade(
                                    trade['symbol'], quantity,
                                    st.session_state["sl_mult"], st.session_state["tp_mult"]
                                )
                                st.success(f"... Trade Executed: {result}")
                                
                                # Log the trade
                                _record_trade(
                                    trade['symbol'], 
                                    trade['action'], 
                                    quantity, 
                                    trade['price'], 
                                    quantity * trade['price'],
                                    fee=quantity * trade['price'] * 0.001,
                                    execution_type='multi_strategy'
                                )
                                
                                # Append to session logs
                                _append_log(
                                    f"Multi-Strategy Trade: {trade['action']} {quantity:.6f} "
                                    f"{trade['symbol']} @ ${trade['price']:.4f} "
                                    f"(Conf: {trade['confidence']:.3f})"
                                )
                                
                                # Notify
                                try:
                                    trade_data = {
                                        'symbol': trade['symbol'],
                                        'side': trade['action'],
                                        'quantity': quantity,
                                        'price': trade['price'],
                                        'value': quantity * trade['price'],
                                        'timestamp': datetime.utcnow().isoformat(),
                                        'execution_type': 'multi_strategy',
                                        'confidence': trade['confidence']
                                    }
                                    notify_trade(trade_data)
                                except Exception:
                                    pass
                                
                                del st.session_state['ms_selected_trade']
                                st.rerun()
                            
                            except Exception as e:
                                st.error(f" Trade execution failed: {e}")
                                try:
                                    notify_error(
                                        "Multi-Strategy Trade Execution", str(e),
                                        {
                                            'symbol': trade['symbol'],
                                            'quantity': quantity,
                                            'action': trade['action']
                                        }
                                    )
                                except Exception:
                                    pass
                        else:
                            st.error(" Invalid quantity")
                    
                    if st.button(" Cancel Trade", key="ms_strategy_cancel"):
                        del st.session_state['ms_selected_trade']
                        st.rerun()
            
                st.info(" Select a signal above to execute a trade")
            
            # -------------------------------------------------
            # Signal Statistics
            # -------------------------------------------------
            st.subheader(" Signal Statistics")
            total_scanned = len(signals_data)
            strong_signals = len(filtered_signals)
            buy_signals = len([s for s in filtered_signals if s['final']['decision'] == 'BUY'])
            sell_signals = len([s for s in filtered_signals if s['final']['decision'] == 'SELL'])
            
            stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
            with stats_col1:
                st.metric("Total Scanned", total_scanned)
            with stats_col2:
                st.metric("Strong Signals", strong_signals)
            with stats_col3:
                st.metric("BUY Signals", buy_signals)
            with stats_col4:
                st.metric("SELL Signals", sell_signals)
        
            st.warning(" No strong signals found with current confidence threshold")
            st.info(" Try lowering the minimum confidence or scanning more pairs")
        
        # Last scan info
        if st.session_state['ms_last_scan_time']:
            st.caption(f"Last scan: {st.session_state['ms_last_scan_time'].strftime('%H:%M:%S')}")
    
        # No signals yet (never scanned)
        st.info(" Click 'Scan All Pairs' to analyze trading opportunities")
        st.subheader(" Pairs to be scanned:")
        if trading_pairs:
            pairs_cols = st.columns(4)
            for i, pair in enumerate(trading_pairs[:20]):
                pairs_cols[i % 4].write(f" {pair}")
            if len(trading_pairs) > 20:
                st.caption(f"... and {len(trading_pairs) - 20} more pairs")
# ---- AUTO-TRADER -------------------------------------------------------------

def render_auto_trader():
    st.header(" Auto-Trader Control")
    st.caption("Background scanner with automated signal detection")
    
    auto_scanner = st.session_state["auto_scanner"]
    
    # Scanner Status and Controls
    col1, col2 = st.columns(2)
    with col1:
        status = " Running" if auto_scanner.is_running() else " Stopped"
        st.metric("Scanner Status", status)
        
        if st.button(" Start Auto-Scanner" if not auto_scanner.is_running() else " Stop Auto-Scanner", 
                     type="primary", key="auto_scanner_toggle"):
            if auto_scanner.is_running():
                auto_scanner.stop_scanning()
                _log_append("Auto-scanner stopped")
                st.success("Auto-scanner stopped.")
            else:
                auto_scanner.start_scanning()
                _log_append("Auto-scanner started")
                st.success("Auto-scanner started.")
            st.rerun()
    
    with col2:
        st.metric("Scan Interval", f"{auto_scanner.scan_interval}s")
        st.metric("Scan Count", auto_scanner.scan_count)
    
    st.markdown("---")
    
    # Last Scan Results
    st.subheader(" Last Scan Results")
    results = auto_scanner.get_latest_results()
    
    if results:
        # Results metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Scanned", results.get('total_scanned', 0))
        with col2:
            st.metric("Signals Found", results.get('signals_found', 0))
        with col3:
            st.metric("Scan #", results.get('scan_number', 0))
        with col4:
            if 'timestamp' in results:
                st.metric("Last Scan", results['timestamp'].strftime("%H:%M:%S"))
        
        # Strong signals details
        strong_signals = results.get('strong_signals', {})
        if strong_signals:
            st.subheader(" Strong Signals Detected")
            
            signal_rows = []
            for symbol, signal_data in strong_signals.items():
                signal_rows.append({
                    "Symbol": symbol,
                    "Signal": signal_data.get('signal', 'N/A'),
                    "Confidence": f"{signal_data.get('confidence', 0):.3f}",
                    "RSI": f"{signal_data.get('rsi', 0):.1f}",
                    "Price": f"${signal_data.get('price', 0):.4f}"
                })
            
            if signal_rows:
                df_signals = pd.DataFrame(signal_rows)
                
                # Color code the signals
                def color_auto_signals(val):
                    if 'BUY' in str(val):
                        return 'background-color: #90EE90'
                    elif 'SELL' in str(val):
                        return 'background-color: #FFB6C1'
                    return ''
                
                styled_signals = df_signals.style.applymap(color_auto_signals, subset=['Signal'])
                st.dataframe(styled_signals, use_container_width=True)
                
                # Auto-execute options (if enabled)
                st.subheader(" Auto-Execute Options")
                auto_execute_enabled = st.checkbox("Enable Auto-Execute", value=False, key="auto_execute_enabled")
                
                if auto_execute_enabled:
                    st.warning(" Auto-execute enabled - trades will be executed automatically!")
                    min_auto_confidence = st.slider("Min Confidence for Auto-Execute", 0.7, 1.0, 0.8, 0.01, key="auto_min_conf")
                    
                    # Show which signals would auto-execute
                    auto_signals = [row for row in signal_rows if float(row['Confidence']) >= min_auto_confidence]
                    if auto_signals:
                        st.info(f" {len(auto_signals)} signals above threshold would auto-execute")
                        for sig in auto_signals[:3]:  # Show top 3
                            st.write(f" {sig['Symbol']}: {sig['Signal']} (Conf: {sig['Confidence']})")
                else:
                    st.info("Auto-execute disabled - manual review required")
        else:
            st.info("No strong signals detected in last scan")
    else:
        st.info("No scan results yet. Scanner will populate data once running.")
    
    st.markdown("---")
    
    # Scanner Configuration
    st.subheader(" Scanner Configuration")
    
    config_col1, config_col2 = st.columns(2)
    with config_col1:
        new_interval = st.number_input(
            "Scan Interval (seconds)", 
            min_value=60, 
            max_value=3600, 
            value=auto_scanner.scan_interval,
            step=30,
            key="auto_scan_interval"
        )
        
        if st.button("Update Interval", key="update_scan_interval"):
            auto_scanner.scan_interval = new_interval
            st.session_state.setdefault("scan_interval", new_interval)
            _log_append(f"Scanner interval updated to {new_interval}s")
            st.success(f"Interval updated to {new_interval} seconds")
    
    with config_col2:
        # Scanner health info
        if auto_scanner.is_running():
            st.success("... Scanner thread active")
        else:
            st.warning(" Scanner thread inactive")
        
        # Manual trigger
        if st.button(" Manual Scan Now", key="manual_scan_trigger"):
            if hasattr(auto_scanner.market_analyzer, 'analyze_market_signals'):
                with st.spinner("Running manual scan..."):
                    try:
                        symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT"]
                        sigs = auto_scanner.market_analyzer.analyze_market_signals(symbols)
                        strong = {s: d for s, d in sigs.items() if d.get("confidence", 0) > 0.6 and d.get("signal") != "HOLD"}
                        
                        auto_scanner.last_scan_results = {
                            "timestamp": datetime.utcnow(),
                            "total_scanned": len(symbols),
                            "signals_found": len(strong),
                            "strong_signals": strong,
                            "scan_number": auto_scanner.scan_count + 1,
                        }
                        auto_scanner.scan_count += 1
                        st.success(f"Manual scan completed - found {len(strong)} strong signals")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Manual scan failed: {e}")
                        _log_append(f"Manual scan error: {e}")
            else:
                st.error("Market analyzer not available for manual scan")
# ---- MANUAL TRADER -----------------------------------------------------------

def render_manual_trader():
    st.header(" Manual Trade Execution")
    st.caption("Execute individual trades with custom parameters")
    
    # Symbol selection
all_pairs = COMPONENTS["market_analyzer"].get_trading_pairs()
symbol = st.selectbox("Trading Pair", all_pairs, key="manual_symbol")

# Current price info
try:
    current_price = COMPONENTS["market_analyzer"].get_price(symbol)
    rsi = COMPONENTS["market_analyzer"].get_latest_rsi(symbol)
    momentum = COMPONENTS["market_analyzer"].get_latest_momentum(symbol)
except Exception as e:
    current_price = 0.0
    rsi = 50.0
    momentum = 0.0
    _log_append(f"Price fetch error: {e}")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Current Price", f"${current_price:.4f}")
with col2:
    st.metric("RSI", f"{rsi:.1f}")
with col3:
    st.metric("Momentum", f"{momentum:.2f}%")

st.markdown("---")

# Trade parameters
trade_col1, trade_col2 = st.columns(2)

with trade_col1:
    st.subheader(" Trade Parameters")

    trade_type = st.radio("Trade Type", ["Market Order", "Limit Order"], horizontal=True, key="manual_trade_type")
    side = st.radio("Side", ["BUY", "SELL"], horizontal=True, key="manual_side")

    # Quantity input
    qty_method = st.radio("Quantity Method", ["By Amount (USD)", "By Quantity"], horizontal=True, key="manual_qty_method")

    # Initialize variables
    calculated_qty = 0.0
    trade_amount_usd = 0.0

    if qty_method == "By Amount (USD)":
        trade_amount_usd = st.number_input(
            "Trade Amount (USD)", 
            min_value=1.0, max_value=10000.0, 
            value=50.0, step=5.0, key="manual_amount"
        )
        if current_price > 0:
            calculated_qty = trade_amount_usd / current_price

            # ✅ Adjust quantity for Binance precision
            if BINANCE_CLIENT:
                calculated_qty = adjust_quantity(symbol, calculated_qty, BINANCE_CLIENT)

            st.info(f"Calculated Quantity: {calculated_qty:.8f} {symbol.replace('USDT', '')}")
        else:
            calculated_qty = 0
    else:
        calculated_qty = st.number_input(
            "Quantity", 
            min_value=0.000001, step=0.000001, format="%.8f", key="manual_qty"
        )

        # ✅ Adjust quantity for Binance precision
        if BINANCE_CLIENT:
            calculated_qty = adjust_quantity(symbol, calculated_qty, BINANCE_CLIENT)

        trade_amount_usd = calculated_qty * current_price
        st.info(f"Trade Value: ${trade_amount_usd:.2f}")

    # ✅ Limit price block inside trade_col1
    if trade_type == "Limit Order":
        limit_price = st.number_input("Limit Price", min_value=0.0001, value=current_price, step=0.0001, format="%.4f", key="manual_limit_price")
    else:
        limit_price = current_price

with trade_col2:
    st.subheader(" Risk Management")

    use_sl_tp = st.checkbox("Use Stop Loss / Take Profit", value=True, key="manual_use_sl_tp")

    if use_sl_tp:
        sl_mult = st.number_input("Stop Loss Multiplier", min_value=0.5, max_value=10.0, value=st.session_state["sl_mult"], step=0.1, key="manual_sl_mult")
        tp_mult = st.number_input("Take Profit Multiplier", min_value=1.0, max_value=20.0, value=st.session_state["tp_mult"], step=0.5, key="manual_tp_mult")

        if side == "BUY":
            sl_price = current_price * (1 - (sl_mult * 0.01))
            tp_price = current_price * (1 + (tp_mult * 0.01))
        else:
            sl_price = current_price * (1 + (sl_mult * 0.01))
            tp_price = current_price * (1 - (tp_mult * 0.01))

        st.info(f"Stop Loss: ${sl_price:.4f}")
        st.info(f"Take Profit: ${tp_price:.4f}")

    # Risk assessment
    portfolio_value = COMPONENTS["portfolio_mgr"].total_value()
    risk_percentage = (trade_amount_usd / portfolio_value * 100) if portfolio_value > 0 else 0
    st.metric("Risk %", f"{risk_percentage:.2f}%")

st.markdown("---")

# Trade execution
st.subheader(" Execute Trade")

summary_col1, summary_col2, summary_col3 = st.columns(3)
with summary_col1:
    st.info(f"**Symbol:** {symbol}")
    st.info(f"**Side:** {side}")
with summary_col2:
    st.info(f"**Type:** {trade_type}")
    st.info(f"**Quantity:** {calculated_qty:.8f}")
with summary_col3:
    st.info(f"**Price:** ${limit_price:.4f}")
    st.info(f"**Value:** ${trade_amount_usd:.2f}")

if st.button(" Execute Trade", type="primary", key="manual_execute", disabled=(calculated_qty <= 0)):
    if calculated_qty > 0:
        try:
            # Execute via trade executor
            result = COMPONENTS["trade_exec"].manual_trade(
                symbol, 
                calculated_qty, 
                sl_mult if use_sl_tp else 1.5, 
                tp_mult if use_sl_tp else 3.0,
                trade_amount_usd=trade_amount_usd
            )
            record_trade(symbol=symbol, side=side, qty=calculated_qty, price=limit_price, usd=trade_amount_usd, source="manual")
            st.success("... Trade executed successfully!")
            if isinstance(result, dict):
                st.json(result)
            else:
                st.write(result)
            _log_append(f"Manual trade executed: {side} {calculated_qty:.8f} {symbol} @ ${limit_price:.4f}")

            # Notify
            try:
                notify_trade({
                    'symbol': symbol,
                    'side': side,
                    'quantity': calculated_qty,
                    'price': limit_price,
                    'value': trade_amount_usd,
                    'timestamp': datetime.utcnow().isoformat(),
                    'execution_type': 'manual'
                })
            except Exception:
                pass

        except Exception as e:
            st.error(f" Trade execution failed: {e}")
            _log_append(f"Manual trade failed: {e}")
            try:
                notify_error("Manual Trade Execution", str(e), {
                    'symbol': symbol,
                    'side': side,
                    'quantity': calculated_qty
                })
            except Exception:
                pass
        else:
        st.error(" Invalid quantity")
        except Exception as e:
                st.error(f" Trade execution failed: {e}")
                _log_append(f"Manual trade failed: {e}")
                try:
                    notify_error("Manual Trade Execution", str(e), {
                        'symbol': symbol,
                        'side': side,
                        'quantity': calculated_qty
                    })
                except Exception:
                    pass
        else:
            st.error(" Invalid quantity")


# ---- BACKTESTING -------------------------------------------------------------

def render_backtesting():
    st.header(" Backtesting")
    if BACKTESTING_AVAILABLE and BacktestingIntegration is not None:
        try:
            bt = BacktestingIntegration()
            bt.render_backtesting_tab()
        except Exception as e:
            st.error(f"Backtesting error: {e}")
            st.info("Try: pip install ccxt scipy")
    else:
        st.error("Backtesting unavailable. Install ccxt & scipy.")


# ---- SYSTEM HEALTH -----------------------------------------------------------

def render_system_health():
    st.header(" System Health Monitor")
    st.caption("Detailed system monitoring and component diagnostics")
    
    # System metrics (more detailed than sidebar)
    st.subheader(" Detailed System Metrics")
    health = get_system_health()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        cpu_pct = float(health["CPU"].replace('%', ''))
        color = "" if cpu_pct > 80 else "" if cpu_pct > 60 else ""
        st.metric("CPU Usage", f"{color} {health['CPU']}")
        
        # CPU usage chart (if you want to add historical data)
        if cpu_pct > 0:
            st.progress(cpu_pct / 100)
        
    with col2:
        mem_pct = float(health["Memory"].replace('%', ''))
        color = "" if mem_pct > 80 else "" if mem_pct > 60 else ""
        st.metric("Memory Usage", f"{color} {health['Memory']}")
        
        if mem_pct > 0:
            st.progress(mem_pct / 100)
        
    with col3:
        thread_count = health["Threads"]
        color = "" if thread_count > 20 else "" if thread_count > 10 else ""
        st.metric("Active Threads", f"{color} {thread_count}")
    
    st.markdown("---")
    
    # Component status (keep this - it's useful for debugging)
    st.subheader(" Component Status")
    
    component_status = []
    for comp_name, comp_obj in COMPONENTS.items():
        if comp_obj is not None:
            status = "... Active"
            if hasattr(comp_obj, 'get_connection_status'):
                try:
                    status = comp_obj.get_connection_status()
                except:
                    status = "... Active (no status method)"
        else:
            status = " Not Available"
        
        component_status.append({
            "Component": comp_name.replace('_', ' ').title(),
            "Status": status,
            "Type": type(comp_obj).__name__ if comp_obj else "None"
        })
    
    comp_df = pd.DataFrame(component_status)
    st.dataframe(comp_df, use_container_width=True)
    
    st.markdown("---")
    
    # Process Information (more detailed than sidebar)
    st.subheader(" Process Details")
    
    try:
        import psutil
        current_process = psutil.Process()
        
        proc_col1, proc_col2, proc_col3 = st.columns(3)
        with proc_col1:
            st.metric("Memory RSS", f"{current_process.memory_info().rss / 1024 / 1024:.1f} MB")
            st.metric("Memory VMS", f"{current_process.memory_info().vms / 1024 / 1024:.1f} MB")
        
        with proc_col2:
            st.metric("CPU Times", f"{current_process.cpu_times().user:.1f}s user")
            st.metric("", f"{current_process.cpu_times().system:.1f}s system")
        
        with proc_col3:
            st.metric("Open Files", len(current_process.open_files()))
            st.metric("Connections", len(current_process.connections()))
            
    except Exception as e:
        st.error(f"Process details unavailable: {e}")
    
    st.markdown("---")
    
    # Refresh button
    if st.button(" Refresh Health Check", key="system_health_refresh"):
        st.rerun()


# Get client from components or try to create one
binance_client = None
try:
    # Try to get from global components first
    if 'BINANCE_CLIENT' in globals():
        binance_client = BINANCE_CLIENT
    else:
        # Try to setup client
        binance_client, _ = setup_binance_client()
except Exception:
    binance_client = None

if binance_client:
    try:
        server_time = binance_client.get_server_time()
        server_datetime = datetime.fromtimestamp(server_time['serverTime'] / 1000)
        st.success(f"... Binance API connected - Server time: {server_datetime.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        # Test account info
        try:
            account_info = binance_client.get_account()
            st.info(f"Account permissions: {', '.join(account_info.get('permissions', []))}")
        except Exception as e:
            st.warning(f" Account info failed: {e}")
            
    except Exception as e:
        st.error(f" Binance API connection failed: {e}")
else:
    st.warning(" No Binance client available - running in demo mode")
    
    st.markdown("---")
    

# ---- SETTINGS ----------------------------------------------------------------

def render_settings():
    st.header(" Trading Settings & Configuration")
    st.caption("Configure risk management, notifications, and system preferences")
    
    # Create main layout
    settings_col1, settings_col2 = st.columns(2)
    
    # ================================
    # LEFT COLUMN - Risk Management
    # ================================
    with settings_col1:
        st.subheader(" Risk Management")
        
        # Stop Loss Multiplier
        st.session_state["sl_mult"] = st.slider(
            " Stop Loss Multiplier", 
            min_value=0.5, 
            max_value=5.0, 
            value=st.session_state["sl_mult"], 
            step=0.1,
            help="Multiplier for stop loss calculation",
            key="settings_sl_mult"
        )
        
        # Take Profit Multiplier
        st.session_state["tp_mult"] = st.slider(
            " Take Profit Multiplier", 
            min_value=1.0, 
            max_value=10.0, 
            value=st.session_state["tp_mult"], 
            step=0.5,
            help="Multiplier for take profit calculation",
            key="settings_tp_mult"
        )
        
        # Risk per Trade
        st.session_state["risk_pct"] = st.slider(
            " Risk per Trade (%)", 
            min_value=0.1, 
            max_value=5.0, 
            value=st.session_state["risk_pct"], 
            step=0.1,
            help="Percentage of account balance to risk per trade",
            key="settings_risk_pct"
        )
        
        # Max Positions
        st.session_state["max_positions"] = st.slider(
            " Maximum Positions", 
            min_value=1, 
            max_value=10, 
            value=st.session_state["max_positions"],
            help="Maximum number of simultaneous open positions",
            key="settings_max_positions"
        )
        
        # Risk Level Indicator
        risk_level = " HIGH" if st.session_state["risk_pct"] > 3.0 else " MEDIUM" if st.session_state["risk_pct"] > 1.5 else " LOW"
        st.info(f"**Current Risk Level:** {risk_level}")
    
    # ================================
    # RIGHT COLUMN - Strategy Settings
    # ================================
    with settings_col2:
        st.subheader(" Strategy Settings")
        
        # Add scan_interval default if missing
        st.session_state.setdefault("scan_interval", 300)
        
        # Minimum Confidence
        st.session_state.setdefault("min_confidence", 0.65)
        st.session_state["min_confidence"] = st.slider(
            " Minimum Signal Confidence", 
            min_value=0.5, 
            max_value=1.0, 
            value=st.session_state["min_confidence"], 
            step=0.01,
            help="Minimum confidence threshold for trade signals",
            key="settings_min_confidence"
        )
        
        # Scan Interval
        st.session_state["scan_interval"] = st.slider(
            " Scan Interval (seconds)", 
            min_value=60, 
            max_value=600, 
            value=st.session_state["scan_interval"], 
            step=30,
            help="Time between market scans for new opportunities",
            key="settings_scan_interval"
        )
        
        # Auto-trading toggle
        st.session_state.setdefault("auto_trade_enabled", False)
        st.session_state["auto_trade_enabled"] = st.checkbox(
            " Enable Auto-Trading", 
            value=st.session_state["auto_trade_enabled"],
            help="Allow bot to execute trades automatically",
            key="settings_auto_trade"
        )
        
        if st.session_state["auto_trade_enabled"]:
            st.warning(" **Auto-trading ENABLED!** Monitor the bot closely.")
        else:
            st.info(" Auto-trading disabled. Manual approval required.")
    
    # ================================
    # EMAIL NOTIFICATION SYSTEM
    # ================================
    st.markdown("---")
    st.subheader(" Email Notification System")
    
    # Get notification status
    notification_status = get_notification_status()
    
    notification_col1, notification_col2 = st.columns(2)
    
    with notification_col1:
        st.metric("Email System", "... Enabled" if notification_status['enabled'] else " Disabled")
        st.metric("Configuration", "... Ready" if notification_status['configured'] else " Incomplete")
        
        # Test email button
        if st.button(" Send Test Email", key="settings_test_email"):
            with st.spinner("Sending test email..."):
                try:
                    success = send_test_notification()
                    if success:
                        st.success("... Test email sent successfully!")
                    else:
                        st.error(" Failed to send test email.")
                except Exception as e:
                    st.error(f" Email test failed: {e}")
    
    with notification_col2:
        st.metric("Emails Sent (Hour)", notification_status.get('emails_sent_hour', 0))
        st.metric("Queue Size", notification_status.get('queue_size', 0))
        
        if notification_status.get('enabled') and notification_status.get('to_emails'):
            st.info(f" **Recipients:** {', '.join(notification_status['to_emails'])}")
    
    # ================================
    # ACTION BUTTONS
    # ================================
    st.markdown("---")
    button_col1, button_col2, button_col3 = st.columns(3)
    
    with button_col1:
        if st.button(" Save Settings", type="primary", key="save_settings"):
            # Update session with current values
            _log_append("Settings saved successfully")
            st.success("... Settings saved!")
    
    with button_col2:
        if st.button(" Reset to Defaults", key="reset_settings"):
            st.session_state.update({
                "sl_mult": 1.5,
                "tp_mult": 3.0,
                "risk_pct": 2.0,
                "max_positions": 5,
                "min_confidence": 0.65,
                "scan_interval": 300,
                "auto_trade_enabled": False
            })
            st.success(" Settings reset to defaults")
            st.rerun()
    
    with button_col3:
        if st.button(" Test Configuration", key="test_settings"):
            # Validate settings
            issues = []
            if st.session_state["risk_pct"] > 5.0:
                issues.append(" Risk per trade is very high (>5%)")
            if st.session_state["sl_mult"] < 1.0:
                issues.append(" Stop loss multiplier is too low")
            
            if issues:
                st.error("Configuration issues found:")
                for issue in issues:
                    st.write(issue)
            else:
                st.success("... Configuration looks good!")


# ---- LOGS --------------------------------------------------------------------

def render_logs():
    st.header(" System Logs")
    st.caption("Real-time activity, error logs, and module status")
    
    # Log controls
    log_col1, log_col2, log_col3 = st.columns(3)
    
    with log_col1:
        log_limit = st.selectbox("Show Last", [50, 100, 200, "All"], index=0, key="log_limit")
        limit = None if log_limit == "All" else int(log_limit)
    
    with log_col2:
        if st.button(" Refresh", key="logs_refresh"):
            st.rerun()
    
    with log_col3:
        if st.button(" Clear Logs", key="clear_logs"):
            st.session_state["logs"] = []
            st.success("Logs cleared")
            st.rerun()
    
    # Export logs
    logs = st.session_state.get("logs", [])
    if logs:
        log_text = "\n".join(logs)
        st.download_button(
            label=" Download Logs",
            data=log_text,
            file_name=f"trading_logs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            key="download_logs"
        )
    
    st.markdown("---")
    
    # ================================
    # MODULE STATUS SECTION (NEW)
    # ================================
    st.subheader(" Module Status & Controls")
    st.caption("Monitor and control all trading bot modules")
    
    # Initialize demo mode states if not exists
    if 'module_demo_modes' not in st.session_state:
        st.session_state['module_demo_modes'] = {}
    
    # Define all possible modules with their display names and descriptions
    module_definitions = {
        'portfolio_mgr': {
            'name': 'Portfolio Manager',
            'description': 'Manages portfolio balances and positions',
            'component': COMPONENTS.get('portfolio_mgr'),
            'fallback_available': True
        },
        'market_analyzer': {
            'name': 'Market Analyzer', 
            'description': 'Real-time market data and technical analysis',
            'component': COMPONENTS.get('market_analyzer'),
            'fallback_available': True
        },
        'trade_exec': {
            'name': 'Trade Executor',
            'description': 'Executes buy/sell orders on exchange',
            'component': COMPONENTS.get('trade_exec'),
            'fallback_available': True
        },
        'risk_mgr': {
            'name': 'Risk Manager',
            'description': 'Position sizing and risk calculations',
            'component': COMPONENTS.get('risk_mgr'),
            'fallback_available': False
        },
        'quantum_analyzer': {
            'name': 'Quantum Analyzer',
            'description': 'Advanced quantum-based market analysis',
            'component': COMPONENTS.get('quantum_analyzer'),
            'fallback_available': True
        },
        'quantum_trader': {
            'name': 'Quantum Trader',
            'description': 'Quantum-enhanced trading strategies',
            'component': COMPONENTS.get('quantum_trader'),
            'fallback_available': True,
            'disabled_reason': st.session_state.get('_qt_status', '')
        },
        'ensemble_engine': {
            'name': 'Ensemble Signal Engine',
            'description': 'Multi-strategy signal aggregation',
            'component': COMPONENTS.get('ensemble_engine'),
            'fallback_available': False
        }
    }
    
    # Additional system components
    system_components = {
        'binance_client': {
            'name': 'Binance API Client',
            'description': 'Exchange connectivity and API access',
            'component': None,  # We'll check this separately
            'fallback_available': True
        },
        'auto_scanner': {
            'name': 'Auto Scanner',
            'description': 'Background market scanning service',
            'component': st.session_state.get('auto_scanner'),
            'fallback_available': False
        },
        'notification_system': {
            'name': 'Notification System',
            'description': 'Email and alert notifications',
            'component': None,  # We'll check this via get_notification_status
            'fallback_available': True
        }
    }
    
    # Check Binance client status
    try:
        client, client_status = setup_binance_client()
        system_components['binance_client']['component'] = client
    except:
        system_components['binance_client']['component'] = None
    
    # Check notification system
    try:
        notif_status = get_notification_status()
        system_components['notification_system']['component'] = notif_status.get('enabled', False)
    except:
        system_components['notification_system']['component'] = False
    
    # Combine all modules
    all_modules = {**module_definitions, **system_components}
    
    # Module status display
    for module_key, module_info in all_modules.items():
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
            
            # Determine status
            component = module_info['component']
            is_demo_forced = st.session_state['module_demo_modes'].get(module_key, False)
            
            if is_demo_forced:
                status = " DEMO MODE"
                status_text = "Forced Demo"
                can_toggle = True
            elif component is not None and component is not False:
                # Check if it's a fallback component
                component_type = type(component).__name__
                if 'Fallback' in component_type:
                    status = " FALLBACK"
                    status_text = "Using Fallback"
                else:
                    status = " ACTIVE"
                    status_text = "Live Connection"
                can_toggle = True
            else:
                status = " OFFLINE"
                status_text = "Not Available"
                can_toggle = module_info['fallback_available']
            
            with col1:
                st.write(f"**{module_info['name']}**")
                st.caption(module_info['description'])
            
            with col2:
                st.write(status)
                st.caption(status_text)
            
            with col3:
                if component is not None and component is not False:
                    # Show additional info based on component type
                    if hasattr(component, 'get_connection_status'):
                        try:
                            conn_status = component.get_connection_status()
                            st.caption(conn_status[:30] + "..." if len(conn_status) > 30 else conn_status)
                        except:
                            st.caption("Status check failed")
                    elif module_key == 'auto_scanner':
                        st.caption(f"Running: {component.is_running()}")
                    elif module_key == 'notification_system':
                        st.caption(f"Configured: {component}")
                    else:
                        st.caption(f"Type: {type(component).__name__}")
                else:
                    reason = module_info.get('disabled_reason')
                    if reason:
                        st.caption(reason)
                    else:
                        st.caption("No component loaded")
            
            with col4:
                # Control buttons
                if can_toggle:
                    if is_demo_forced:
                        if st.button(" Enable Live", key=f"enable_{module_key}"):
                            st.session_state['module_demo_modes'][module_key] = False
                            _log_append(f"Module {module_info['name']} switched to LIVE mode")
                            st.success(f"{module_info['name']} enabled for live mode")
                            st.rerun()
                    else:
                        if st.button(" Force Demo", key=f"demo_{module_key}"):
                            st.session_state['module_demo_modes'][module_key] = True
                            _log_append(f"Module {module_info['name']} forced to DEMO mode")
                            st.warning(f"{module_info['name']} forced to demo mode")
                            st.rerun()
                else:
                    st.write(" No fallback")
            
            st.divider()
    
    # Global module controls
    st.subheader(" Global Module Controls")
    
    global_col1, global_col2, global_col3 = st.columns(3)
    
    with global_col1:
        if st.button(" Enable All Live", key="enable_all_modules"):
            st.session_state['module_demo_modes'] = {}
            _log_append("All modules enabled for live mode")
            st.success("All compatible modules enabled for live mode")
            st.rerun()
    
    with global_col2:
        if st.button(" Force All Demo", key="demo_all_modules"):
            demo_modes = {}
            for module_key, module_info in all_modules.items():
                if module_info['fallback_available']:
                    demo_modes[module_key] = True
            st.session_state['module_demo_modes'] = demo_modes
            _log_append("All modules forced to demo mode")
            st.warning("All compatible modules forced to demo mode")
            st.rerun()
    
    with global_col3:
        if st.button(" Refresh Modules", key="refresh_all_modules"):
            # Force re-initialization of components
            try:
                # Re-initialize components and update global reference
                new_components, _, _ = initialize_components()
                
                # Update the global COMPONENTS reference
                globals()['COMPONENTS'] = new_components
                st.session_state["_components_cache"] = new_components
                
                _log_append("All modules refreshed")
                st.success("Modules refreshed successfully")
                st.rerun()
            except Exception as e:
                _log_append(f"Module refresh failed: {e}")
                st.error(f"Module refresh failed: {e}")
    
    st.markdown("---")
    
    # Display logs
    st.subheader(f" Recent Activity ({len(logs)} total)")
    _display_logs(limit)


# ------------------------------------------------------------------
# MAIN NAVIGATION ---------------------------------------------------------
# ------------------------------------------------------------------

# Tab selection
TABS = [
    " Dashboard",
    " Portfolio", 
    " Performance",
    " Multi-Strategy",
    " Auto-Trader",
    " Manual Trader",
    " Backtesting",
    " System Health",
    " Settings",
    " Logs",
]

# ------------------------------------------------------------------
# SIDEBAR BRANDING / QUICK INFO
# ------------------------------------------------------------------
with st.sidebar:
    # Company logo and branding
    st.markdown(
        """
        <div style='text-align: center; margin-bottom: 20px;'>
            <img src='https://static.wixstatic.com/media/80aa29_3bdfcbab4dd34671915e3b66b0b596e4~mv2.jpeg/v1/fill/w_146,h_104,al_c,q_80,usm_0.66_1.00_0.01,enc_avif,quality_auto/LRC_1719585575250.jpeg' 
                 width='120' style='border-radius: 8px; margin-bottom: 10px;'/>
            <h3 style='margin: 10px 0; color: #333;'> Hybrid Quantum Trading Bot</h3>
            <p style='margin: 5px 0; color: #666; font-size: 14px;'>
                <strong>Rondanini Publishing Ltd.</strong>
            </p>
            <p style='margin: 0; color: #888; font-size: 12px;'>
                <a href='https://www.rondanini.net' target='_blank' style='color: #888; text-decoration: none;'>
                    www.rondanini.net
                </a>
            </p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    st.markdown("---")
    
    # API Connection Status
    st.subheader(" API Connection")
    try:
        # Get client from components or try to create one
        binance_client = None
        try:
            binance_client, client_status = setup_binance_client()
        except Exception:
            binance_client = None
            client_status = "No Binance client available - running in demo mode"
        
        if binance_client:
            st.success("... Connected")
            try:
                server_time = binance_client.get_server_time()
                server_datetime = datetime.fromtimestamp(server_time['serverTime'] / 1000)
                st.caption(f"Server: {server_datetime.strftime('%H:%M:%S UTC')}")
            except:
                st.caption("Connection established")
        else:
            st.warning(" Demo Mode")
            st.caption("API keys not configured")
    except Exception as e:
        st.error(" Connection Failed")
        st.caption(str(e)[:50])
    
    st.markdown("---")
    
    # Portfolio Value
    st.subheader(" Portfolio")
    try:
        portfolio_value = COMPONENTS['portfolio_mgr'].total_value()
        st.metric("Total Value", f"${portfolio_value:,.2f}")
        
        # Add GBP equivalent
        gbp_rate = get_usd_to_gbp_rate()
        gbp_value = portfolio_value * gbp_rate
        st.caption(f" GBP {gbp_value:,.2f} GBP")
    except Exception as e:
        st.metric("Total Value", "N/A")
        st.caption("Portfolio unavailable")
    
    st.markdown("---")
    
    # Scanner Status
    st.subheader(" Auto Scanner")
    scanner = st.session_state.get('auto_scanner')
    if scanner and scanner.is_running():
        st.success(" Running")
        st.caption(f"Scan #{scanner.scan_count}")
    else:
        st.warning(" Stopped")
        st.caption("Click to start scanning")
    
    # Toggle Scanner button
    if st.button("Toggle Scanner", key="sidebar_toggle_scanner", use_container_width=True):
        if scanner:
            if scanner.is_running():
                scanner.stop_scanning()
                _log_append("Scanner stopped from sidebar")
                st.success("Scanner stopped")
            else:
                scanner.start_scanning() 
                _log_append("Scanner started from sidebar")
                st.success("Scanner started")
            time.sleep(1)  # Brief pause for user feedback
            st.rerun()
    
    st.markdown("---")
    
    # Environment Information
    st.subheader(" System Info")
    
    # Trading mode with color coding
    mode = " TESTNET" if os.getenv("USE_TESTNET", "false").lower() == "true" else " LIVE"
    if "TESTNET" in mode:
        st.info(f"**Mode:** {mode}")
    else:
        st.warning(f"**Mode:** {mode}")
    
    # System metrics
    try:
        health = get_system_health()
        cpu_pct = float(health["CPU"].replace('%', ''))
        mem_pct = float(health["Memory"].replace('%', ''))
        
        # Color code based on usage
        cpu_color = "" if cpu_pct > 80 else "" if cpu_pct > 60 else ""
        mem_color = "" if mem_pct > 80 else "" if mem_pct > 60 else ""
        
        st.text(f"CPU: {cpu_color} {health['CPU']}")
        st.text(f"Memory: {mem_color} {health['Memory']}")
        st.text(f"Threads: {health['Threads']}")
    except Exception as e:
        st.text("CPU: --")
        st.text("Memory: --") 
        st.text("Threads: --")
    
    # Environment details (collapsed by default)
    with st.expander(" Environment Details"):
        st.text(f"Python: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        st.text(f"Streamlit: {st.__version__}")
        st.text(f"Platform: {sys.platform}")
        st.text(f"Process ID: {os.getpid()}")
        
        # Session info
        session_duration = time.time() - st.session_state.get('session_start', time.time())
        st.text(f"Session: {int(session_duration/60)}min")
    
    st.markdown("---")
    
    # Footer
    st.markdown(
        """
        <div style='text-align: center; font-size: 11px; color: #888;'>
             2025 All Rights Reserved<br>
            <em>Advanced Quantum Trading Solutions</em>
        </div>
        """, 
        unsafe_allow_html=True
    )

# Create tabs
tabs = st.tabs(TABS)

# Route to appropriate render function
with tabs[0]:  # Dashboard
    render_dashboard()

with tabs[1]:  # Portfolio
    render_portfolio()

with tabs[2]:  # Performance
    render_performance()

with tabs[3]:  # Multi-Strategy
    render_multi_strategy()

with tabs[4]:  # Auto-Trader
    render_auto_trader()

with tabs[5]:  # Manual Trader
    render_manual_trader()

with tabs[6]:  # Backtesting
    render_backtesting()

with tabs[7]:  # System Health
    render_system_health()

with tabs[8]:  # Settings
    render_settings()

with tabs[9]:  # Logs
    render_logs()


# ------------------------------------------------------------------
# STATUS BAR
# ------------------------------------------------------------------
st.markdown("---")
st.subheader(" System Status")

status_col1, status_col2, status_col3, status_col4 = st.columns(4)

with status_col1:
    # Check if we have a working client
    try:
        client_available = binance_client is not None
        if not 'binance_client' in locals():
            client_available, _ = setup_binance_client()
            client_available = client_available is not None
    except:
        client_available = False
        
    if client_available:
        st.success(" API Connected")
    else:
        st.error(" Demo Mode")

with status_col2:
    scanner = st.session_state.get("auto_scanner")
    if scanner and scanner.is_running():
        st.success(" Scanner Active")
    else:
        st.warning(" Scanner Stopped")

with status_col3:
    auto_trade = st.session_state.get("auto_trade_enabled", False)
    if auto_trade:
        st.success(" Auto-Trade ON")
    else:
        st.info(" Manual Mode")

with status_col4:
    mode = " TESTNET" if os.getenv("USE_TESTNET", "false").lower() == "true" else " LIVE"
    if "TESTNET" in mode:
        st.info(mode)
    else:
        st.warning(mode)


# ------------------------------------------------------------------
# FOOTER
# ------------------------------------------------------------------
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; padding: 20px;'>
        <h4> Hybrid Quantum Crypto Trading Bot</h4>
        <p> Quantum Analytics |  AI Trading |  Advanced Analytics</p>
        <p style='color: #666; font-size: 14px;'>
            <strong>Rondanini Publishing Ltd.</strong> |  2025 All Rights Reserved
        </p>
        <p style='color: #888; font-size: 12px;'>
             <strong>Risk Warning:</strong> Trading involves substantial risk. Past performance does not guarantee future results.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)


# ------------------------------------------------------------------
# MAIN GUARD
# ------------------------------------------------------------------
def main():
    """Main entry point - Streamlit runs everything at module level."""
    pass


if __name__ == "__main__":
    main()
 
 


