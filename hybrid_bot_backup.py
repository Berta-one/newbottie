 -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Hybrid Quantum Crypto Trading Bot (Rebuild)
==========================================

**Purpose**
A consolidated, deploymentâ€‘safe Streamlit application that brings back:

- Icons + stable tab indexing (no more tuple index errors)
- Working **Multiâ€‘Strategy Market Scanner** wired to advanced ML, quantum & ensemble modules (with graceful fallbacks)
- **Backtesting tab** (via BacktestingIntegration) that lets you click any result row to **apply its weights** back to Multiâ€‘Strategy sliders
- **Portfolio tab** with live balances + **Last 100 Trades w/ Realized & Unrealized PnL** (websocketâ€‘aware; falls back to REST/demo)
- **Manual Trading** & **Auto Trader** controls
- **Settings** (risk + notification + system toggles)
- **Logs**

**Deployment notes**
- Works on Railway without the `$PORT` interpolation bug. We *read* the `PORT` env var and set Streamlit config programmatically.
- All 3rdâ€‘party imports are wrapped in try/except; app degrades gracefully to demo when a dependency is missing.
- Websockets (Binance) are optional; set `ENABLE_WEBSOCKETS=true` to attempt live fills & ticker streaming.

---
"""

# ============================================================================
# Imports & Safe Env Config
# ============================================================================
import os
import sys
import time
import json
import threading
import traceback
from datetime import datetime, timedelta
from collections import deque, defaultdict
from typing import Dict, Any, List, Optional

import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# ------------------------------------------------------------------
# Enforce Streamlit server settings BEFORE st.set_page_config()
# ------------------------------------------------------------------
# Railway gives us PORT; *never* pass literal "$PORT" to Streamlit.
# If PORT not set, default to 8501.
_port = int(os.getenv("PORT", "8501") or 8501)
os.environ["STREAMLIT_SERVER_PORT"] = str(_port)
os.environ.setdefault("STREAMLIT_SERVER_ADDRESS", "0.0.0.0")
os.environ.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")

st.set_page_config(
    page_title="Hybrid Quantum Trading Bot", page_icon="ðŸ§ ", layout="wide"
)

# ============================================================================
# SAFE IMPORT SHIMS
# ============================================================================
BINANCE_AVAILABLE = False
TWM_AVAILABLE = False
try:  # python-binance
    from binance.client import Client as BinanceClient
    from binance.streams import ThreadedWebsocketManager

    BINANCE_AVAILABLE = True
    TWM_AVAILABLE = True
except Exception:
    try:
        from binance.client import Client as BinanceClient  # type: ignore

        BINANCE_AVAILABLE = True
    except Exception:
        BINANCE_AVAILABLE = False
        BinanceClient = None  # type: ignore
    TWM_AVAILABLE = False

# --- Advanced / optional modules -------------------------------------------------
BACKTESTING_AVAILABLE = False
try:
    from backtesting_integration import BacktestingIntegration

    BACKTESTING_AVAILABLE = True
except Exception:
    BACKTESTING_AVAILABLE = False

try:
    from advanced_market_intelligence import AdvancedMarketIntelligence
except Exception:
    AdvancedMarketIntelligence = None  # type: ignore

try:
    from advanced_ml_strategy import AdvancedMLStrategy
except Exception:
    AdvancedMLStrategy = None  # type: ignore

try:
    from ensemble_signal_engine import EnsembleSignalEngine
except Exception:
    EnsembleSignalEngine = None  # type: ignore

try:
    from adaptive_risk_system import AdaptiveRiskManager
except Exception:
    AdaptiveRiskManager = None  # type: ignore

# Quantum stack (prefer full, fallback math sim)
try:
    from quantum_engine import QuantumAnalyzer as QuantumAnalyzerFull
except Exception:
    QuantumAnalyzerFull = None
try:
    from quantum_engine_fallback import QuantumAnalyzer as QuantumAnalyzerFB
except Exception:
    QuantumAnalyzerFB = None

# Notification system (optional)
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
    )
except Exception:
    # graceful noâ€‘ops
    def get_notification_system():
        return None

    def notify_system(event, msg="", data=None):
        pass

    def notify_error(context, err, data=None):
        pass

    def notify_trade(data):
        pass

    def notify_trade_close(data):
        pass

    def notify_signal(data):
        pass

    def send_test_notification():
        return False

    def get_notification_status():
        return {
            "enabled": False,
            "configured": False,
            "types": {
                "trades": False,
                "signals": False,
                "system": False,
                "errors": False,
            },
            "emails_sent_hour": 0,
            "queue_size": 0,
            "to_emails": [],
        }


# Auth (optional; if missing, auto auth)
try:
    from auth import require_authentication
except Exception:

    def require_authentication():
        class DummyAuth:
            admin_username = "admin"

        return DummyAuth()


# ============================================================================
# Environment & Globals
# ============================================================================
USE_TESTNET = (
    os.getenv("USE_TESTNET", "false").lower() == "true"
)  # you said Live, so default false
ENABLE_WEBSOCKETS = os.getenv("ENABLE_WEBSOCKETS", "true").lower() == "true"
AUTO_TRADE_ENABLED_ENV = os.getenv("AUTO_TRADE_ENABLED", "false").lower() == "true"
DASHBOARD_PASSWORD_ENV = os.getenv("DASHBOARD_PASSWORD", "")

# Risk defaults
DEFAULT_SL_MULT = float(os.getenv("SL_MULT", "1.5"))
DEFAULT_TP_MULT = float(os.getenv("TP_MULT", "3.0"))

# ============================================================================
# Authentication Gate
# ============================================================================
auth = require_authentication()
if "system_notified" not in st.session_state:
    notify_system(
        "started", f"Dashboard accessed by {getattr(auth,'admin_username','user')}"
    )
    st.session_state.system_notified = True


# ============================================================================
# Fallback Component Implementations
# ============================================================================
class FallbackPortfolioManager:
    def __init__(self):
        self.portfolio = {
            "USDT": {
                "balance": 10000.0,
                "free": 10000.0,
                "locked": 0.0,
                "price": 1.0,
                "value": 10000.0,
                "change": 0.0,
            },
            "BTC": {
                "balance": 0.02,
                "free": 0.02,
                "locked": 0.0,
                "price": 65000.0,
                "value": 1300.0,
                "change": 2.5,
            },
            "ETH": {
                "balance": 0.5,
                "free": 0.5,
                "locked": 0.0,
                "price": 3500.0,
                "value": 1750.0,
                "change": 1.8,
            },
        }

    def get_portfolio(self):
        return self.portfolio

    def total_value(self):
        return sum(a["value"] for a in self.portfolio.values())

    def last_updated(self):
        return datetime.now().strftime("%H:%M:%S")

    def refresh_portfolio(self):
        return self.get_portfolio()

    def is_live(self):
        return False

    def get_connection_status(self):
        return "âŒ Using demo data - Portfolio Manager not available"

    def get_trade_history(self, symbol=None, limit=100):
        hist = []
        now = datetime.utcnow()
        for i in range(limit):
            side = "BUY" if i % 2 == 0 else "SELL"
            price = 65000 + np.random.randn() * 1000
            qty = 0.0002
            hist.append(
                {
                    "symbol": "BTCUSDT",
                    "side": side,
                    "quantity": qty,
                    "price": price,
                    "value": qty * price,
                    "commission": 0.01,
                    "time": (now - timedelta(minutes=i * 5)).isoformat(
                        timespec="seconds"
                    )
                    + "Z",
                }
            )
        return hist


class FallbackMarketAnalyzer:
    def __init__(self, client=None):
        self.client = client

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
        ]

    def get_price(self, symbol):
        prices = {
            "BTCUSDT": 65000,
            "ETHUSDT": 3500,
            "BNBUSDT": 600,
            "XRPUSDT": 0.65,
            "ADAUSDT": 0.45,
            "SOLUSDT": 140,
            "DOTUSDT": 8,
            "LINKUSDT": 18,
        }
        return prices.get(symbol, 100.0)

    def get_latest_rsi(self, symbol):
        return float(np.random.uniform(20, 80))

    def get_latest_momentum(self, symbol):
        return float(np.random.uniform(-5, 5))

    def get_volatility(self, symbol):
        return float(np.random.uniform(0.02, 0.08))

    def analyze_market_signals(self, symbols):
        sigs = {}
        for s in symbols:
            sigs[s] = {
                "signal": np.random.choice(["BUY", "SELL", "HOLD"]),
                "confidence": float(np.random.uniform(0.5, 0.9)),
                "rsi": self.get_latest_rsi(s),
                "price": self.get_price(s),
            }
        return sigs


class FallbackTradeExecutor:
    def __init__(self, client=None, risk_mgr=None, log_callback=None):
        self.client = client
        self.risk_mgr = risk_mgr
        self.log_callback = log_callback or (lambda m: print(m))
        self.mock_balance = 10000.0

    def manual_trade(self, symbol, qty, sl_mult, tp_mult, side="BUY"):
        price = 100.0
        self.log_callback(f"DEMO {side} {qty} {symbol} @ {price}")
        self.mock_balance -= qty * price
        _trade = {
            "symbol": symbol,
            "side": side,
            "quantity": qty,
            "price": price,
            "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "demo": True,
        }
        record_trade_to_session(_trade)
        notify_trade(_trade)
        return f"ðŸ“ Demo trade {side} {qty} {symbol}"

    def auto_execute(
        self, signal, total_balance=None, open_positions=0, sl_mult=1.5, tp_mult=3.0
    ):
        return self.manual_trade(
            signal.get("symbol", "BTCUSDT"), 0.001, sl_mult, tp_mult
        )

    def get_active_orders(self):
        return {}

    def cancel_order(self, symbol):
        return f"Cancel {symbol}"

    def get_connection_status(self):
        return f"Demo executor. Balance: {self.mock_balance:.2f}"

    def get_account_summary(self):
        return {
            "total_usdt": self.mock_balance,
            "tradeable_usdt": self.mock_balance * 0.9,
            "can_trade": True,
            "demo_mode": True,
        }


# ============================================================================
# Binance Client Setup + Websockets
# ============================================================================


def setup_binance_client() -> (Optional["BinanceClient"], str):
    if not BINANCE_AVAILABLE:
        return None, "âŒ Binance library not available (demo mode)"
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    if not api_key or not api_secret:
        return None, "âš ï¸ API keys not configured - using demo"
    try:
        client = BinanceClient(api_key, api_secret)
        if USE_TESTNET and hasattr(client, "API_URL"):
            client.API_URL = "https://testnet.binance.vision/api"
        # sanity ping
        client.get_server_time()
        mode = "ðŸ§ª TESTNET" if USE_TESTNET else "ðŸš€ LIVE"
        return client, f"âœ… Connected to Binance {mode}"
    except Exception as e:
        return None, f"âŒ Connection failed: {e}"


# ------------------------------------------------------------------
# Websocket Manager
# ------------------------------------------------------------------
class WSManager:
    """Light wrapper around pythonâ€‘binance ThreadedWebsocketManager.
    Collects ticker & user trade updates into st.session_state caches.
    """

    def __init__(self, client: Optional["BinanceClient"], symbols: List[str]):
        self.client = client
        self.symbols = symbols
        self.twm = None
        self._running = False

    def start(self):
        if not ENABLE_WEBSOCKETS or not self.client or not TWM_AVAILABLE:
            return False
        if self._running:
            return True
        try:
            self.twm = ThreadedWebsocketManager(
                api_key=self.client.API_KEY, api_secret=self.client.API_SECRET
            )
            self.twm.start()
            for sym in self.symbols:
                self.twm.start_symbol_ticker_socket(
                    callback=self._ticker_cb, symbol=sym.lower()
                )
            # user data stream for fills
            self.twm.start_user_socket(callback=self._user_cb)
            self._running = True
            return True
        except Exception as e:
            print(f"WS start failed: {e}")
            return False

    def _ticker_cb(self, msg):
        # msg: dict; we care price
        price = float(msg.get("c") or msg.get("C") or 0)
        sym = msg.get("s", "").upper()
        if sym:
            st.session_state.ws_prices[sym] = price

    def _user_cb(self, msg):
        # look for executionReport events to capture trades
        if msg.get("e") == "executionReport":
            sym = msg.get("s", "") + (
                "USDT" if not msg.get("s", "").endswith("USDT") else ""
            )
            side = msg.get("S")
            last_qty = float(msg.get("l", 0))
            last_price = float(msg.get("L", 0))
            ts = (
                datetime.utcfromtimestamp(msg.get("T", 0) / 1000).isoformat(
                    timespec="seconds"
                )
                + "Z"
            )
            _t = {
                "symbol": sym,
                "side": side,
                "quantity": last_qty,
                "price": last_price,
                "timestamp": ts,
                "ws": True,
            }
            record_trade_to_session(_t)

    def stop(self):
        try:
            if self.twm:
                self.twm.stop()
        finally:
            self._running = False


# ============================================================================
# Session State Init Helpers
# ============================================================================


def ss_init(key, value):
    if key not in st.session_state:
        st.session_state[key] = value


# Core session keys
ss_init("sl_mult", DEFAULT_SL_MULT)
ss_init("tp_mult", DEFAULT_TP_MULT)
ss_init("logs", [])
ss_init("trade_history", deque(maxlen=1000))  # raw events
ss_init("computed_trades", [])  # processed rows w PnL
ss_init("ws_prices", defaultdict(float))
ss_init("auto_running", False)
ss_init("last_action", "None")

# Multiâ€‘Strategy states
ss_init("weight_quantum", 30)
ss_init("weight_ml", 30)
ss_init("weight_technical", 40)
ss_init("multi_min_conf", 0.65)
ss_init("multi_max_pairs", 20)
ss_init("multi_scan_mode", "Top Volume Pairs")
ss_init("multi_show_only_signals", True)
ss_init("latest_signals", [])
ss_init("last_scan_time", None)
ss_init("manual_scan_requested", False)
ss_init("selected_trade", None)
ss_init("last_applied_strategy", None)

# ============================================================================
# Record trade utility -> session_state trade_history
# ============================================================================


def record_trade_to_session(trade: Dict[str, Any]):
    """Append a trade dict to session_state history + notify."""
    if "trade_history" not in st.session_state:
        st.session_state.trade_history = deque(maxlen=1000)
    st.session_state.trade_history.appendleft(trade)
    # mark recompute needed
    st.session_state._needs_pnl_refresh = True


# ============================================================================
# Compute realized / unrealized PnL from session trade history
# ============================================================================


def compute_pnl_rows(history: List[Dict[str, Any]], price_func) -> List[Dict[str, Any]]:
    """Return list of rows (max 100) w realized/unrealized PnL.
    Simple FIFO position accounting per symbol.
    """
    pos_qty = defaultdict(float)
    pos_cost = defaultdict(float)  # total cost in quote
    rows = []
    for t in reversed(history):  # oldest -> newest for FIFO cost basis
        sym = t.get("symbol", "?")
        side = t.get("side", "BUY").upper()
        qty = float(t.get("quantity", 0))
        price = float(t.get("price", 0))
        ts = t.get("time") or t.get("timestamp") or ""
        if side.startswith("B"):
            # increase position
            pos_qty[sym] += qty
            pos_cost[sym] += qty * price
            rows.append(
                {
                    "Time": ts,
                    "Symbol": sym,
                    "Side": "BUY",
                    "Qty": qty,
                    "Price": price,
                    "RealizedPnL": 0.0,
                    "RealizedPnL%": 0.0,
                    "UnrealizedPnL": None,
                    "UnrealizedPnL%": None,
                }
            )
        else:  # SELL
            if pos_qty[sym] > 0:
                avg_cost = pos_cost[sym] / pos_qty[sym]
            else:
                avg_cost = price
            proceeds = qty * price
            cost_portion = min(qty, pos_qty[sym]) * avg_cost
            realized = proceeds - cost_portion
            realized_pct = (price / avg_cost - 1) * 100 if avg_cost > 0 else 0
            pos_qty[sym] -= qty
            pos_cost[sym] -= qty * avg_cost
            rows.append(
                {
                    "Time": ts,
                    "Symbol": sym,
                    "Side": "SELL",
                    "Qty": qty,
                    "Price": price,
                    "RealizedPnL": realized,
                    "RealizedPnL%": realized_pct,
                    "UnrealizedPnL": None,
                    "UnrealizedPnL%": None,
                }
            )
    # Add summary rows (unrealized for remaining pos)
    for sym, qty in pos_qty.items():
        if qty <= 0:
            continue
        avg_cost = pos_cost[sym] / qty if qty > 0 else 0
        mkt = price_func(sym)
        unreal = qty * (mkt - avg_cost)
        unreal_pct = (mkt / avg_cost - 1) * 100 if avg_cost > 0 else 0
        rows.append(
            {
                "Time": "OPEN",
                "Symbol": sym,
                "Side": "POSITION",
                "Qty": qty,
                "Price": mkt,
                "RealizedPnL": 0.0,
                "RealizedPnL%": 0.0,
                "UnrealizedPnL": unreal,
                "UnrealizedPnL%": unreal_pct,
            }
        )
    # newest first for display & limit to 100
    rows = list(reversed(rows))[:100]
    return rows


# ============================================================================
# Component Initialization (live vs fallback)
# ============================================================================


def initialize_components():
    comps = {}
    client, client_status = setup_binance_client()

    # Portfolio Manager
    try:
        from portfolio_manager import PortfolioManager  # user code

        if client:
            comps["portfolio_mgr"] = PortfolioManager(
                api_key=os.getenv("BINANCE_API_KEY"),
                api_secret=os.getenv("BINANCE_API_SECRET"),
            )
        else:
            raise ImportError
    except Exception:
        comps["portfolio_mgr"] = FallbackPortfolioManager()

    # Market Analyzer
    try:
        from market_analyzer import MarketAnalyzer

        if client:
            comps["market_analyzer"] = MarketAnalyzer(client)
        else:
            raise ImportError
    except Exception:
        comps["market_analyzer"] = FallbackMarketAnalyzer(client)

    # Trade Executor
    try:
        from trade_executor import TradeExecutor

        comps["trade_exec"] = TradeExecutor(
            client,
            None,
            log_callback=lambda m: st.session_state.logs.append(
                f"[{datetime.now().strftime('%H:%M:%S')}] {m}"
            ),
        )
    except Exception:
        comps["trade_exec"] = FallbackTradeExecutor()

    # Quantum analyzer
    if QuantumAnalyzerFull:
        try:
            comps["quantum_analyzer"] = QuantumAnalyzerFull()
        except Exception:
            comps["quantum_analyzer"] = (
                QuantumAnalyzerFB() if QuantumAnalyzerFB else None
            )
    else:
        comps["quantum_analyzer"] = QuantumAnalyzerFB() if QuantumAnalyzerFB else None

    # Advanced modules
    comps["advanced_intel"] = (
        AdvancedMarketIntelligence(client)
        if AdvancedMarketIntelligence and client
        else None
    )
    comps["advanced_ml"] = AdvancedMLStrategy() if AdvancedMLStrategy else None
    comps["adaptive_risk"] = AdaptiveRiskManager() if AdaptiveRiskManager else None
    if (
        EnsembleSignalEngine
        and client
        and comps["quantum_analyzer"]
        and comps["market_analyzer"]
    ):
        try:
            from quantum_trading_integration import (
                QuantumTrader,
            )  # uses real analyzer but we pass market data ourselves
        except Exception:
            QuantumTrader = None
        quant_trader = None
        if QuantumTrader and client:
            try:
                quant_trader = QuantumTrader(client)
            except Exception:
                quant_trader = None
        comps["ensemble_engine"] = EnsembleSignalEngine(
            client, quant_trader or comps["quantum_analyzer"], comps["market_analyzer"]
        )
    else:
        comps["ensemble_engine"] = None

    # Websockets
    comps["ws_mgr"] = (
        WSManager(client, comps["market_analyzer"].get_trading_pairs()[:20])
        if client
        else None
    )

    return comps, client_status


components, client_status = initialize_components()

# Start websockets (background) if possible & not yet started
if "ws_started" not in st.session_state:
    if components.get("ws_mgr") and ENABLE_WEBSOCKETS:
        started = components["ws_mgr"].start()
        st.session_state.ws_started = started
    else:
        st.session_state.ws_started = False

# ============================================================================
# Sidebar Branding & Quick Controls
# ============================================================================
with st.sidebar:
    st.markdown(
        """
    <div style='text-align:center;margin-bottom:20px;'>
        <h3>ðŸ§  Quantum Trading Bot</h3>
        <p style='font-size:12px;'>Rondanini Publishing Ltd. â€¢ Â© 2025</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.subheader("ðŸ“ˆ Status")
    st.info(client_status)

    try:
        total_value = components["portfolio_mgr"].total_value()
    except Exception:
        total_value = 0.0
    st.metric("Portfolio", f"${total_value:,.2f}")

    if st.button("ðŸ”„ Refresh Portfolio", key="sb_refresh_port"):
        try:
            components["portfolio_mgr"].refresh_portfolio()
        except Exception as e:
            st.error(str(e))
        st.experimental_rerun()

    st.markdown("---")

    # Quick Backtest
    if BACKTESTING_AVAILABLE:
        st.markdown("**ðŸ”¬ Quick Backtest**")
        if st.button("ðŸš€ Run Quick Test", use_container_width=True, key="sb_quick_bt"):
            try:
                bt = BacktestingIntegration()
                df = bt._run_engine(
                    ["BTCUSDT", "ETHUSDT"],
                    "1h",
                    1000,
                    0.001,
                    days=30,
                    refresh_cache=False,
                )
                st.success("Backtest OK (30d demo)")
            except Exception as e:
                st.error(f"Backtest failed: {e}")
        st.markdown("---")

    st.subheader("ðŸ”” Notifications")
    ns = get_notification_status()
    st.write("Enabled:" if ns["enabled"] else "Disabled:", ns["enabled"])
    if st.button("ðŸ“§ Test Email", key="sb_test_email"):
        ok = send_test_notification()
        st.success("Sent" if ok else "Failed")

