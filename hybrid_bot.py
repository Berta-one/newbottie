
#!/usr/bin/env python3
"""
Hybrid Crypto Trading Bot Dashboard
==================================
- 8 Tabs: Portfolio, Scanner, Manual Trade, Auto Bot, Performance, Quantum, Risk Settings, Health
- Handles missing columns and empty logs gracefully
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import json, os, time, threading, requests, random
import numpy as np

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    from dotenv import load_dotenv; load_dotenv()
except ImportError:
    pass

try:
    from binance.client import Client
    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False

TRADING_MODULES_AVAILABLE = False
try:
    from strategy import check_breakout_enhanced, get_strategy_confidence
    from enhanced_ml_strategy import get_ml_enhanced_signal
    from relaxed_strategy import enhanced_strategy_check
    from trader import calculate_dynamic_position_size, monitor_position_enhanced, execute_entry, execute_exit, get_account_balance
    from multi_pair_scanner import CryptoPairScanner
    from bot_controller import AdaptiveRiskManager
    TRADING_MODULES_AVAILABLE = True
except:
    pass

QUANTUM_AVAILABLE = False
try:
    from quantum_engine import QuantumTradingEngine
    QUANTUM_AVAILABLE = True
except:
    pass

API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')
MIN_BALANCE_USD = float(os.getenv('MIN_BALANCE_USD', '10.0'))
SCAN_INTERVAL = int(os.getenv('SCAN_INTERVAL', '300'))
MIN_CONFIDENCE = float(os.getenv('MIN_CONFIDENCE', '0.65'))
MAX_POSITIONS = int(os.getenv('MAX_POSITIONS', '3'))
RISK_PERCENTAGE = float(os.getenv('RISK_PERCENTAGE', '0.015'))
QUANTUM_CONF_THRESHOLD = 0.7

if 'auto_running' not in st.session_state:
    st.session_state['auto_running'] = False
if 'last_action' not in st.session_state:
    st.session_state['last_action'] = 'None'
if 'quantum_only' not in st.session_state:
    st.session_state['quantum_only'] = True
if 'risk_override' not in st.session_state:
    st.session_state['risk_override'] = RISK_PERCENTAGE

def get_binance_client():
    if not BINANCE_AVAILABLE or not API_KEY or not API_SECRET:
        return None
    return Client(API_KEY, API_SECRET)

def get_gbp_exchange_rate():
    try:
        r = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=5)
        return r.json()['rates']['GBP']
    except:
        return 0.79

def ensure_log_files():
    os.makedirs('logs', exist_ok=True)
    if not os.path.exists('logs/trades.csv'):
        with open('logs/trades.csv','w') as f:
            f.write('timestamp,symbol,direction,entry_price,exit_price,quantity,change_pct,status,strategy,confidence,quantum_signal,risk_level\n')
    for log in ['logs/manual_trades.log','logs/trade_executions.json','logs/auto_trader_debug.log','logs/bot_heartbeat.log','logs/quantum_trades.csv']:
        if not os.path.exists(log):
            open(log,'w').close()

def safe_read_csv(path):
    if os.path.exists(path) and os.path.getsize(path)>0:
        return pd.read_csv(path)
    return pd.DataFrame()

def log_trade(tr):
    ts=datetime.now().isoformat()
    with open('logs/trade_executions.json','a') as f: f.write(json.dumps({**tr,'timestamp':ts})+"\n")
    with open('logs/trades.csv','a') as f:
        f.write(f"{ts},{tr['symbol']},{tr['type']},{tr['price']},{tr.get('exit_price','')},{tr['quantity']},,"
                f"{'OPEN' if tr['type']=='ENTRY' else 'CLOSED'},{tr['strategy']},{tr.get('confidence',1)},"
                f"{tr.get('quantum_signal','N/A')},{tr.get('risk_level','')}\n")
    if 'Quantum' in tr['strategy']:
        with open('logs/quantum_trades.csv','a') as f:
            f.write(f"{ts},{tr['symbol']},{tr['type']},{tr['price']},{tr['quantity']},{tr.get('confidence',1)},"
                    f"{tr.get('quantum_signal','')},{tr['strategy']}\n")

def get_portfolio():
    client=get_binance_client()
    if not client: return {},0,0
    acct=client.get_account()
    tickers={t['symbol']:float(t['price']) for t in client.get_all_tickers()}
    port={}; total_usd=0
    for bal in acct['balances']:
        tot=float(bal['free'])+float(bal['locked'])
        if tot>0:
            sym=f"{bal['asset']}USDT"
            price=tickers.get(sym,1 if bal['asset'] in ['USDT','BUSD','USDC','FDUSD'] else 0)
            val=tot*price
            if val>=MIN_BALANCE_USD:
                port[bal['asset']]={'balance':tot,'price_usd':price,'usd_value':val}
                total_usd+=val
    return port,total_usd,total_usd*get_gbp_exchange_rate()

def get_open_positions():
    client=get_binance_client()
    if not client: return []
    acct=client.get_account()
    tickers={t['symbol']:float(t['price']) for t in client.get_all_tickers()}
    res=[]
    for bal in acct['balances']:
        tot=float(bal['free'])+float(bal['locked'])
        if tot>0 and bal['asset']!='USDT':
            sym=f"{bal['asset']}USDT"
            price=tickers.get(sym,0)
            val=tot*price
            if val>=MIN_BALANCE_USD:
                res.append({'Asset':bal['asset'],'Symbol':sym,'Total':tot,'USD Value':val,'GBP Value':val*get_gbp_exchange_rate(),'Price':price})
    return res

def start_auto_bot(): st.session_state['auto_running']=True
def stop_auto_bot(): st.session_state['auto_running']=False

# UI
st.set_page_config(page_title="Hybrid Crypto Bot", layout="wide")
ensure_log_files()
st.title("🧠 Hybrid Crypto Bot")

tabs=st.tabs(["Portfolio","Scanner","Manual Trade","Auto Bot","Performance","Quantum","Risk Settings","Health"])

# Portfolio Tab
with tabs[0]:
    st.header("Portfolio Overview")
    port,usd,gbp=get_portfolio()
    st.metric("Total USD",f"${usd:,.2f}"); st.metric("Total GBP",f"£{gbp:,.2f}")
    if port:
        df=pd.DataFrame([{'Asset':a,'Balance':d['balance'],'USD Value':d['usd_value']} for a,d in port.items()])
        st.dataframe(df); st.plotly_chart(px.pie(df, values='USD Value', names='Asset'), use_container_width=True)
    else:
        st.info("No portfolio data available.")

# Scanner Tab
with tabs[1]:
    st.header("Market Scanner")
    if st.button("Run Scan"): st.info("Scanner functionality placeholder.")
    if 'scan_results' in st.session_state and st.session_state['scan_results']:
        for o in st.session_state['scan_results'][:20]:
            st.write(f"{o['symbol']} | {o['decision']} | {o['confidence']:.2%}")
    else:
        st.info("No scan results yet.")

# Manual Trade Tab
with tabs[2]:
    st.header("Manual Trade")
    sym=st.text_input("Symbol (e.g. ETHUSDT)")
    qty=st.number_input("Quantity",min_value=0.0)
    side=st.selectbox("Side",["BUY","SELL"])
    if st.button("Execute Trade"): st.info("Manual trade execution placeholder.")

# Auto Bot Tab
with tabs[3]:
    st.header("Auto Bot Control")
    st.write("Status:","Running" if st.session_state['auto_running'] else "Stopped")
    st.write("Last Action:",st.session_state['last_action'])
    if st.button("Start Auto Bot"): start_auto_bot()
    if st.button("Stop Auto Bot"): stop_auto_bot()

# Performance Tab
with tabs[4]:
    st.header("Performance Metrics")
    df=safe_read_csv('logs/trades.csv')
    if not df.empty:
        if 'change_pct' in df.columns:
            df['pnl_pct']=df['change_pct'].fillna(0)
        else:
            df['pnl_pct']=0
        cum=df['pnl_pct'].cumsum()
        fig=go.Figure(); fig.add_trace(go.Scatter(x=list(range(len(cum))),y=cum,name="PnL%")); st.plotly_chart(fig)
        st.write(f"Total Trades: {len(df)}")
    else:
        st.info("No performance data yet.")

# Quantum Tab
with tabs[5]:
    st.header("Quantum Analysis")
    if os.path.exists('logs/quantum_trades.csv') and os.path.getsize('logs/quantum_trades.csv')>0:
        st.subheader("Quantum Trade History")
        st.text("".join(open('logs/quantum_trades.csv').read().splitlines()[-10:]))
    else:
        st.info("No quantum trade data yet.")

# Risk Settings Tab
with tabs[6]:
    st.header("Risk Settings")
    st.slider("Risk % Override",0.001,0.05,st.session_state['risk_override'],0.001,key='risk_override')
    st.checkbox("Require Quantum Confirmation",value=st.session_state['quantum_only'],key='quantum_only')

# Health Tab
with tabs[7]:
    st.header("System Health")
    if PSUTIL_AVAILABLE:
        st.write(f"CPU: {psutil.cpu_percent()}% | Memory: {psutil.virtual_memory().percent}% | Threads: {threading.active_count()}")
    else:
        st.warning("psutil not installed. Install with: pip install psutil")
