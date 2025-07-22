#!/usr/bin/env python3
"""
Hybrid Bot Test v2
==================

**Purpose**: Clean, testable rebuild of your trading dashboard **without overwriting your prod `hybrid_bot.py`**.

### What's new in this build
- ✅ **New tab order** (as requested):
  1. Dashboard
  2. Portfolio
  3. Performance (NEW: last 100 trades + PnL + GBP equiv)
  4. Multi-Strategy Scanner (quantum+ML+tech weights, scan + quick trade)
  5. Auto-Trader (scanner status + control)
  6. Manual Trader
  7. Backtesting (with days selector + push weights to Multi-Strategy)
  8. System Health
  9. Settings
 10. Logs
- ✅ Unique `key=` values everywhere (fixes duplicated widget ID errors).
- ✅ Graceful **module auto-import with fallbacks** (uses your advanced modules if present).
- ✅ **GBP conversion** helper with API + env fallback.
- ✅ Central **trade logging**; any manual or quick trade logs to `logs/trade_history.csv`.
- ✅ Performance tab computes **realized & mark-to-market PnL** when possible.
- ✅ Safe for local testing (`streamlit run hybrid_bot_test_v2.py`).
- ✅ No `$PORT` crash — we detect hosting env & set server port automatically when needed.

---
**NOTE**: This file intentionally *does not* include every last advanced UI embellishment from your prod bot. The goal is a stable functional baseline. Once you're happy, we'll merge features forward.
"""

import os
import sys
import time
import csv
import json
import traceback
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import psutil
import streamlit as st

# ------------------------------------------------------------------
# Streamlit page config ASAP (before rendering widgets)
# ------------------------------------------------------------------
st.set_page_config(page_title="Hybrid Bot Test", page_icon="🤖", layout="wide")

# ------------------------------------------------------------------
# ENV / HOST FIXES (Railway / local)
# ------------------------------------------------------------------
# If running on Railway, Streamlit sometimes chokes on non-int env vars.
# We'll sanitize STREAMLIT_SERVER_PORT before Streamlit reads it.
if "STREAMLIT_SERVER_PORT" in os.environ:
    # Some deploys inject "$PORT" literal. Replace with numeric when possible.
    port_env = os.environ["STREAMLIT_SERVER_PORT"]
    if not port_env.isdigit():
        port_fallback = os.getenv("PORT", "8501")
        os.environ["STREAMLIT_SERVER_PORT"] = str(port_fallback)

# Force listen 0.0.0.0 in container hosts
if "RAILWAY_ENVIRONMENT" in os.environ:
    os.environ.setdefault("STREAMLIT_SERVER_ADDRESS", "0.0.0.0")

# ------------------------------------------------------------------
# Authentication stub (replace with your real auth.require_authentication)
# ------------------------------------------------------------------
try:
    from auth import require_authentication  # your real module
except Exception:  # fallback
    def require_authentication():
        class _Auth:
            admin_username = "local-user"
        return _Auth()

auth = require_authentication()

# ------------------------------------------------------------------
# Notification system (graceful fallback)
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
    )
except Exception:  # fallbacks are silent no-ops
    def _noop(*_, **__):
        return None
    get_notification_system = _noop
    notify_system = _noop
    notify_error = _noop
    notify_trade = _noop
    notify_trade_close = _noop
    notify_signal = _noop
    send_test_notification = _noop
    def get_notification_status():
        return {
            "enabled": False,
            "configured": False,
            "types": {"trades": False, "signals": False, "system": False, "errors": False},
            "emails_sent_hour": 0,
            "queue_size": 0,
            "to_emails": [],
        }

# ------------------------------------------------------------------
# Optional / Advanced modules auto-import matrix
# ------------------------------------------------------------------
modules: Dict[str, Any] = {}
_import_attempts = [
    ("portfolio_manager", "PortfolioManager"),
    ("market_analyzer", "MarketAnalyzer"),
    ("trade_executor", "TradeExecutor"),
    ("risk_manager", "RiskManager"),
    ("ensemble_signal_engine", "EnsembleSignalEngine"),
    ("quantum_trading_integration", "QuantumTrader"),
    ("quantum_engine", "QuantumAnalyzer"),  # primary
    ("quantum_engine_fallback", "QuantumAnalyzer"),  # alt name; last wins
    ("advanced_market_intelligence", "AdvancedMarketIntelligence"),
    ("adaptive_risk_system", "AdaptiveRiskManager"),
    ("advanced_ml_strategy", "AdvancedMLStrategy"),
]

# Binance client is special
try:
    from binance.client import Client
    modules["Client"] = Client
except Exception as e:  # maybe not installed yet
    modules["Client"] = None
    print(f"⚠️ Binance client import failed: {e}")

for mod_path, cls_name in _import_attempts:
    try:
        mod = __import__(mod_path, fromlist=[cls_name])
        modules[cls_name] = getattr(mod, cls_name)
    except Exception as e:
        modules[cls_name] = None
        print(f"(module missing) {cls_name}: {e}")

# Backtesting Integration
try:
    from backtesting_integration import BacktestingIntegration
    BACKTESTING_AVAILABLE = True
except Exception as e:
    BacktestingIntegration = None
    BACKTESTING_AVAILABLE = False
    print(f"⚠️ Backtesting unavailable: {e}")

