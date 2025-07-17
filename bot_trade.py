import streamlit as st
import pandas as pd
from datetime import datetime
from trader import get_account_balance
from binance.client import Client
import os

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
    # Try to use websocket for price updates if available
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
        for asset in assets:
            symbol = f"{asset}USDT"
            twm.start_symbol_ticker_socket(callback=handle_msg, symbol=symbol)
        import time
        time.sleep(2)  # Let websocket collect some prices
        twm.stop()
    except Exception:
        ws_prices = {}
    for asset in assets:
        # Exclude NFT and ETHW from scanning and display
        if asset.upper() in ['NFT', 'ETHW']:
            continue
        symbol = f"{asset}USDT"
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
                'Asset': asset,
                'Pair': symbol,
                'Price': price,
                'Signal': signal_out,
                'Confidence': confidence,
                'Strategy': strategy_label
            })
        except Exception as e:
            # Only append error if not invalid symbol (e.g., skip NFT/ETHW)
            if 'Invalid symbol' not in str(e):
                results.append({
                    'Asset': asset,
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


def bot_trade_dashboard():
    st.title("🤖 Bot Trade (Live)")
    st.caption("Live multi-crypto trading dashboard with real Binance data and signals")

    # --- Status indicators ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Status", "🟢 Online", "24/7 Active")
    with col2:
        st.metric("Platform", "Binance", "Live")
    with col3:
        client = get_binance_client()
        balance = get_account_balance(client, 'USDT')
        st.metric("USDT Balance", f"${balance:,.2f}")
    with col4:
        st.metric("Time", datetime.now().strftime("%H:%M:%S"), "Live")

    # --- Multi-Asset Market Signals ---
    st.subheader("📈 Market Signals (All Portfolio Assets)")
    positions = get_open_positions()
    # Exclude NFT and ETHW from assets
    assets = [p['Asset'] for p in positions if p['Asset'].upper() not in ['NFT', 'ETHW']] if positions else []
    if 'last_scan_time' not in st.session_state:
        st.session_state['last_scan_time'] = None
    scan_col1, scan_col2 = st.columns([1,3])
    with scan_col1:
        if st.button("🔄 Scan Now", type="primary"):
            st.session_state['last_scan_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with scan_col2:
        st.write(f"Last scan: {st.session_state['last_scan_time']}")
    st.write(f"Scanned pairs: {', '.join([f'{a}USDT' for a in assets]) if assets else 'None'}")
    if assets:
        signals = get_all_signals(assets)
        df = pd.DataFrame(signals)
        # Show only valid signals (exclude errors and NFT/ETHW)
        if not df.empty:
            df = df[df['Signal'] != 'ERROR']
            st.dataframe(df[['Asset','Pair','Price','Signal','Confidence','Strategy']], use_container_width=True)
        else:
            st.info("No valid signals found.")
    else:
        st.info("No open positions.")

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