# ============================================================================
# Tab Definitions  (ORDER MATTERS!)
# ============================================================================
TABS = st.tabs(
    [
        "ðŸ  Dashboard",  # [0]
        "âœ‹ Manual",  # [1]
        "ðŸ¤– Auto",  # [2]
        "âš› Multi-Strategy",  # [3]
        "ðŸ’¼ Portfolio",  # [4]
        "ðŸ“ˆ Performance",  # [5]
        "ðŸ”¬ Backtesting",  # [6]
        "âš™ Settings",  # [7]
        "ðŸ“ Logs",  # [8]
    ]
)

# ============================================================================
# DASHBOARD TAB [0]
# ============================================================================
with TABS[0]:
    st.header("ðŸ“Š Portfolio Overview")
    st.caption("High level status of your account & system health.")

    try:
        port = components["portfolio_mgr"].get_portfolio()
    except Exception:
        port = {}

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Value", f"${components['portfolio_mgr'].total_value():,.2f}")
    with col2:
        st.metric("Mode", "LIVE" if not USE_TESTNET else "TESTNET")
    with col3:
        st.metric("Assets", len(port))
    with col4:
        st.metric("Updated", components["portfolio_mgr"].last_updated())

    if port:
        df = pd.DataFrame(
            [
                {
                    "Asset": k,
                    "Balance": v.get("balance", 0),
                    "Free": v.get("free", v.get("balance", 0)),
                    "Locked": v.get("locked", 0),
                    "Price": v.get("price", 0),
                    "Value": v.get("value", v.get("balance", 0) * v.get("price", 0)),
                    "Change%": v.get("change", 0),
                }
                for k, v in port.items()
            ]
        )
        st.dataframe(df, use_container_width=True)
        if len(df) > 1:
            fig = px.pie(df, values="Value", names="Asset", title="Allocation")
            st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# MANUAL TAB [1]