# ------------------------------------------------------------------
# Fallback Implementations
# ------------------------------------------------------------------
class FallbackPortfolioManager:
    def __init__(self):
        self._demo_portfolio = {
            'USDT': {'balance': 10000.0, 'free': 10000.0, 'locked': 0.0, 'price': 1.0, 'value': 10000.0, 'change_24h': 0.0},
            'BTC': {'balance': 0.02, 'free': 0.02, 'locked': 0.0, 'price': 65000.0, 'value': 1300.0, 'change_24h': 1.5},
            'ETH': {'balance': 0.5, 'free': 0.5, 'locked': 0.0, 'price': 3500.0, 'value': 1750.0, 'change_24h': 2.3},
        }
    def get_portfolio(self):
        return self._demo_portfolio
    def total_value(self):
        return sum(v['value'] for v in self._demo_portfolio.values())
    def last_updated(self):
        return datetime.now().strftime("%H:%M:%S")
    def refresh_portfolio(self):
        return self._demo_portfolio
    def is_live(self):
        return False
    def get_connection_status(self):
        return "Demo portfolio"
    def get_trade_history(self, symbol=None, limit=100):
        demo = []
        now = datetime.utcnow()
        for i in range(min(limit, 10)):
            demo.append({
                "symbol": "BTCUSDT",
                "side": "BUY" if i % 2 == 0 else "SELL",
                "quantity": 0.0005,
                "price": 60000 + i * 100,
                "value": 0.0005 * (60000 + i * 100),
                "commission": 0.01,
                "time": (now - timedelta(minutes=i*5)).isoformat(),
            })
        return demo

class FallbackMarketAnalyzer:
    def __init__(self, client=None):
        self.client = client
    def get_trading_pairs(self):
        return ['BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT','XRPUSDT','ADAUSDT']
    def get_price(self, symbol):
        prices = {
            'BTCUSDT': 65000.0,'ETHUSDT': 3500.0,'BNBUSDT': 600.0,'SOLUSDT': 200.0,'XRPUSDT': 0.6,'ADAUSDT':0.45
        }
        return prices.get(symbol, 1.0)
    def get_latest_rsi(self, symbol):
        return np.random.uniform(30,70)
    def get_latest_momentum(self, symbol):
        return np.random.uniform(-5,5)
    def get_volatility(self, symbol):
        return np.random.uniform(0.01,0.08)
    def analyze_market_signals(self, symbols:List[str]):
        out={}
        for s in symbols:
            out[s]={
                'signal': np.random.choice(['BUY','SELL','HOLD']),
                'confidence': np.random.uniform(0.5,0.9),
                'rsi': self.get_latest_rsi(s),
                'price': self.get_price(s)
            }
        return out

class FallbackTradeExecutor:
    def __init__(self, client=None, risk_mgr=None, log_callback=None):
        self.client=client
        self.risk_mgr=risk_mgr
        self.log_callback=log_callback or (lambda m: print(m))
        self._mock_balance=10000.0
    def manual_trade(self, symbol, qty=None, sl_mult=1.5, tp_mult=3.0, trade_amount_usd=None):
        # NO side param here -> we will pass only supported args
        price = components['market_analyzer'].get_price(symbol) if 'market_analyzer' in components else 1.0
        if trade_amount_usd:
            qty = trade_amount_usd/price
        elif qty is None:
            qty = 50/price
        notional = qty*price
        self._mock_balance -= notional
        msg=f"Demo trade {symbol} qty={qty:.6f} @ {price:.2f} (${notional:.2f})"
        self.log_callback(msg)
        _record_trade(symbol, 'BUY', qty, price, notional, fee=notional*0.001, execution_type='demo')
        return msg
    def auto_execute(self, signal, total_balance=None, open_positions=0, sl_mult=1.5, tp_mult=3.0):
        symbol = signal.get('symbol','BTCUSDT')
        return self.manual_trade(symbol, trade_amount_usd=25.0)
    def get_active_orders(self):
        return {}
    def cancel_order(self, symbol):
        return f"Cancel {symbol} (demo)"
    def get_connection_status(self):
        return f"Demo executor bal=${self._mock_balance:,.2f}"
    def get_account_summary(self):
        return {'total_usdt': self._mock_balance,'tradeable_usdt': self._mock_balance*0.9,'can_trade':True,'demo_mode':True}

# ------------------------------------------------------------------
# Binance client setup
# ------------------------------------------------------------------
def setup_binance_client():
    ClientCls = modules.get('Client')
    if ClientCls is None:
        return None, "Binance client unavailable (not installed)."
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    if not api_key or not api_secret:
        return None, "API keys not set – running in demo mode."
    try:
        client = ClientCls(api_key, api_secret)
        # Force live (user request) unless env says testnet
        if os.getenv("USE_TESTNET", "false").lower() == "true":
            client.API_URL = 'https://testnet.binance.vision/api'
        client.get_server_time()  # connectivity check
        mode = "TESTNET" if 'testnet' in getattr(client, 'API_URL','').lower() else "LIVE"
        return client, f"Connected to Binance {mode}."
    except Exception as e:
        return None, f"Binance connection failed: {e}"

