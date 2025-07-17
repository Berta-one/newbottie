import streamlit as st
import pandas as pd
from datetime import datetime
from trader import get_account_balance, execute_entry, execute_exit, monitor_position_enhanced, log_trade_execution
from binance.client import Client
import os
import threading
import time
import json

# --- Helper: Get current signal, confidence, and price (live) ---

# --- Import all available strategies ---
from strategy import check_breakout_enhanced, get_strategy_confidence
try:
    from enhanced_ml_strategy import check_ml_signal, get_ml_confidence
except ImportError:
    check_ml_signal = None
    get_ml_confidence = None


# --- Multi-asset signal fetcher (with optional websocket price updates) ---
def get_all_signals(assets, interval='5m', lookback=120):
    client = get_binance_client()
    strategy = st.session_state.get('selected_strategy', 'Breakout')
    results = []
    # Get all trading pairs and tickers from Binance
    try:
        exchange_info = client.get_exchange_info()
        tickers = client.get_ticker()
        # Top 20 by volume
        top_symbols = sorted(
            [t for t in tickers if t.get('quoteVolume')],
            key=lambda x: float(x['quoteVolume']),
            reverse=True
        )[:20]
        symbols = [t['symbol'] for t in top_symbols if t['symbol'][-4:] == 'USDT']
    except Exception as e:
        st.error(f"Error fetching Binance symbols: {e}")
        return []
    # WebSocket for live prices (optional, fallback to REST price)
    ws_prices = {}
    try:
        from binance import ThreadedWebsocketManager
        api_key = os.getenv('BINANCE_API_KEY')
        api_secret = os.getenv('BINANCE_API_SECRET')
        twm = ThreadedWebsocketManager(api_key=api_key, api_secret=api_secret)
        twm.start()
        def handle_msg(msg):
            s = msg['s']
            ws_prices[s] = float(msg['c'])
        for symbol in symbols:
            twm.start_symbol_ticker_socket(callback=handle_msg, symbol=symbol)
        import time
        time.sleep(2)
        twm.stop()
    except Exception:
        ws_prices = {}
    # Scan all symbols (no watchlist)
    for symbol in symbols:
        try:
            klines = client.get_klines(symbol=symbol, interval=interval, limit=lookback)
            price = ws_prices.get(symbol, float(klines[-1][4]))
            # Select strategy logic
            if strategy == 'ML Enhanced' and check_ml_signal and get_ml_confidence:
                signal = check_ml_signal(klines)
                confidence = get_ml_confidence(klines)
                strategy_label = 'ML Enhanced'
            elif strategy == 'Breakout':
                signal = check_breakout_enhanced(klines)
                confidence = get_strategy_confidence(klines)
                strategy_label = 'Breakout'
            else:
                signal = check_breakout_enhanced(klines)
                confidence = get_strategy_confidence(klines)
                strategy_label = 'Breakout'
            if signal == 'BUY_LONG':
                signal_out = 'BUY'
            elif signal == 'BUY_SHORT':
                signal_out = 'SELL'
            else:
                signal_out = 'HOLD'
            results.append({
                'Pair': symbol,
                'Price': price,
                'Signal': signal_out,
                'Confidence': confidence,
                'Strategy': strategy_label
            })
        except Exception as e:
            if 'Invalid symbol' not in str(e):
                results.append({
                    'Pair': symbol,
                    'Price': None,
                    'Signal': 'ERROR',
                    'Confidence': 0.0,
                    'Strategy': strategy,
                    'Error': str(e)
                })
    return results

# --- Helper: Get Binance client ---
def get_binance_client():
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    return Client(api_key, api_secret)

# --- Helper: Get open positions (live) ---
def get_open_positions():
    client = get_binance_client()
    try:
        account = client.get_account()
        positions = []
        for bal in account['balances']:
            free = float(bal['free'])
            locked = float(bal['locked'])
            if (free + locked) > 0 and bal['asset'] not in ['USDT', 'BUSD', 'USDC']:
                positions.append({
                    'Asset': bal['asset'],
                    'Free': free,
                    'Locked': locked,
                    'Total': free + locked
                })
        return positions
    except Exception as e:
        st.error(f"Error loading open positions: {e}")
        return []