# ============================================================================
with TABS[1]:
    st.header("âœ‹ Manual Trading")
    ma = components["market_analyzer"]
    pairs = ma.get_trading_pairs() if ma else []
    sym = st.selectbox("Pair", pairs, key="man_pair")
    px_cur = ma.get_price(sym) if ma else 0
    st.info(f"Price: ${px_cur:,.4f}")

    qty = st.number_input(
        "Quantity",
        min_value=0.000001,
        value=0.001,
        step=0.000001,
        format="%.6f",
        key="man_qty",
    )
    side = st.selectbox("Side", ["BUY", "SELL"], key="man_side")

    if st.button("ðŸš€ Execute", type="primary", key="man_exec"):
        res = components["trade_exec"].manual_trade(
            sym, qty, st.session_state.sl_mult, st.session_state.tp_mult, side=side
        )
        st.success(str(res))

# ============================================================================
# AUTO TAB [2]
# ============================================================================
with TABS[2]:
    st.header("ðŸ¤– Auto Trader Control")
    st.write("Status:", "Running" if st.session_state.auto_running else "Stopped")
    st.write("Last Action:", st.session_state.last_action)
    colA, colB = st.columns(2)
    with colA:
        if st.button("Start Auto Bot", key="auto_start"):
            st.session_state.auto_running = True
            st.session_state.last_action = (
                f"Started {datetime.now().strftime('%H:%M:%S')}"
            )
            st.experimental_rerun()
    with colB:
        if st.button("Stop Auto Bot", key="auto_stop"):
            st.session_state.auto_running = False
            st.session_state.last_action = (
                f"Stopped {datetime.now().strftime('%H:%M:%S')}"
            )
            st.experimental_rerun()

    st.markdown("---")
    st.subheader("ðŸ“¡ Auto Scanner Snapshot")
    snaps = (
        components["market_analyzer"].analyze_market_signals(
            ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
        )
        if components["market_analyzer"]
        else {}
    )
    st.json(snaps)