# ------------------------------------------------------------------
# Component initialization (safe, layered fallbacks)
# ------------------------------------------------------------------
def initialize_components():
    comps:Dict[str,Any]={}

    client, client_status = setup_binance_client()

    # Risk Manager (optional)
    RiskMgrCls = modules.get('RiskManager')
    if RiskMgrCls:
        try:
            comps['risk_mgr'] = RiskMgrCls(max_risk_percent=0.02, max_positions=5)
        except Exception as e:
            print(f"RiskMgr init fail: {e}")
            comps['risk_mgr']=None
    else:
        comps['risk_mgr']=None

    # Portfolio Manager
    PortMgrCls = modules.get('PortfolioManager')
    if PortMgrCls and client:
        try:
            comps['portfolio_mgr'] = PortMgrCls(api_key=os.getenv('BINANCE_API_KEY'), api_secret=os.getenv('BINANCE_API_SECRET'))
        except Exception as e:
            print(f"PortMgr fail: {e}")
            comps['portfolio_mgr']=FallbackPortfolioManager()
    else:
        comps['portfolio_mgr']=FallbackPortfolioManager()

    # Market Analyzer
    MktCls = modules.get('MarketAnalyzer')
    if MktCls and client:
        try:
            comps['market_analyzer']=MktCls(client)
        except Exception as e:
            print(f"MarketAnalyzer fail: {e}")
            comps['market_analyzer']=FallbackMarketAnalyzer(client)
    else:
        comps['market_analyzer']=FallbackMarketAnalyzer(client)

    # Trade Executor (no-side signature)
    TradeExecCls = modules.get('TradeExecutor')
    if TradeExecCls and client:
        try:
            comps['trade_exec']=TradeExecCls(client, comps.get('risk_mgr'), log_callback=_append_log)
        except Exception as e:
            print(f"TradeExecutor fail: {e}")
            comps['trade_exec']=FallbackTradeExecutor(client, comps.get('risk_mgr'), log_callback=_append_log)
    else:
        comps['trade_exec']=FallbackTradeExecutor(client, comps.get('risk_mgr'), log_callback=_append_log)

    # Quantum Analyzer (prefer real -> fallback)
    QA_real = modules.get('QuantumAnalyzer')  # may have been overwritten by fallback import; handle next
    if QA_real:
        try:
            comps['quantum_analyzer']=QA_real()
        except Exception as e:
            print(f"QuantumAnalyzer primary fail: {e}")
            comps['quantum_analyzer']=None
    else:
        comps['quantum_analyzer']=None

    # Quantum Trader wrapper (optional)
    QTCls = modules.get('QuantumTrader')
    if QTCls and client:
        try:
            comps['quantum_trader']=QTCls(client)
        except Exception as e:
            print(f"QuantumTrader fail: {e}")
            comps['quantum_trader']=None
    else:
        comps['quantum_trader']=None

    return comps, client, client_status

# ------------------------------------------------------------------
# Logging Utilities & Trade History persistence
# ------------------------------------------------------------------
LOG_DIR = Path("logs"); LOG_DIR.mkdir(exist_ok=True)
TRADE_LOG_PATH = LOG_DIR / "trade_history.csv"

# st.session_state log list init done after components

def _append_log(msg:str):
    ts = datetime.now().strftime('%H:%M:%S')
    st.session_state.setdefault('logs',[]).append(f"[{ts}] {msg}")

# trade recorder ensures CSV exists with header
TRADE_HEADER = ["timestamp","symbol","side","quantity","price","notional_usd","fee_usd","execution_type"]

def _ensure_trade_log_header():
    if not TRADE_LOG_PATH.exists():
        with TRADE_LOG_PATH.open('w', newline='') as f:
            csv.writer(f).writerow(TRADE_HEADER)

_ensure_trade_log_header()


def _record_trade(symbol:str, side:str, qty:float, price:float, notional:float, fee:float=0.0, execution_type:str="manual"):
    _ensure_trade_log_header()
    with TRADE_LOG_PATH.open('a', newline='') as f:
        csv.writer(f).writerow([
            datetime.utcnow().isoformat(),symbol,side,qty,price,notional,fee,execution_type
        ])
    notify_trade({
        'symbol':symbol,'side':side,'quantity':qty,'price':price,'value':notional,
        'timestamp':datetime.utcnow().isoformat(),'execution_type':execution_type
    })
    _append_log(f"Trade logged {side} {qty} {symbol} @ {price}")


def load_trade_history(max_rows:int=100) -> pd.DataFrame:
    rows=[]
    if TRADE_LOG_PATH.exists():
        try:
            df = pd.read_csv(TRADE_LOG_PATH)
            rows.append(df)
        except Exception as e:
            print(f"trade log read fail: {e}")
    # Also include portfolio_mgr trade history (if any)
    try:
        ph = components['portfolio_mgr'].get_trade_history(limit=max_rows)
        if ph:
            dfh = pd.DataFrame(ph)
            # standardize cols
            rename_map={
                'value':'notional_usd','commission':'fee_usd','time':'timestamp','qty':'quantity'
            }
            for k,v in rename_map.items():
                if k in dfh.columns and v not in dfh.columns:
                    dfh.rename(columns={k:v}, inplace=True)
            # ensure required
            for col in TRADE_HEADER:
                if col not in dfh.columns:
                    dfh[col] = np.nan
            rows.append(dfh[TRADE_HEADER])
    except Exception as e:
        print(f"portfolio trade hist fail: {e}")
    if not rows:
        return pd.DataFrame(columns=TRADE_HEADER)
    df_all=pd.concat(rows,ignore_index=True)
    df_all.drop_duplicates(subset=["timestamp","symbol","side","price"], inplace=True)
    df_all.sort_values("timestamp", ascending=False, inplace=True)
    return df_all.head(max_rows).reset_index(drop=True)

