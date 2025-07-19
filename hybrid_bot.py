#!/usr/bin/env python3
"""
Hybrid Crypto Trading Bot Dashboard (hybrid_bot.py)
==================================================
Company: Rondanini Publishing Ltd.
Website: https://www.rondanini.net

Features:
- Live trading with Binance integration (live only, no testnet)
- Three modes: Auto Bot (always-on), Quantum-enhanced, Manual trading
- Integrates breakout, ML-enhanced, relaxed strategies
- AdaptiveRiskManager for dynamic position sizing/risk rules
- Full logging, health monitoring, performance metrics
- GBP conversion, portfolio analysis, streaming UI dashboard
- Background trading loop managed via threading
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import json, os, time, threading, requests, random, uuid
import numpy as np, psutil
from concurrent.futures import ThreadPoolExecutor
try:
    from dotenv import load_dotenv; load_dotenv()
except ImportError:
    pass

# Binance client
try:
    from binance.client import Client
    from binance.exceptions import BinanceAPIException
    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False

# Trading modules
TRADING_MODULES_AVAILABLE = False
try:
    from strategy import check_breakout_enhanced, get_strategy_confidence
    from enhanced_ml_strategy import get_ml_enhanced_signal
    from relaxed_strategy import enhanced_strategy_check
    from trader import calculate_dynamic_position_size, monitor_position_enhanced, execute_entry, execute_exit, get_account_balance
    from multi_pair_scanner import CryptoPairScanner
    from bot_controller import AdaptiveRiskManager
    TRADING_MODULES_AVAILABLE = True
except ImportError as e:
    st.warning(f"Trading modules unavailable: {e}")

# Quantum modules
QUANTUM_AVAILABLE = False
try:
    from quantum_engine import QuantumTradingEngine
    QUANTUM_AVAILABLE = True
except ImportError as e:
    st.warning(f"Quantum modules unavailable: {e}")

API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')
MIN_BALANCE_USD = float(os.getenv('MIN_BALANCE_USD', '10.0'))
SCAN_INTERVAL = int(os.getenv('SCAN_INTERVAL', '300'))
MIN_CONFIDENCE = float(os.getenv('MIN_CONFIDENCE', '0.65'))
MAX_POSITIONS = int(os.getenv('MAX_POSITIONS', '3'))
RISK_PERCENTAGE = float(os.getenv('RISK_PERCENTAGE', '0.015'))
SCAN_MODE = os.getenv('SCAN_MODE', 'SELECTED')

def get_binance_client():
    if not BINANCE_AVAILABLE or not API_KEY or not API_SECRET:
        return None
    try:
        return Client(API_KEY, API_SECRET)
    except Exception as e:
        st.error(f"Binance init error: {e}")
        return None

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
    for log in [
        'logs/manual_trades.log','logs/trade_executions.json','logs/auto_trader_debug.log',
        'logs/bot_heartbeat.log'
    ]:
        if not os.path.exists(log):
            with open(log,'w') as f: f.write('')

def get_portfolio():
    client=get_binance_client()
    if not client:
        return {},0,0
    acct=client.get_account()
    tickers={t['symbol']:float(t['price']) for t in client.get_all_tickers()}
    port={}
    total_usd=0
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
    res=[]
    if not client: return res
    acct=client.get_account()
    tickers={t['symbol']:float(t['price']) for t in client.get_all_tickers()}
    for bal in acct['balances']:
        tot=float(bal['free'])+float(bal['locked'])
        if tot>0 and bal['asset']!='USDT':
            sym=f"{bal['asset']}USDT"
            price=tickers.get(sym,0)
            val=tot*price
            if val>=MIN_BALANCE_USD:
                res.append({'Asset':bal['asset'],'Symbol':sym,'Total':tot,'USD Value':val,'GBP Value':val*get_gbp_exchange_rate(),'Price':price})
    return res

def log_trade(tr):
    ts=datetime.now().isoformat()
    with open('logs/trade_executions.json','a') as f:
        f.write(json.dumps({**tr,'timestamp':ts})+"\n")
    with open('logs/trades.csv','a') as f:
        f.write(f"{ts},{tr['symbol']},{tr['type']},{tr['price']},{tr.get('exit_price','')},{tr['quantity']},,"
                f"{'OPEN' if tr['type']=='ENTRY' else 'CLOSED'},{tr['strategy']},{tr.get('confidence',1)},"
                f"{tr.get('quantum_signal','N/A')},{tr.get('risk_level','')}\n")

# Background Auto Bot
def start_auto_bot():
    if st.session_state.get('auto_running'): return
    st.session_state['auto_running']=True

    def loop():
        client=get_binance_client()
        rm = AdaptiveRiskManager() if TRADING_MODULES_AVAILABLE else None
        quantum_eng = QuantumTradingEngine() if QUANTUM_AVAILABLE else None
        scanner = CryptoPairScanner(client) if TRADING_MODULES_AVAILABLE else None
        cycle=0
        while st.session_state.get('auto_running',False):
            cycle+=1
            start = datetime.now()
            with open('logs/bot_heartbeat.log','a') as f: f.write(f"{start.isoformat()} - cycle {cycle}\n")
            open_pos = get_open_positions()
            open_syms=[p['Symbol'] for p in open_pos]
            port,usd,gbp = get_portfolio()
            # Monitor exits
            for p in open_pos:
                try:
                    ex,reason=monitor_position_enhanced(client,p['Symbol'],p['Price'])
                    if ex:
                        res=execute_exit(client,p['Symbol'],p['Total'],p['Price'],None,reason)
                        tr={'symbol':p['Symbol'],'type':'EXIT','price':p['Price'],'quantity':p['Total'],'strategy':'AutoExit','result':res}
                        log_trade(tr)
                        st.session_state['last_action']=f"Auto closed {p['Symbol']}: {reason}"
                except Exception as e:
                    with open('logs/auto_trader_debug.log','a') as f: f.write(str(e)+"\n")
            # Scan and entries
            if len(open_pos)<MAX_POSITIONS:
                try:
                    pairs = scanner.get_selected_pairs()
                    opps = scanner.scan_multiple_pairs(pairs,max_workers=5)
                    filtered=[o for o in opps if o['confidence']>=MIN_CONFIDENCE and o['decision']!='HOLD' and o['symbol'] not in open_syms]
                    enhanced=[]
                    for opp in filtered:
                        sym=opp['symbol']
                        klines=client.get_klines(sym,"1m",120)
                        bsig=get_strategy_confidence(klines)
                        bo=check_breakout_enhanced(klines)
                        ml_sig,ml_conf=get_ml_enhanced_signal(klines)
                        r_sig,r_conf=enhanced_strategy_check(klines)
                        votes,confs=[],[]
                        for sig,c in [(bo,bsig),(ml_sig,ml_conf),(r_sig,r_conf)]:
                            if sig!='HOLD':
                                votes.append(sig)
                                confs.append(c)
                        if len(votes)>=2:
                            lv=votes.count('BUY_LONG')
                            sv=votes.count('BUY_SHORT')
                            if lv>=2:
                                final='BUY_LONG'; final_conf=np.mean([c for s,c in zip(votes,confs) if s=='BUY_LONG'])
                            elif sv>=2:
                                final='BUY_SHORT'; final_conf=np.mean([c for s,c in zip(votes,confs) if s=='BUY_SHORT'])
                            else: continue
                            dyn = rm.get_dynamic_rules(sym.replace('USDT',''), final_conf, 'BULL_TRENDING', 0.03) if rm else {}
                            final_conf*=dyn.get('confidence_factor',1)
                            if final_conf>=MIN_CONFIDENCE:
                                enhanced.append({'symbol':sym,'signal':final,'confidence':final_conf,'votes':len(votes),'dyn':dyn})
                    executed=False
                    if QUANTUM_AVAILABLE and quantum_eng and enhanced:
                        for e in enhanced[:3]:
                            q = quantum_eng.generate_quantum_trading_recommendation(portfolio_data=port,market_condition='BULL_TRENDING',strategy='Ensemble',risk_level='BALANCED',portfolio_value=usd)
                            if q['quantum_signal']==e['signal'] and q['quantum_confidence']>0.7:
                                price=float(client.get_symbol_ticker(e['symbol'])['price'])
                                bal=get_account_balance(client,'USDT')
                                size=calculate_dynamic_position_size(bal,0.001,e['confidence'],0.03,RISK_PERCENTAGE)
                                res=execute_entry(client,e['symbol'],size,e['signal'])
                                tr={'symbol':e['symbol'],'type':'ENTRY','price':price,'quantity':size,'strategy':'QuantumAuto','confidence':e['confidence'],'quantum_signal':q['quantum_signal'],'risk_level':str(e['dyn'])}
                                log_trade(tr)
                                st.session_state['last_action']=f"Quantum trade: {e['symbol']}"
                                executed=True
                                break
                    if not executed and enhanced:
                        e= max(enhanced,key=lambda x:x['confidence'])
                        price=float(client.get_symbol_ticker(e['symbol'])['price'])
                        bal=get_account_balance(client,'USDT')
                        size=calculate_dynamic_position_size(bal,0.001,e['confidence'],0.03,RISK_PERCENTAGE)
                        res=execute_entry(client,e['symbol'],size,e['signal'])
                        tr={'symbol':e['symbol'],'type':'ENTRY','price':price,'quantity':size,'strategy':'EnhancedAuto','confidence':e['confidence'],'quantum_signal':'N/A','risk_level':str(e['dyn'])}
                        log_trade(tr)
                        st.session_state['last_action']=f"Auto trade: {e['symbol']}"
                except Exception as e:
                    with open('logs/auto_trader_debug.log','a') as f: f.write(str(e)+"\n")
            elapsed=(datetime.now()-start).total_seconds()
            t=max(60,SCAN_INTERVAL-elapsed)
            time.sleep(t)
    threading.Thread(target=loop,daemon=True).start()

def stop_auto_bot():
    st.session_state['auto_running']=False

# Streamlit UI
st.set_page_config(page_title="Hybrid Crypto Bot", layout="wide")
ensure_log_files()
st.title("🧠 Hybrid Crypto Bot (Auto + Quantum + Manual)")

# Sidebar controls
with st.sidebar:
    st.header("Controls")
    if BINANCE_AVAILABLE and API_KEY and API_SECRET:
        st.success("🔐 Binance Connected")
        client = get_binance_client()
        try:
            st.write(f"Account balance: {get_account_balance(client,'USDT')} USDT")
        except:
            st.error("Error fetching balance")
    else:
        st.error("⚠️ Binance not initialized (Check API_KEY/API_SECRET)")
    st.write("Auto-Bot Status:", "Running" if st.session_state.get('auto_running') else "Stopped")
    if st.button("Start Auto-Bot"):
        start_auto_bot()
    if st.button("Stop Auto-Bot"):
        stop_auto_bot()
    st.write("---")
    st.checkbox("Enable Quantum Mode", key="quantum_mode")
    st.write("---")
    st.header("Manual Trade")
    m_symbol=st.text_input("Symbol (e.g. ETHUSDT)")
    m_qty=st.number_input("Quantity",min_value=0.0,format="%.6f")
    m_side=st.selectbox("Side",["BUY","SELL"])
    if st.button("Execute Manual Trade"):
        try:
            price=float(get_binance_client().get_symbol_ticker(symbol=m_symbol)['price'])
            res=execute_entry(get_binance_client(),m_symbol,m_qty, "BUY_LONG" if m_side=="BUY" else "BUY_SHORT")
            log_trade({'symbol':m_symbol,'type':'MANUAL_'+m_side,'price':price,'quantity':m_qty,'strategy':'Manual'})
            st.success(f"Manual {m_side} order executed for {m_qty} {m_symbol}")
        except Exception as e:
            st.error(f"Manual trade failed: {e}")

tabs=st.tabs(["Portfolio","Scanner","Execution","Performance","Logs","Health"])

with tabs[0]:
    st.header("📦 Portfolio Overview")
    port,usd,gbp=get_portfolio()
    st.metric("Total USD",f"${usd:,.2f}","")
    st.metric("Total GBP",f"£{gbp:,.2f}","")
    if port:
        df=pd.DataFrame([{'Asset':a,'Balance':d['balance'],'USD Value':d['usd_value']} for a,d in port.items()])
        st.dataframe(df)
        fig=px.pie(df, values='USD Value', names='Asset', title="Asset Allocation")
        st.plotly_chart(fig, use_container_width=True)
        opens=get_open_positions()
        if opens:
            st.subheader("Open Positions")
            st.dataframe(pd.DataFrame(opens))

with tabs[1]:
    st.header("🔍 Market Scanner")
    if st.button("Run Scan"):
        scanner = CryptoPairScanner(get_binance_client())
        pairs = scanner.get_selected_pairs()
        opps = scanner.scan_multiple_pairs(pairs, max_workers=5)
        st.session_state['last_scan']=opps
    opps=st.session_state.get('last_scan',[])
    for o in opps[:20]:
        st.write(f"{o['symbol']} | {o['decision']} | conf={o['confidence']:.2%}")

with tabs[2]:
    st.header("🛠️ Trade Execution & Bot Activity")
    st.write("Last Action:", st.session_state.get('last_action','—'))
    if os.path.exists('logs/trade_executions.json'):
        with open('logs/trade_executions.json','r') as f:
            lines=f.readlines()[-20:]
        for ln in lines:
            st.write(json.loads(ln))

with tabs[3]:
    st.header("📊 Performance Metrics")
    if os.path.exists('logs/trades.csv'):
        df=pd.read_csv('logs/trades.csv')
        df['pnl_pct']=df['change_pct'].fillna(0)
        cum=df['pnl_pct'].cumsum()
        fig=go.Figure()
        fig.add_trace(go.Scatter(x=list(range(len(cum))), y=cum,name="Cumulative PnL %"))
        st.plotly_chart(fig,use_container_width=True)

with tabs[4]:
    st.header("📜 Logs")
    if os.path.exists('logs/auto_trader_debug.log'):
        st.subheader("Auto Trader Debug")
        st.text("".join(open('logs/auto_trader_debug.log').read().splitlines()[-20:]))

with tabs[5]:
    st.header("❤️ System Health")
    hb="N/A"
    if os.path.exists('logs/bot_heartbeat.log'):
        hb=open('logs/bot_heartbeat.log').read().splitlines()[-1]
    st.write("Last Heartbeat:", hb)
    mem=psutil.virtual_memory()
    cpu=psutil.cpu_percent()
    threads=threading.active_count()
    st.write(f"CPU Usage: {cpu}%")
    st.write(f"Memory Usage: {mem.percent}%")
    st.write(f"Active Threads: {threads}")
    st.subheader("Error Log")
    if os.path.exists('logs/auto_trader_debug.log'):
        st.text("".join(open('logs/auto_trader_debug.log').read().splitlines()[-10:]))
    if st.button("Clear Error Log"):
        open('logs/auto_trader_debug.log','w').close()
    if st.button("Restart Auto Bot"):
        stop_auto_bot(); time.sleep(1); start_auto_bot()