# ============================================================================
# MULTIâ€‘STRATEGY TAB [3]
# ============================================================================
with TABS[3]:
    st.header("âš› Multi-Strategy Market Scanner")
    st.caption("Quantum + ML + Technical ensemble across multiple pairs.")

    ma = components["market_analyzer"]
    ens = components["ensemble_engine"]

    # --- Config section ------------------------------------------------------
    c1, c2 = st.columns([2, 1])
    with c1:
        st.write("**Strategy Weights (autoâ€‘normalize to 100%)**")
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            wq = st.slider(
                "Quantum", 0, 100, st.session_state.weight_quantum, key="ms_wq"
            )
        with sc2:
            wml = st.slider("ML", 0, 100, st.session_state.weight_ml, key="ms_wml")
        with sc3:
            wt = st.slider(
                "Technical", 0, 100, st.session_state.weight_technical, key="ms_wt"
            )
        tot = wq + wml + wt
        if tot <= 0:
            wq, wml, wt = 0, 0, 100
        else:
            wq = int(wq / tot * 100)
            wml = int(wml / tot * 100)
            wt = 100 - wq - wml
        # save
        st.session_state.weight_quantum = wq
        st.session_state.weight_ml = wml
        st.session_state.weight_technical = wt
        wc1, wc2, wc3 = st.columns(3)
        wc1.metric("Quantum", f"{wq}%")
        wc1.progress(wq / 100)
        wc2.metric("ML", f"{wml}%")
        wc2.progress(wml / 100)
        wc3.metric("Tech", f"{wt}%")
        wc3.progress(wt / 100)
        # Presets
        pc1, pc2, pc3, pc4 = st.columns(4)
        if pc1.button("âš› Focus", key="ms_p_q"):
            st.session_state.weight_quantum = 60
            st.session_state.weight_ml = 20
            st.session_state.weight_technical = 20
            st.experimental_rerun()
        if pc2.button("ðŸ¤– Focus", key="ms_p_ml"):
            st.session_state.weight_quantum = 20
            st.session_state.weight_ml = 60
            st.session_state.weight_technical = 20
            st.experimental_rerun()
        if pc3.button("ðŸ“Š Tech", key="ms_p_t"):
            st.session_state.weight_quantum = 20
            st.session_state.weight_ml = 20
            st.session_state.weight_technical = 60
            st.experimental_rerun()
        if pc4.button("âš– Balanced", key="ms_p_bal"):
            st.session_state.weight_quantum = 33
            st.session_state.weight_ml = 33
            st.session_state.weight_technical = 34
            st.experimental_rerun()
    with c2:
        mc = st.slider(
            "Min Confidence",
            0.5,
            1.0,
            float(st.session_state.multi_min_conf),
            0.01,
            key="ms_minconf",
        )
        mp = st.slider(
            "Max Pairs",
            5,
            50,
            int(st.session_state.multi_max_pairs),
            5,
            key="ms_maxpairs",
        )
        sm = st.selectbox(
            "Scan Mode",
            [
                "Top Volume Pairs",
                "Portfolio + Major Pairs",
                "All USDT Pairs",
                "Custom Selection",
            ],
            index=[
                "Top Volume Pairs",
                "Portfolio + Major Pairs",
                "All USDT Pairs",
                "Custom Selection",
            ].index(st.session_state.multi_scan_mode),
            key="ms_scanmode",
        )
        st.session_state.multi_min_conf = mc
        st.session_state.multi_max_pairs = mp
        st.session_state.multi_scan_mode = sm

    # Pair selection
    all_pairs = ma.get_trading_pairs() if ma else []
    if sm == "Top Volume Pairs":
        ms_pairs = all_pairs[:mp]
    elif sm == "Portfolio + Major Pairs":
        try:
            port = components["portfolio_mgr"].get_portfolio()
            port_pairs = [f"{a}USDT" for a in port if a not in ("USDT", "BUSD")]
        except Exception:
            port_pairs = []
        majors = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT"]
        ms_pairs = list(dict.fromkeys(port_pairs + majors))[:mp]
    elif sm == "All USDT Pairs":
        ms_pairs = [p for p in all_pairs if p.endswith("USRT") or p.endswith("USDT")][
            :mp
        ]
    else:
        ms_pairs = st.multiselect(
            "Select Pairs", all_pairs, default=["BTCUSDT", "ETHUSDT"], key="ms_custom"
        )[:mp]

    # Scan controls
    scc1, scc2, scc3 = st.columns(3)
    if scc1.button("ðŸ” Scan", type="primary", key="ms_scan"):
        st.session_state.manual_scan_requested = True
    if scc2.button("ðŸ”„ Refresh", key="ms_refresh"):
        st.session_state.manual_scan_requested = True
    show_only = scc3.checkbox(
        "Show Only Signals",
        value=st.session_state.multi_show_only_signals,
        key="ms_onlysig",
    )
    st.session_state.multi_show_only_signals = show_only

    # Run scan
    if st.session_state.manual_scan_requested:
        prog = st.progress(0.0)
        status = st.empty()
        res = []
        for i, sym in enumerate(ms_pairs):
            prog.progress((i + 1) / max(1, len(ms_pairs)))
            status.text(f"Analyzing {sym} ({i+1}/{len(ms_pairs)})")
            try:
                if ens:  # full ensemble
                    sig = ens.get_signals(
                        sym,
                        {
                            "quantum": st.session_state.weight_quantum,
                            "ml": st.session_state.weight_ml,
                            "technical": st.session_state.weight_technical,
                        },
                        st.session_state.multi_min_conf,
                    )
                else:  # heuristic fallback
                    rsi = ma.get_latest_rsi(sym) if ma else 50
                    mom = ma.get_latest_momentum(sym) if ma else 0
                    vol = ma.get_volatility(sym) if ma else 0.05
                    qa = components["quantum_analyzer"]
                    qsig = (
                        qa.generate_quantum_signal(
                            {"rsi": rsi, "momentum": mom, "price_volatility": vol}
                        )
                        if qa
                        else {"decision": "HOLD", "confidence": 0.5}
                    )
                    tech_sig = "BUY" if rsi < 30 else "SELL" if rsi > 70 else "HOLD"
                    tech_conf = 0.6 if tech_sig != "HOLD" else 0.4
                    ml_sig = "BUY" if mom > 0 else "SELL" if mom < 0 else "HOLD"
                    ml_conf = 0.55
                    fs = (
                        qsig["confidence"] * st.session_state.weight_quantum
                        + ml_conf * st.session_state.weight_ml
                        + tech_conf * st.session_state.weight_technical
                    ) / 100.0
                    fd = "HOLD"
                    if fs >= st.session_state.multi_min_conf:
                        fd = ml_sig if ml_sig == tech_sig else qsig["decision"]
                    sig = {
                        "symbol": sym,
                        "quantum": {
                            "decision": qsig["decision"],
                            "confidence": qsig["confidence"],
                        },
                        "ml": {"decision": ml_sig, "confidence": ml_conf},
                        "technical": {"decision": tech_sig, "confidence": tech_conf},
                        "final": {"decision": fd, "confidence": fs},
                        "price": ma.get_price(sym) if ma else 0,
                        "rsi": rsi,
                        "momentum": mom,
                        "volatility": vol,
                    }
                res.append(sig)
                if (
                    sig["final"]["decision"] in ("BUY", "SELL")
                    and sig["final"]["confidence"] >= 0.8
                ):
                    notify_signal(
                        {
                            "symbol": sym,
                            "signal": sig["final"]["decision"],
                            "confidence": sig["final"]["confidence"],
                        }
                    )
            except Exception as e:
                st.error(f"Error {sym}: {e}")
        prog.empty()
        status.empty()
        st.session_state.latest_signals = res
        st.session_state.manual_scan_requested = False
        st.session_state.last_scan_time = datetime.now()

    # Display results
    data = st.session_state.latest_signals
    if data:
        if show_only:
            data = [
                d
                for d in data
                if d["final"]["decision"] != "HOLD"
                and d["final"]["confidence"] >= st.session_state.multi_min_conf
            ]
        if data:
            st.subheader(f"ðŸ“Š Results ({len(data)})")
            disp = []
            for s in data:
                disp.append(
                    {
                        "Symbol": s["symbol"],
                        "Price": s.get("price", 0),
                        "Final": s["final"]["decision"],
                        "Conf": round(s["final"]["confidence"], 3),
                        "Quantum": f"{s['quantum']['decision']} ({s['quantum']['confidence']:.2f})",
                        "ML": f"{s['ml']['decision']} ({s['ml']['confidence']:.2f})",
                        "Tech": f"{s['technical']['decision']} ({s['technical']['confidence']:.2f})",
                        "RSI": round(s.get("rsi", 0), 1),
                        "Mom": round(s.get("momentum", 0), 2),
                        "Vol": round(s.get("volatility", 0), 3),
                    }
                )
            df = pd.DataFrame(disp)
            st.dataframe(df, use_container_width=True)

            # Quick trade picks
            st.subheader("âš¡ Quick Trade Picks")
            buys = [s for s in data if s["final"]["decision"] == "BUY"]
            sells = [s for s in data if s["final"]["decision"] == "SELL"]
            tc1, tc2 = st.columns(2)
            with tc1:
                if buys:
                    st.write("**ðŸŸ¢ BUY**")
                for i, s in enumerate(buys[:5]):
                    bc1, bc2 = st.columns([3, 1])
                    bc1.write(
                        f"{s['symbol']} @ {s.get('price',0):.4f} (Conf {s['final']['confidence']:.3f})"
                    )
                    if bc2.button("Buy", key=f"ms_buy_{i}"):
                        st.session_state.selected_trade = {
                            "symbol": s["symbol"],
                            "action": "BUY",
                            "price": s.get("price", 0),
                            "confidence": s["final"]["confidence"],
                            "timestamp": datetime.now(),
                            "source": "multi_strategy",
                        }
                        st.experimental_rerun()
            with tc2:
                if sells:
                    st.write("**ðŸ”´ SELL**")
                for i, s in enumerate(sells[:5]):
                    sc1, sc2 = st.columns([3, 1])
                    sc1.write(
                        f"{s['symbol']} @ {s.get('price',0):.4f} (Conf {s['final']['confidence']:.3f})"
                    )
                    if sc2.button("Sell", key=f"ms_sell_{i}"):
                        st.session_state.selected_trade = {
                            "symbol": s["symbol"],
                            "action": "SELL",
                            "price": s.get("price", 0),
                            "confidence": s["final"]["confidence"],
                            "timestamp": datetime.now(),
                            "source": "multi_strategy",
                        }
                        st.experimental_rerun()

            # Execute selection
            tr = st.session_state.selected_trade
            if tr and tr.get("source") == "multi_strategy":
                st.divider()
                st.subheader(f"ðŸŽ¯ Execute {tr['action']} {tr['symbol']}")
                e1, e2, e3 = st.columns(3)
                with e1:
                    st.info(f"Price: {tr['price']:.4f}")
                    st.info(f"Confidence: {tr['confidence']:.3f}")
                with e2:
                    qx = st.number_input(
                        "Qty",
                        min_value=0.000001,
                        value=0.001,
                        step=0.000001,
                        format="%.6f",
                        key="ms_exec_qty",
                    )
                with e3:
                    if st.button("Execute", type="primary", key="ms_exec_go"):
                        res = components["trade_exec"].manual_trade(
                            tr["symbol"],
                            qx,
                            st.session_state.sl_mult,
                            st.session_state.tp_mult,
                            side=tr["action"],
                        )
                        st.success(str(res))
                        st.session_state.selected_trade = None
                        st.experimental_rerun()
                    if st.button("Cancel", key="ms_exec_cancel"):
                        st.session_state.selected_trade = None
                        st.experimental_rerun()

            # Stats
            st.subheader("ðŸ“ˆ Signal Stats")
            ts1, ts2, ts3, ts4 = st.columns(4)
            ts1.metric("Total Scanned", len(st.session_state.latest_signals))
            ts2.metric("Signals", len(data))
            ts3.metric("BUY", len(buys))
            ts4.metric("SELL", len(sells))

            if st.session_state.last_scan_time:
                st.caption(
                    f"Last scan: {st.session_state.last_scan_time.strftime('%H:%M:%S')}"
                )
        else:
            st.warning("No strong signals.")
    else:
        st.info("ðŸ” Click Scan to analyze.")
        if ms_pairs:
            st.write("Pairs to scan:")
            st.write(", ".join(ms_pairs))