# ------------------------------------------------------------------
# GBP conversion helper
# ------------------------------------------------------------------
GBP_RATE_CACHE_KEY='gbp_rate_cache'

def _fetch_usd_gbp_rate(timeout=5)->float:
    # quick multi-endpoint fallback
    apis=[
        "https://api.exchangerate-api.com/v4/latest/USD",
        "https://open.er-api.com/v6/latest/USD",
        "https://api.fxratesapi.com/latest?base=USD",
    ]
    for url in apis:
        try:
            import requests
            r=requests.get(url,timeout=timeout)
            if r.status_code==200:
                data=r.json()
                if 'rates' in data and 'GBP' in data['rates']:
                    return float(data['rates']['GBP'])
                # alt schema
                if 'GBP' in data:
                    return float(data['GBP'])
        except Exception:
            continue
    # env fallback
    env_rate=os.getenv('USD_GBP_RATE')
    if env_rate:
        try:return float(env_rate)
        except:pass
    return 0.79  # static fallback


def get_usd_to_gbp_rate(cache_minutes=30)->float:
    now=time.time()
    cache=st.session_state.get(GBP_RATE_CACHE_KEY)
    if cache and (now-cache['ts'])<cache_minutes*60:
        return cache['rate']
    rate=_fetch_usd_gbp_rate()
    st.session_state[GBP_RATE_CACHE_KEY]={'rate':rate,'ts':now}
    return rate

# ------------------------------------------------------------------
# AutoScanner background thread
# ------------------------------------------------------------------
class AutoScanner:
    def __init__(self, market_analyzer, scan_interval=300):
        self.market_analyzer=market_analyzer
        self.scan_interval=scan_interval
        self.running=False
        self.thread=None
        self.last_scan_results={}
        self.scan_count=0
    def start_scanning(self):
        if self.running: return
        self.running=True
        self.thread=threading.Thread(target=self._loop,daemon=True)
        self.thread.start()
    def stop_scanning(self):
        self.running=False
    def _loop(self):
        while self.running:
            try:
                self.scan_count+=1
                symbols=['BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT','XRPUSDT']
                sigs=self.market_analyzer.analyze_market_signals(symbols)
                strong={s:d for s,d in sigs.items() if d.get('confidence',0)>0.6 and d.get('signal')!="HOLD"}
                self.last_scan_results={
                    'timestamp':datetime.utcnow(),
                    'total_scanned':len(symbols),
                    'signals_found':len(strong),
                    'strong_signals':strong,
                    'scan_number':self.scan_count,
                }
            except Exception as e:
                print(f"scanner err: {e}")
            time.sleep(self.scan_interval)
    def get_latest_results(self):
        return self.last_scan_results
    def is_running(self):
        return self.running

# ------------------------------------------------------------------
# Initialize components & session state
# ------------------------------------------------------------------
components, client, client_status = initialize_components()

if 'logs' not in st.session_state:
    st.session_state['logs']=[
        f"[{datetime.now().strftime('%H:%M:%S')}] Bot session started",
        f"[{datetime.now().strftime('%H:%M:%S')}] {client_status}",
    ]
if 'sl_mult' not in st.session_state: st.session_state['sl_mult']=1.5
if 'tp_mult' not in st.session_state: st.session_state['tp_mult']=3.0
if 'auto_scanner' not in st.session_state: st.session_state['auto_scanner']=AutoScanner(components['market_analyzer'])

# ------------------------------------------------------------------
# SIDEBAR BRANDING / QUICK INFO
# ------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🤖 Hybrid Bot Test")
    st.caption(f"Welcome {auth.admin_username}")
    st.markdown("---")
    # API status
    if client:
        st.success("Binance Connected")
    else:
        st.warning("Demo Mode")
    st.caption(client_status)
    # Portfolio quick metric
    try:
        st.metric("Portfolio Value", f"${components['portfolio_mgr'].total_value():,.2f}")
    except Exception:
        st.metric("Portfolio Value","--")
    st.markdown("---")
    # Scanner
    scan=st.session_state['auto_scanner']
    if scan.is_running():
        st.success("Scanner Running")
    else:
        st.warning("Scanner Stopped")
    if st.button("Toggle Scanner", key="sb_toggle_scanner"):
        if scan.is_running(): scan.stop_scanning()
        else: scan.start_scanning()
        st.rerun()
    st.markdown("---")
    # System metrics
    try:
        st.metric("CPU", f"{psutil.cpu_percent()}%")
        st.metric("Mem", f"{psutil.virtual_memory().percent}%")
    except Exception:
        pass
    st.markdown("---")
    st.caption("© 2025 Rondanini Publishing Ltd.")

# ------------------------------------------------------------------
# Tabs (NEW ORDER)
# ------------------------------------------------------------------
TAB_LABELS=[
    "🏠 Dashboard",
    "💼 Portfolio",
    "📈 Performance",
    "⚛ Multi-Strategy",
    "🤖 Auto-Trader",
    "✋ Manual Trader",
    "🔬 Backtesting",
    "🩺 System Health",
    "⚙️ Settings",
    "📝 Logs",
]