# --- Helper: Get trade history (from Binance API) ---
def get_trade_history(symbol='BTCUSDT', limit=50):
    client = get_binance_client()
    try:
        trades = client.get_my_trades(symbol=symbol, limit=limit)
        # Format for dashboard
        trade_list = []
        for t in trades:
            trade_list.append({
                'Time': datetime.fromtimestamp(t['time']/1000).strftime('%Y-%m-%d %H:%M:%S'),
                'Symbol': t['symbol'],
                'Side': 'BUY' if t['isBuyer'] else 'SELL',
                'Price': float(t['price']),
                'Qty': float(t['qty']),
                'QuoteQty': float(t['quoteQty']),
                'Commission': float(t['commission']),
                'CommissionAsset': t['commissionAsset'],
                'OrderId': t['orderId'],
                'TradeId': t['id']
            })
        return trade_list
    except Exception as e:
        st.error(f"Error loading trade history: {e}")
        return []

# --- Bot Trade Dashboard (Live Data) ---


def start_auto_trader():
    """Background trading loop: scans, opens, and closes trades automatically."""
    if 'auto_trader_running' in st.session_state and st.session_state['auto_trader_running']:
        return  # Already running
    st.session_state['auto_trader_running'] = True
    def trading_loop():
        from hybrid_bot import RISK_LEVELS
        client = get_binance_client()
        # Get selected risk level from session state, fallback to 'Balanced'
        selected_risk = st.session_state.get('selected_risk_level', 'Balanced')
        risk_info = RISK_LEVELS.get(selected_risk, RISK_LEVELS['Balanced'])
        risk_per_trade = risk_info.get('risk_per_trade', 0.015)
        import logging
        logging.basicConfig(filename='logs/auto_trader_debug.log', level=logging.INFO, format='%(asctime)s %(message)s')
        while st.session_state.get('auto_trader_running', True):
            # 1. Load open positions (from Binance)
            open_positions = get_open_positions()
            open_assets = set([p['Asset'] for p in open_positions])
            open_symbols = [p['Asset'] + 'USDT' for p in open_positions]
            logging.info(f"Open positions: {open_symbols}")
            # 2. Read actionable opportunities from logs/portfolio_scans.log
            actionable = []
            try:
                with open('logs/portfolio_scans.log', 'r') as f:
                    for line in f.readlines()[-200:]:
                        if '|' in line and 'Signal:' in line:
                            # Example: ETHUSDT | Δ%: +3.65 | Vol: 1.26x | Conf: 0.62 | Signal: BUY_LONG
                            parts = line.split('|')
                            if len(parts) == 5:
                                symbol = parts[0].strip()
                                signal = parts[4].split(':')[-1].strip()
                                confidence = float(parts[3].split(':')[-1].strip())
                                price = None  # Price not in log, will fetch below
                                # Only act on BUY_LONG or BUY_SHORT
                                if signal in ('BUY_LONG', 'BUY_SHORT'):
                                    actionable.append({'symbol': symbol, 'signal': signal, 'confidence': confidence})
            except Exception as e:
                logging.info(f"Error reading portfolio_scans.log: {e}")
            logging.info(f"Found {len(actionable)} actionable opportunities from scan log.")
            # 3. For each actionable opportunity, open trade if not already open
            for opp in actionable:
                symbol = opp['symbol']
                signal_type = opp['signal']
                confidence = opp['confidence']
                if symbol in open_symbols:
                    logging.info(f"Skipping {symbol}: already in open positions.")
                    continue
                # Fetch price
                try:
                    klines = client.get_klines(symbol=symbol, interval='5m', limit=1)
                    price = float(klines[-1][4])
                except Exception as e:
                    logging.info(f"Failed to fetch price for {symbol}: {e}")
                    price = None
                # --- Dynamic Position Sizing using confidence and volatility ---
                from trader import calculate_dynamic_position_size
                balance = get_account_balance(client, 'USDT')
                base_quantity = 0.001  # Default base trade size, can be made configurable
                # Estimate volatility as stddev of last 20 closes / mean close (fallback to 0.02 if error)
                volatility = 0.02
                try:
                    klines = client.get_klines(symbol=symbol, interval='5m', limit=20)
                    closes = [float(k[4]) for k in klines]
                    if len(closes) > 1:
                        import numpy as np
                        volatility = float(np.std(closes) / np.mean(closes))
                except Exception as e:
                    logging.info(f"Volatility calculation failed for {symbol}: {e}")
                qty = calculate_dynamic_position_size(
                    account_balance=balance,
                    base_quantity=base_quantity,
                    confidence=confidence,
                    volatility=volatility,
                    risk_percentage=risk_per_trade
                )
                logging.info(f"Placing trade: {symbol}, qty={qty}, price={price}, volatility={volatility}, confidence={confidence}")
                result = execute_entry(client, symbol, qty, signal_type)
                logging.info(f"Trade result: {result}")
                log_trade_execution('ENTRY', symbol, qty, price, result)
                # --- Write trade to logs/trades.csv ---
                try:
                    pnl = ''
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    with open('logs/trades.csv', 'a') as f:
                        f.write(f"{now},{symbol},{signal_type},{price},{pnl}\n")
                except Exception as e:
                    with open('logs/trade_errors.log', 'a') as ferr:
                        ferr.write(f"{datetime.now().isoformat()} Error writing trade: {e}\n")
                st.session_state['last_action'] = f"Opened {symbol} at {price} ({signal_type})"
            # 4. For open positions, check exit
            for pos in open_positions:
                symbol = pos['Asset'] + 'USDT'
                qty = pos['Total']
                # Find entry price from trade log (simplified)
                entry_price = None
                try:
                    with open('logs/trade_executions.json', 'r') as f:
                        for line in f:
                            entry = json.loads(line)
                            if entry['trade_type'] == 'ENTRY' and entry['symbol'] == symbol:
                                entry_price = entry['price']
                except Exception:
                    pass
                if entry_price:
                    should_exit, reason = monitor_position_enhanced(client, symbol, entry_price)
                    if should_exit:
                        result = execute_exit(client, symbol, qty, None, entry_price, reason)
                        log_trade_execution('EXIT', symbol, qty, entry_price, result)
                        # --- Write exit trade to logs/trades.csv ---
                        try:
                            pnl = ''
                            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            with open('logs/trades.csv', 'a') as f:
                                f.write(f"{now},{symbol},EXIT,{entry_price},{pnl}\n")
                        except Exception as e:
                            with open('logs/trade_errors.log', 'a') as ferr:
                                ferr.write(f"{datetime.now().isoformat()} Error writing exit trade: {e}\n")
                        st.session_state['last_action'] = f"Closed {symbol} ({reason})"
            # 5. Sleep for scan interval
            time.sleep(st.session_state.get('scan_interval', 60))
    t = threading.Thread(target=trading_loop, daemon=True)
    t.start()