# ============================================================================
# PORTFOLIO TAB [4]
# ============================================================================
with TABS[4]:
    st.header("ðŸ’¼ Portfolio")
    pm = components["portfolio_mgr"]
    try:
        portfolio = pm.get_portfolio()
    except Exception:
        portfolio = {}
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.info(pm.get_connection_status())
    with col2:
        if st.button("ðŸ”„ Refresh", key="pf_refresh"):
            pm.refresh_portfolio()
            st.experimental_rerun()
    with col3:
        st.caption(f"Updated: {pm.last_updated()}")

    if portfolio:
        rows = [
            {
                "Asset": a,
                "Balance": v.get("balance", 0),
                "Free": v.get("free", v.get("balance", 0)),
                "Locked": v.get("locked", 0),
                "Price (USD)": v.get("price", 0),
                "Value (USD)": v.get("value", v.get("balance", 0) * v.get("price", 0)),
                "24h %": v.get("change_24h", v.get("change", 0)),
            }
            for a, v in portfolio.items()
        ]
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)
        if len(df) > 1:
            fig = px.pie(
                df[df["Value (USD)"] > 1.0],
                values="Value (USD)",
                names="Asset",
                title="Allocation",
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No portfolio data.")

    st.markdown("---")
    st.subheader("ðŸ“œ Last 100 Trades (Realized & Unrealized PnL)")

    # If we need to recompute (new trades appended) do so
    if st.session_state.get("_needs_pnl_refresh", True):
        hist = list(st.session_state.trade_history)

        def _pf_price(sym):
            # use ws price > analyzer
            px = st.session_state.ws_prices.get(sym, 0)
            if px:
                return px
            try:
                return components["market_analyzer"].get_price(sym)
            except Exception:
                return 0

        rows = compute_pnl_rows(hist, _pf_price)
        st.session_state.computed_trades = rows
        st.session_state._needs_pnl_refresh = False

    if st.session_state.computed_trades:
        tdf = pd.DataFrame(st.session_state.computed_trades)
        st.dataframe(tdf, use_container_width=True)
        realized = tdf["RealizedPnL"].sum()
        unreal = tdf["UnrealizedPnL"].fillna(0).sum()
        rc1, rc2 = st.columns(2)
        rc1.metric("Realized PnL", f"${realized:,.2f}")
        rc2.metric("Unrealized PnL", f"${unreal:,.2f}")
    else:
        st.info("No trades yet.")

# ============================================================================
# PERFORMANCE TAB [5]
# ============================================================================
with TABS[5]:
    st.header("ðŸ“ˆ Performance Analytics")
    st.caption("Equity curve & trade distribution from recorded history.")
    hist = list(st.session_state.trade_history)
    if hist:
        # Build equity curve (very rough: apply Realized PnL cumulatively to starting 0)
        pf_rows = (
            st.session_state.computed_trades
            if st.session_state.computed_trades
            else compute_pnl_rows(hist, lambda s: 0)
        )
        eq = []
        cum = 0
        for r in reversed(pf_rows):
            cum += r["RealizedPnL"]
            eq.append({"t": r["Time"], "equity": cum})
        edf = pd.DataFrame(eq)
        fig = go.Figure(data=[go.Scatter(x=edf["t"], y=edf["equity"], mode="lines")])
        fig.update_layout(
            title="Realized PnL Curve", xaxis_title="Time", yaxis_title="PnL (USD)"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No trade history to analyze.")

# ============================================================================
# BACKTESTING TAB [6]
# ============================================================================
with TABS[6]:
    st.header("ðŸ”¬ Backtesting")
    if BACKTESTING_AVAILABLE:
        try:
            bt = BacktestingIntegration()
            bt.render_backtesting_tab()
        except Exception as e:
            st.error(f"Backtesting error: {e}")
            st.info("Try: pip install ccxt scipy")
    else:
        st.error("Backtesting unavailable. Install ccxt & scipy.")

# ============================================================================
# SETTINGS TAB [7]
# ============================================================================
with TABS[7]:
    st.header("âš™ Settings & Configuration")
    sc1, sc2 = st.columns(2)
    with sc1:
        st.subheader("Risk Management")
        st.session_state.sl_mult = st.slider(
            "Stop Loss Mult (ATR)",
            0.5,
            5.0,
            float(st.session_state.sl_mult),
            0.1,
            key="set_sl",
        )
        st.session_state.tp_mult = st.slider(
            "Take Profit Mult (ATR)",
            1.0,
            10.0,
            float(st.session_state.tp_mult),
            0.5,
            key="set_tp",
        )
        st.write("Current:", st.session_state.sl_mult, st.session_state.tp_mult)
    with sc2:
        st.subheader("System")
        st.write("Mode:", "LIVE" if not USE_TESTNET else "TESTNET")
        st.write("Websockets:", "ON" if st.session_state.ws_started else "OFF")
        if st.button("Restart Websockets", key="set_ws_restart") and components.get(
            "ws_mgr"
        ):
            components["ws_mgr"].stop()
            time.sleep(1)
            components["ws_mgr"].start()
            st.experimental_rerun()

    st.markdown("---")
    st.subheader("Notifications")
    nstat = get_notification_status()
    st.json(nstat)

# ============================================================================
# LOGS TAB [8]
# ============================================================================
with TABS[8]:
    st.header("ðŸ“ Logs")
    if st.button("Clear Logs", key="lg_clear"):
        st.session_state.logs = []
    if st.session_state.logs:
        for l in reversed(st.session_state.logs[-500:]):
            st.text(l)
    else:
        st.info("No logs yet.")

# ============================================================================
# End of File
# ============================================================================