_t = st.tabs(TAB_LABELS)
(
    tab_dashboard,
    tab_portfolio,
    tab_performance,
    tab_multistrat,
    tab_autotrader,
    tab_manual,
    tab_backtest,
    tab_syshealth,
    tab_settings,
    tab_logs,
) = _t

# ==================================================================
# TAB 1: DASHBOARD (overview metrics)
# ==================================================================
with tab_dashboard:
    st.header("📊 Dashboard Overview")
    st.info(client_status)

    # top metrics row
    try:
        port_val = components['portfolio_mgr'].total_value()
    except Exception:
        port_val = 0.0
    gbp_rate = get_usd_to_gbp_rate()
    port_val_gbp = port_val * gbp_rate
    col1,col2,col3,col4 = st.columns(4)
    with col1: st.metric("Total USD", f"${port_val:,.2f}")
    with col2: st.metric("Total GBP", f"£{port_val_gbp:,.2f}")
    with col3: st.metric("Mode", "LIVE" if client else "DEMO")
    scan = st.session_state['auto_scanner']
    with col4: st.metric("Scanner", "Running" if scan.is_running() else "Stopped")

    st.markdown("---")
    st.subheader("Recent Trades")
    df_tr = load_trade_history(10)
    if df_tr.empty:
        st.info("No trades yet.")
    else:
        st.dataframe(df_tr, use_container_width=True)

# ==================================================================
# TAB 2: PORTFOLIO
# ==================================================================
with tab_portfolio:
    st.header("💼 Portfolio")
    st.caption("Live balances (or demo fallback)")

    colr1,colr2 = st.columns([1,1])
    with colr1: st.info(components['portfolio_mgr'].get_connection_status())
    with colr2:
        if st.button("🔄 Refresh Portfolio", key="pf_refresh"):
            components['portfolio_mgr'].refresh_portfolio(); st.rerun()

    try:
        portfolio = components['portfolio_mgr'].get_portfolio()
    except Exception as e:
        st.error(f"Portfolio error: {e}")
        portfolio={}

    if portfolio:
        rows=[]
        for asset,data in portfolio.items():
            rows.append({
                "Asset":asset,
                "Balance":data.get('balance',0.0),
                "Free":data.get('free',data.get('balance',0.0)),
                "Locked":data.get('locked',0.0),
                "Price (USD)":data.get('price',0.0),
                "Value (USD)":data.get('value',data.get('balance',0.0)*data.get('price',0.0)),
                "24h %":data.get('change_24h',0.0),
            })
        dfp=pd.DataFrame(rows)
        dfp['Value (GBP)']=dfp['Value (USD)']*gbp_rate
        st.dataframe(dfp, use_container_width=True)

        # pie
        sig=dfp[dfp['Value (USD)']>1]
        if len(sig)>1:
            import plotly.express as px
            fig=px.pie(sig,values='Value (USD)',names='Asset',title='Allocation')
            st.plotly_chart(fig,use_container_width=True)

    else:
        st.warning("No portfolio data.")

# ==================================================================
# TAB 3: PERFORMANCE (last 100 trades + PnL + GBP)
# ==================================================================
with tab_performance:
    st.header("📈 Performance")
    st.caption("Last 100 trades with realized & mark-to-market PnL")

    df_hist=load_trade_history(100)
    if df_hist.empty:
        st.info("No trade history to display.")
    else:
        # ensure numeric
        for c in ['quantity','price','notional_usd','fee_usd']:
            if c in df_hist.columns:
                df_hist[c]=pd.to_numeric(df_hist[c],errors='coerce')
        # mark current prices
        mkt=components['market_analyzer']
        cur_prices={s:mkt.get_price(s) for s in df_hist['symbol'].dropna().unique()}
        df_hist['mark_price_usd']=df_hist['symbol'].map(cur_prices)
        # realized PnL naive FIFO across symbol
        pnl_real=[]; pos_qty={}; pos_cost={}
        for _,r in df_hist.iloc[::-1].iterrows():  # oldest first
            sym=r['symbol']; side=r['side']; qty=r['quantity']; px=r['price']; val=qty*px
            if side in ('BUY','BUY_LONG','LONG'):
                pos_qty[sym]=pos_qty.get(sym,0)+qty
                pos_cost[sym]=pos_cost.get(sym,0)+val
                pnl_real.append(0.0)
            elif side in ('SELL','SELL_SHORT','SHORT'):
                held=pos_qty.get(sym,0)
                if held>0:
                    avg_cost=pos_cost[sym]/held if held else 0
                    closed_qty=min(qty,held)
                    pnl=(px-avg_cost)*closed_qty
                    # reduce position
                    pos_qty[sym]-=closed_qty
                    pos_cost[sym]-=avg_cost*closed_qty
                else:
                    pnl=0.0
                pnl_real.append(pnl)
            else:
                pnl_real.append(0.0)
        pnl_real = pnl_real[::-1]  # reverse back to current order
        df_hist['realized_pnl_usd']=pnl_real
        # unrealized vs mark price (if still holding)
        df_hist['unrealized_pnl_usd']=(df_hist['mark_price_usd']-df_hist['price'])*df_hist['quantity']
        df_hist['realized_pnl_gbp']=df_hist['realized_pnl_usd']*gbp_rate
        df_hist['unrealized_pnl_gbp']=df_hist['unrealized_pnl_usd']*gbp_rate
        st.dataframe(df_hist, use_container_width=True)

        tot_real=df_hist['realized_pnl_usd'].sum()
        tot_unrl=df_hist['unrealized_pnl_usd'].sum()
        win_trades=(df_hist['realized_pnl_usd']>0).sum()
        closed_trades=(df_hist['realized_pnl_usd']!=0).sum()
        win_rate= (win_trades/closed_trades*100) if closed_trades else 0
        colp1,colp2,colp3,colp4=st.columns(4)
        with colp1: st.metric("Realized PnL USD", f"${tot_real:,.2f}")
        with colp2: st.metric("Unrealized PnL USD", f"${tot_unrl:,.2f}")
        with colp3: st.metric("Win Rate", f"{win_rate:.1f}%")
        with colp4: st.metric("Trades", len(df_hist))