def bot_trade_dashboard():
    st.title("🤖 Bot Trade (Live)")
    st.caption("Live multi-crypto trading dashboard with real Binance data and signals")

    # --- Status indicators ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        status = "🟢 Running" if st.session_state.get('auto_trader_running') else "🔴 Stopped"
        st.metric("Bot Status", status)
    with col2:
        st.metric("Platform", "Binance", "Live")
    with col3:
        client = get_binance_client()
        balance = get_account_balance(client, 'USDT')
        st.metric("USDT Balance", f"${balance:,.2f}")
    with col4:
        st.metric("Time", datetime.now().strftime("%H:%M:%S"), "Live")
    # --- Bot control ---
    if not st.session_state.get('auto_trader_running'):
        if st.button("▶️ Start Auto-Trader", type="primary"):
            start_auto_trader()
            st.success("Auto-trader started!")
    else:
        if st.button("⏹️ Stop Auto-Trader", type="secondary"):
            st.session_state['auto_trader_running'] = False
            st.warning("Auto-trader stopped.")
    # --- Last action ---
    st.info(f"Last action: {st.session_state.get('last_action', 'None')}")

    # --- Multi-Asset Market Signals ---
    st.subheader("� Recent Opportunities (from Scan Log)")
    import os, json
    log_path = 'logs/portfolio_scans.log'
    opportunities = []
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            for line in f.readlines()[-100:]:
                try:
                    entry = json.loads(line)
                    if isinstance(entry, dict):
                        opportunities.append(entry)
                except Exception:
                    continue
    if opportunities:
        df = pd.DataFrame(opportunities)
        # Only show relevant columns if present
        cols = [c for c in ['timestamp','symbol','price','signal','confidence','strategy','change','volume'] if c in df.columns]
        st.dataframe(df[cols] if cols else df, use_container_width=True)
    else:
        st.info('No recent opportunities found in scan log.')
    # --- Open positions ---
    st.subheader("🔓 Open Positions")
    open_positions = get_open_positions()
    if open_positions:
        st.dataframe(pd.DataFrame(open_positions), use_container_width=True)
    else:
        st.info("No open positions.")
    # --- Recent actions ---
    st.subheader("⚡ Recent Actions")
    try:
        with open('logs/trade_executions.json', 'r') as f:
            lines = f.readlines()[-10:]
            actions = [json.loads(line) for line in lines]
        st.dataframe(pd.DataFrame(actions), use_container_width=True)
    except Exception:
        st.info("No recent actions logged.")
        tickers = client.get_ticker()
        top_symbols = sorted(
            [t for t in tickers if t.get('quoteVolume')],
            key=lambda x: float(x['quoteVolume']),
            reverse=True
        )[:40]
        all_usdt_pairs = [t['symbol'] for t in top_symbols if t['symbol'][-4:] == 'USDT']
    except Exception:
        all_usdt_pairs = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
    # Scan all pairs, no watchlist UI
    with st.spinner('Scanning all pairs for signals...'):
        signals = get_all_signals([])
    df = pd.DataFrame(signals)
    if not df.empty and 'Signal' in df.columns:
        df = df[df['Signal'] != 'ERROR']
        if not df.empty:
            def color_signal(val):
                if val == 'BUY':
                    return 'background-color: #2ecc40; color: white; font-weight: bold; animation: flash-green 1s infinite alternate;'
                elif val == 'SELL':
                    return 'background-color: #ff4136; color: white; font-weight: bold; animation: flash-red 1s infinite alternate;'
                elif val == 'HOLD':
                    return 'background-color: #0074d9; color: white; font-weight: bold; animation: flash-blue 1s infinite alternate;'
                return ''
            styled = df[['Pair','Price','Signal','Confidence','Strategy']].style.applymap(color_signal, subset=['Signal'])
            st.write('<style>@keyframes flash-green {0%{background:#2ecc40;}100%{background:#27ae60;}}@keyframes flash-red {0%{background:#ff4136;}100%{background:#c0392b;}}@keyframes flash-blue {0%{background:#0074d9;}100%{background:#2980b9;}}</style>', unsafe_allow_html=True)
            st.dataframe(styled, use_container_width=True)
        else:
            st.warning('No valid trading signals found. Try scanning again or check your API connection.')
    else:
        st.error('No signals returned. There may be an issue with the Binance API, your connection, or the scanning logic.')


    # --- Historical Opportunities from Logs ---
    st.subheader("🕒 Historical Opportunities (Scans Log)")
    log_path = 'logs/portfolio_scans.log'
    if os.path.exists(log_path):
        log_rows = []
        with open(log_path, 'r') as f:
            scan_time = None
            for line in f:
                line = line.strip()
                if line.startswith('[') and 'Scan' in line:
                    scan_time = line.split(']')[0][1:]
                elif '|' in line and 'Signal:' in line:
                    # Example: ETHUSDT | Δ%: +3.65 | Vol: 1.26x | Conf: 0.62 | Signal: HOLD
                    parts = line.split('|')
                    if len(parts) == 5:
                        pair = parts[0].strip()
                        change = parts[1].split(':')[-1].strip()
                        vol = parts[2].split(':')[-1].strip()
                        conf = parts[3].split(':')[-1].strip()
                        signal = parts[4].split(':')[-1].strip()
                        log_rows.append({
                            'Time': scan_time,
                            'Pair': pair,
                            'Change %': change,
                            'Volume': vol,
                            'Confidence': conf,
                            'Signal': signal
                        })
        if log_rows:
            log_df = pd.DataFrame(log_rows)
            st.dataframe(log_df, use_container_width=True)
        else:
            st.info("No opportunities found in scan logs.")
    else:
        st.info("No scan log file found.")

    # --- Trade History ---
    st.subheader("📋 Trade History (BTC/USDT)")
    trades = get_trade_history()
    if trades:
        df = pd.DataFrame(trades)
        st.dataframe(df)
    else:
        st.info("No trade history yet.")

    # --- Configuration ---
    with st.expander("⚙️ Bot Configuration"):
        st.json({
            "Strategy": st.session_state.get('selected_strategy', 'Breakout'),
            "Risk": st.session_state.get('risk', 0.015),
            "Max Positions": st.session_state.get('max_positions', 3),
            "Scan Interval": st.session_state.get('scan_interval', 60),
            "Mode": "Live"
        })

    # --- Next steps/help ---
    st.subheader("🚀 Next Steps")
    st.info("""
    **Current Status:** ✅ Live trading enabled with real Binance data.
    - Monitor open positions and trade history above.
    - All trades and signals are based on live market data.
    """)