# ==================================================================
# TAB 4: MULTI-STRATEGY SCANNER
# (lightweight version; we'll later wire advanced modules)
# ==================================================================
with tab_multistrat:
    st.header("⚛ Multi-Strategy Market Scanner")
    st.caption("Quantum + ML + Technical weights; scan & quick trade.")

    # session defaults
    ss=st.session_state
    ss.setdefault('ms_weight_quantum',30)
    ss.setdefault('ms_weight_ml',30)
    ss.setdefault('ms_weight_technical',40)
    ss.setdefault('ms_min_conf',0.65)
    ss.setdefault('ms_max_pairs',20)
    ss.setdefault('ms_mode','Top Volume Pairs')
    ss.setdefault('ms_show_only',True)
    ss.setdefault('ms_signals',[])
    ss.setdefault('ms_last_scan',None)

    c1,c2=st.columns([2,1])
    with c1:
        st.write("**Strategy Weights (sum=100)**")
        s1,s2,s3=st.columns(3)
        with s1:
            q=st.slider("Quantum %",0,100,ss.ms_weight_quantum,key="ms_wq")
        with s2:
            ml=st.slider("ML %",0,100,ss.ms_weight_ml,key="ms_wm")
        with s3:
            te=st.slider("Technical %",0,100,ss.ms_weight_technical,key="ms_wt")
        tot=q+ml+te
        if tot>0:
            q=int(q/tot*100); ml=int(ml/tot*100); te=100-q-ml
        ss.ms_weight_quantum=q; ss.ms_weight_ml=ml; ss.ms_weight_technical=te
        m1,m2,m3=st.columns(3)
        with m1: st.metric("Quantum",f"{q}%"); st.progress(q/100)
        with m2: st.metric("ML",f"{ml}%"); st.progress(ml/100)
        with m3: st.metric("Tech",f"{te}%"); st.progress(te/100)
    with c2:
        minc=st.slider("Min Conf",0.5,1.0,float(ss.ms_min_conf),0.01,key="ms_mc")
        maxp=st.slider("Max Pairs",5,50,int(ss.ms_max_pairs),5,key="ms_mp")
        mode=st.selectbox("Scan Mode",["Top Volume Pairs","Portfolio + Major Pairs","All USDT Pairs","Custom"],index=["Top Volume Pairs","Portfolio + Major Pairs","All USDT Pairs","Custom"].index(ss.ms_mode),key="ms_mode_sel")
        ss.ms_min_conf=minc; ss.ms_max_pairs=maxp; ss.ms_mode=mode

    all_pairs=components['market_analyzer'].get_trading_pairs()
    if ss.ms_mode=="Top Volume Pairs":
        scan_pairs=all_pairs[:ss.ms_max_pairs]
    elif ss.ms_mode=="Portfolio + Major Pairs":
        try:
            pf=components['portfolio_mgr'].get_portfolio()
            pf_pairs=[f"{a}USDT" for a in pf.keys() if a not in ('USDT','BUSD')]
        except Exception:
            pf_pairs=[]
        majors=['BTCUSDT','ETHUSDT','BNBUSDT','XRPUSDT','ADAUSDT','SOLUSDT']
        scan_pairs=list(dict.fromkeys(pf_pairs+majors))[:ss.ms_max_pairs]
    elif ss.ms_mode=="All USDT Pairs":
        scan_pairs=[p for p in all_pairs if p.endswith('USDT')][:ss.ms_max_pairs]
    else:
        scan_pairs=st.multiselect("Pairs",all_pairs,default=['BTCUSDT','ETHUSDT','BNBUSDT'],key="ms_custom")[:ss.ms_max_pairs]

    cScan1,cScan2,cScan3=st.columns(3)
    with cScan1:
        if st.button("🔍 Scan",key="ms_scan_btn"): ss.ms_do_scan=True
    with cScan2:
        if st.button("🔄 Refresh",key="ms_refresh_btn"): ss.ms_do_scan=True
    with cScan3:
        ss.ms_show_only = st.checkbox("Only Strong", value=ss.ms_show_only, key="ms_only")

    if ss.get('ms_do_scan'):
        prog=st.progress(0.0); status=st.empty(); sigs=[]
        for i,sym in enumerate(scan_pairs):
            prog.progress((i+1)/len(scan_pairs))
            status.text(f"Analyzing {sym}... {i+1}/{len(scan_pairs)}")
            rsi=components['market_analyzer'].get_latest_rsi(sym)
            mom=components['market_analyzer'].get_latest_momentum(sym)
            vol=components['market_analyzer'].get_volatility(sym)
            price=components['market_analyzer'].get_price(sym)
            # simple heuristics replicating your earlier logic
            q_dec="HOLD"; q_conf=0.5
            if rsi<30 and mom>3: q_dec,q_conf="BUY",0.75
            elif rsi>70 and mom<-3: q_dec,q_conf="SELL",0.75
            elif abs(mom)>5: q_dec,q_conf=("BUY" if mom>0 else "SELL"),0.65
            ml_dec=q_dec; ml_conf=q_conf*0.9
            te_dec=q_dec; te_conf=min(q_conf*1.1,1.0)
            final=(q_conf*q + ml_conf*ml + te_conf*te)/100.0
            final_dec = q_dec if final>=ss.ms_min_conf else "HOLD"
            sigs.append({
                'symbol':sym,
                'quantum':{'decision':q_dec,'confidence':q_conf},
                'ml':{'decision':ml_dec,'confidence':ml_conf},
                'technical':{'decision':te_dec,'confidence':te_conf},
                'final':{'decision':final_dec,'confidence':final},
                'price':price,'rsi':rsi,'momentum':mom,'volatility':vol,
            })
            if final_dec in ('BUY','SELL') and final>=0.8:
                notify_signal({'symbol':sym,'signal':final_dec,'confidence':final,'price':price})
        prog.empty(); status.empty()
        ss.ms_signals=sigs; ss.ms_last_scan=datetime.utcnow(); ss.ms_do_scan=False

    sigs=ss.ms_signals
    if sigs:
        if ss.ms_show_only:
            disp=[s for s in sigs if s['final']['decision']!='HOLD' and s['final']['confidence']>=ss.ms_min_conf]
        else:
            disp=sigs
        if disp:
            st.subheader(f"Results ({len(disp)} pairs)")
            rows=[]
            for s in disp:
                rows.append({
                    'Symbol':s['symbol'],
                    'Price':s['price'],
                    'Final':s['final']['decision'],
                    'Conf':round(s['final']['confidence'],3),
                    'Quantum':f"{s['quantum']['decision']} ({s['quantum']['confidence']:.2f})",
                    'ML':f"{s['ml']['decision']} ({s['ml']['confidence']:.2f})",
                    'Tech':f"{s['technical']['decision']} ({s['technical']['confidence']:.2f})",
                    'RSI':round(s['rsi'],1),'Momentum':round(s['momentum'],2),'Vol':round(s['volatility'],3),
                })
            df_sig=pd.DataFrame(rows)
            st.dataframe(df_sig,use_container_width=True)
            # quick trade interface
            st.subheader("⚡ Quick Trade")
            for idx, s in enumerate(disp[:10]):
                colA,colB,colC=st.columns([3,1,1])
                with colA: st.write(f"**{s['symbol']}** {s['final']['decision']} (Conf {s['final']['confidence']:.2f})")
                with colB:
                    if st.button("Buy",key=f"ms_qt_buy_{idx}"):
                        st.session_state['ms_selected']={'symbol':s['symbol'],'action':'BUY','price':s['price'],'confidence':s['final']['confidence']}; st.rerun()
                with colC:
                    if st.button("Sell",key=f"ms_qt_sell_{idx}"):
                        st.session_state['ms_selected']={'symbol':s['symbol'],'action':'SELL','price':s['price'],'confidence':s['final']['confidence']}; st.rerun()
            if 'ms_selected' in st.session_state:
                tr=st.session_state['ms_selected']
                st.info(f"Selected {tr['action']} {tr['symbol']} @ {tr['price']}")
                qty=st.number_input("Qty",min_value=0.000001,step=0.000001,format="%.6f",key="ms_trade_qty")
                if st.button("Execute",key="ms_exec_btn") and qty>0:
                    res=components['trade_exec'].manual_trade(tr['symbol'], qty, st.session_state['sl_mult'], st.session_state['tp_mult'])
                    # we assume BUY; fallback: record side separately
                    _record_trade(tr['symbol'],tr['action'],qty,tr['price'],qty*tr['price'],fee=qty*tr['price']*0.001,execution_type='multi_strategy')
                    st.success(str(res))
                    del st.session_state['ms_selected']
                    st.rerun()
        else:
            st.warning("No strong signals at current threshold.")
    else:
        st.info("Click Scan to analyze market.")

# ==================================================================
# TAB 5: AUTO-TRADER CONTROL
# ==================================================================
with tab_autotrader:
    st.header("🤖 Auto-Trader Control")
    scan=st.session_state['auto_scanner']
    colA,colB=st.columns(2)
    with colA:
        st.metric("Scanner", "Running" if scan.is_running() else "Stopped")
        if st.button("Start" if not scan.is_running() else "Stop", key="at_toggle"):
            scan.start_scanning() if not scan.is_running() else scan.stop_scanning(); st.rerun()
    with colB:
        st.metric("Interval", f"{scan.scan_interval}s")
    st.markdown("---")
    res=scan.get_latest_results()
    if res:
        st.metric("Signals Found", res.get('signals_found',0))
        st.metric("Last Scan #", res.get('scan_number',0))
        if res.get('strong_signals'):
            st.json(res['strong_signals'])
    else:
        st.info("No scan results yet.")

# ==================================================================
# TAB 6: MANUAL TRADER
# ==================================================================
with tab_manual:
    st.header("✋ Manual Trader")
    mkt=components['market_analyzer']
    pairs=mkt.get_trading_pairs()
    sym=st.selectbox("Symbol",pairs,key="mt_sym")
    price=mkt.get_price(sym)
    st.info(f"Current Price: ${price:,.4f}")
    qty=st.number_input("Quantity",min_value=0.000001,step=0.000001,format="%.6f",key="mt_qty")
    use_sl_tp=st.checkbox("Use SL/TP",value=True,key="mt_sl_tp")
    if use_sl_tp:
        sl=st.number_input("Stop Loss %",1.0,20.0,5.0,step=0.5,key="mt_sl")
        tp=st.number_input("Take Profit %",1.0,50.0,10.0,step=0.5,key="mt_tp")
    if st.button("🚀 Execute",key="mt_exec") and qty>0:
        # FallbackTradeExecutor doesn't accept side param
        res=components['trade_exec'].manual_trade(sym, qty, st.session_state['sl_mult'], st.session_state['tp_mult'])
        _record_trade(sym,'BUY',qty,price,qty*price,fee=qty*price*0.001,execution_type='manual')
        st.success(str(res))

# ==================================================================
# TAB 7: BACKTESTING
# ==================================================================
with tab_backtest:
    st.header("🔬 Backtesting")
    if not BACKTESTING_AVAILABLE:
        st.error("Backtesting unavailable. Install deps & module.")
        st.code("pip install ccxt scipy")
    else:
        bt_days_sel=st.selectbox("Lookback",["7d","30d","90d","180d","365d"],index=4,key="bt_days_sel")
        days=int(bt_days_sel.rstrip('d'))
        refresh_cache=st.checkbox("Force re-download",value=False,key="bt_refresh")
        pairs_txt=st.text_input("Pairs","BTCUSDT,ETHUSDT,SOLUSDT",key="bt_pairs")
        capital=st.number_input("Start Capital (USDT)",100,1_000_000,1_000,100,key="bt_cap")
        fee_rate=st.number_input("Fee Rate",0.0,0.01,0.001,0.0001,format="%.4f",key="bt_fee")
        if st.button("Run Backtest",key="bt_run"):
            with st.spinner("Running backtest..."):
                try:
                    bt=BacktestingIntegration()
                    df=bt._run_engine([p.strip().upper() for p in pairs_txt.split(',') if p.strip()], timeframe="1h", capital=capital, fee_rate=fee_rate, days=days, refresh_cache=refresh_cache)
                except Exception as e:
                    st.error(f"Backtest failed: {e}")
                    st.exception(e)
                    df=None
            if df is not None and not df.empty:
                st.subheader("Results")
                st.dataframe(df,use_container_width=True)
                # apply to multistrat weights if columns present
                required={"Quantum Weight","ML Weight","Technical Weight"}
                if required.issubset(df.columns):
                    st.subheader("🎯 Apply Strategy Weights")
                    for i,row in df.iterrows():
                        colA,colB=st.columns([4,1])
                        with colA:
                            st.write(f"{row['Pair']}: Q{row['Quantum Weight']} ML{row['ML Weight']} T{row['Technical Weight']}")
                        with colB:
                            if st.button("Set",key=f"bt_set_{i}"):
                                st.session_state['ms_weight_quantum']=int(row['Quantum Weight'])
                                st.session_state['ms_weight_ml']=int(row['ML Weight'])
                                st.session_state['ms_weight_technical']=int(row['Technical Weight'])
                                st.session_state['ms_wq']=int(row['Quantum Weight'])
                                st.session_state['ms_wm']=int(row['ML Weight'])
                                st.session_state['ms_wt']=int(row['Technical Weight'])
                                st.success("Applied to Multi-Strategy weights.")
                                st.rerun()
            else:
                st.warning("No backtest data.")

# ==================================================================
# TAB 8: SYSTEM HEALTH
# ==================================================================
with tab_syshealth:
    st.header("🩺 System Health")
    try:
        st.metric("CPU", f"{psutil.cpu_percent()}%")
        st.metric("Memory", f"{psutil.virtual_memory().percent}%")
        st.metric("Threads", threading.active_count())
    except Exception as e:
        st.error(str(e))
    st.markdown("---")
    st.subheader("Environment")
    st.json({k:v for k,v in os.environ.items() if k in ('RAILWAY_ENVIRONMENT','PORT','USE_TESTNET','BINANCE_API_KEY','BINANCE_API_SECRET')})

# ==================================================================
# TAB 9: SETTINGS (minimal for now)
# ==================================================================
with tab_settings:
    st.header("⚙️ Settings")
    st.caption("Session-level risk settings")
    st.session_state['sl_mult']=st.slider("Stop Loss Mult",0.5,5.0,float(st.session_state['sl_mult']),0.1,key="set_sl")
    st.session_state['tp_mult']=st.slider("Take Profit Mult",1.0,10.0,float(st.session_state['tp_mult']),0.5,key="set_tp")
    st.markdown("---")
    st.subheader("Notifications")
    ns=get_notification_status()
    st.json(ns)
    if ns.get('enabled') and st.button("Test Email",key="set_test_email"): send_test_notification()

# ==================================================================
# TAB 10: LOGS
# ==================================================================
with tab_logs:
    st.header("📝 Logs")
    if st.button("Clear Logs",key="lg_clear"):
        st.session_state['logs']=[]; st.rerun()
    for l in st.session_state.get('logs',[]):
        st.text(l)

# ------------------------------------------------------------------
# END OF FILE
# ------------------------------------------------------------------
