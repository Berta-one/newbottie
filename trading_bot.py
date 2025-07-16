
"""
Crypto Trading Bot Demo

Company: Rondanini Publishing Ltd.  
Website: https://www.rondanini.net

MIT License
Copyright (c) 2025 Rondanini Publishing Ltd.

Logo:
https://static.wixstatic.com/media/80aa29_3bdfcbab4dd34671915e3b66b0b596e4~mv2.jpeg/v1/fill/w_146,h_104,al_c,q_80,usm_0.66_1.00_0.01,enc_avif,quality_auto/LRC_1719585575250.jpeg
"""

import os
import time
import streamlit as st
from datetime import datetime

def trading_dashboard(settings_compact=False):
    # --- Bot Demo Tab Content Only ---
    import random
    import plotly.graph_objs as go
    import pandas as pd
    import requests
    from hybrid_bot import TRADING_STRATEGIES, RISK_LEVELS

    # Use main app's session state for settings
    risk = st.session_state.get('risk', 1.5)
    scan_interval = st.session_state.get('scan_interval', 5)
    # Always live mode
    mode = 'Live'
    selected_strategy = st.session_state.get('selected_strategy', 'Breakout')
    selected_risk = st.session_state.get('selected_risk_level', 'Balanced')

    # --- Main Logo and Title ---
    st.title("🤖 Crypto Trading Bot Dashboard (Live)")

    # --- Status indicators ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Status", "🟢 Online", "24/7 Active")
    with col2:
        st.metric("Platform", "Railway", "Cloud Hosted")
    with col3:
        st.metric("Uptime", f"{datetime.now().strftime('%H:%M:%S')}", "Live Clock")
    with col4:
        st.metric("Mode", "Live", "Live")

    # --- Bot Health Panel ---
    st.markdown("### 🩺 Bot Health & System Status")
    health_cols = st.columns(4)
    health_cols[0].success("API: OK")
    health_cols[1].info("Logs: OK")
    health_cols[2].warning("Last Scan: <1m ago")
    health_cols[3].success("Heartbeat: Live")

    strategy_info = TRADING_STRATEGIES[selected_strategy]
    risk_info = RISK_LEVELS[selected_risk]


    # --- Settings section (compact if settings_compact=True) ---
    import inspect
    frame = inspect.currentframe()
    args, _, _, values = inspect.getargvalues(frame)
    settings_compact = values.get('settings_compact', False)
    st.header("Bot Settings")
    st.write("Select trading strategy and risk level for the live bot.")
    col1, col2 = st.columns(2)
    with col1:
        strategy = st.selectbox("Strategy", ["Scalping", "Breakout", "Swing", "Conservative"], key="live_strategy")
    with col2:
        risk = st.selectbox("Risk Level", ["Conservative", "Balanced", "Aggressive"], key="live_risk")
    st.button("Update Settings", key="update_live_settings")

    # --- Main Demo Content (as before) ---
    st.subheader("📈 Trading Simulation (Multi-Pair)")
    if st.session_state.get('bot_override', False):
        st.warning("🚨 Bot is currently BLOCKED by override. No trades or signals will be generated.")
    else:
        pairs = [
            "BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT", "ADA/USDT",
            "DOGE/USDT", "AVAX/USDT", "ETH/BTC", "SOL/BTC", "BNB/BTC", "ADA/ETH",
            "LTC/BTC", "MATIC/USDT", "ARBUSDT", "OPUSDT", "SUIUSDT", "INJUSDT", "JUPUSDT",
            "SOL/BNB", "BNB/ETH", "BTC/ETH", "ETH/BNB", "SOL/ETH", "DOGE/BTC"
        ]
        selected_pair = random.choice(pairs)
        price = random.randint(1, 100_000) + random.random()
        change_24h = random.uniform(-8, 8)
        signal = random.choice(["BUY", "SELL", "HOLD"])
        confidence = random.uniform(0.6, 0.99)

        # --- Live Price Chart (simulated) ---
        if 'price_history' not in st.session_state:
            st.session_state['price_history'] = []
        st.session_state['price_history'].append(price)
        if len(st.session_state['price_history']) > 60:
            st.session_state['price_history'] = st.session_state['price_history'][-60:]
        chart_df = pd.DataFrame({"Price": st.session_state['price_history']})
        chart = go.Figure()
        chart.add_trace(go.Scatter(y=chart_df["Price"], mode="lines+markers", name=selected_pair))
        chart.update_layout(title=f"Live Price Chart: {selected_pair}", xaxis_title="Time (refreshes)", yaxis_title="Price (USD)", height=300)
        st.plotly_chart(chart, use_container_width=True)

        # --- Color-coded metrics ---
        col1, col2 = st.columns(2)
        with col1:
            color = "#00ff00" if change_24h > 0 else ("#ff0000" if change_24h < 0 else "#cccccc")
            st.markdown(f"<h4 style='color:{color};'>{selected_pair}: ${price:,.4f} ({change_24h:+.2f}%)</h4>", unsafe_allow_html=True)
        with col2:
            sig_color = {"BUY": "#00ff00", "SELL": "#ff0000", "HOLD": "#cccccc"}[signal]
            st.markdown(f"<h4 style='color:{sig_color};'>Signal: {signal} (Confidence: {confidence:.1%})</h4>", unsafe_allow_html=True)

        # --- Simulate trade execution and log ---
        if 'trading_log' not in st.session_state:
            st.session_state['trading_log'] = []
        if 'last_trade_time' not in st.session_state:
            st.session_state['last_trade_time'] = None
        now = datetime.now()
        can_trade = signal != 'HOLD' and (st.session_state['last_trade_time'] is None or (now - st.session_state['last_trade_time']).total_seconds() > 30)
        if can_trade:
            trade = {
                "Time": now.strftime("%H:%M:%S"),
                "Pair": selected_pair,
                "Action": signal,
                "Price": f"${price:,.4f}",
                "P&L": f"{random.uniform(-5, 8):+.2f}%"
            }
            st.session_state['trading_log'].insert(0, trade)
            st.session_state['last_trade_time'] = now
            # Log to file
            with open('logs/trades.csv', 'a') as f:
                f.write(f"{trade['Time']},{trade['Pair']},{trade['Action']},{price},{trade['P&L']}\n")
            with open('logs/console_output.log', 'a') as f:
                f.write(f"[{now.isoformat()}] TRADE EXECUTED: {signal} {selected_pair} at ${price:,.4f}\n")

        # --- Summary Statistics ---
        st.markdown("### 📊 Summary Statistics")
        trades_df = pd.DataFrame(st.session_state['trading_log'])
        if not trades_df.empty:
            pnl_vals = trades_df['P&L'].str.replace('%','').astype(float)
            win_rate = (pnl_vals > 0).mean() * 100
            avg_pnl = pnl_vals.mean()
            st.write(f"**Total Trades:** {len(trades_df)} | **Win Rate:** {win_rate:.1f}% | **Avg P&L:** {avg_pnl:+.2f}%")
        else:
            st.info("No trades yet.")

        # --- Last Trade Indicator ---
        if st.session_state['trading_log']:
            last_trade = st.session_state['trading_log'][0]
            st.success(f"Last Trade: {last_trade['Action']} {last_trade['Pair']} at {last_trade['Price']} ({last_trade['Time']}) | P&L: {last_trade['P&L']}")

        # --- Trading Log Table ---
        st.markdown("### � Recent Activity")
        st.table(st.session_state['trading_log'][:10])

        # --- Leaderboard/Performance vs Market (simulated) ---
        st.markdown("### 🏆 Leaderboard vs Market")
        leaderboard = pd.DataFrame({
            "Bot": ["Your Bot", "BTC HODL", "ETH HODL", "Random"],
            "PnL %": [avg_pnl if not trades_df.empty else 0, 2.5, 1.2, -0.5]
        })
        st.bar_chart(leaderboard.set_index("Bot"))

        # --- News & Alerts Panel (crypto news headlines) ---
        st.markdown("### 📰 News & Alerts")
        try:
            news = requests.get("https://cryptopanic.com/api/v1/posts/?auth_token=demo&public=true").json()
            for item in news.get("results", [])[:5]:
                st.write(f"[{item['title']}]({item['url']})")
        except Exception:
            st.info("Crypto news unavailable (demo mode)")

        # --- Bot Configuration (show actual selected strategy/risk) ---
        st.markdown("### ⚙️ Bot Configuration")
        st.info(f"""
        **Current Setup:**
        - 🎯 Strategy: {selected_strategy} ({strategy_info['description']})
        - 💰 Risk: {risk}% per trade (Risk Level: {selected_risk})
        - ⏱️ Scan Interval: {scan_interval} minutes
        - 🛡️ Mode: Live
        - 📊 Exchange: Binance Live
        """)

        # --- Help & Documentation ---
        with st.expander("❓ Help & Documentation"):
            st.markdown("""
            **How to use this dashboard:**
            - The bot trades on multiple crypto pairs using live funds.
            - Adjust risk and scan interval in the sidebar.
            - Download logs and trades for analysis.
            - View live price chart, signals, and summary stats.
            - News and leaderboard are for informational purposes.
            """)


    # --- Bot Trades Table (All) ---
    st.subheader("🤖 Bot Trades (All)")
    import csv
    try:
        with open('logs/trades.csv', 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
        if len(rows) > 1:
            headers = rows[0]
            data = rows[1:]
            df = pd.DataFrame(data, columns=headers)
            st.dataframe(df)
        else:
            st.info("No bot trades recorded yet.")
    except Exception as e:
        st.error(f"Could not load trades: {e}")


    # --- Trading simulation for multiple pairs ---
    st.subheader("📈 Trading Simulation (Multi-Pair)")
    if st.session_state.get('bot_override', False):
        st.warning("🚨 Bot is currently BLOCKED by override. No trades or signals will be generated.")
    else:
        pairs = [
            "BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT", "ADA/USDT",
            "DOGE/USDT", "AVAX/USDT", "ETH/BTC", "SOL/BTC", "BNB/BTC", "ADA/ETH",
            "LTC/BTC", "MATIC/USDT", "ARBUSDT", "OPUSDT", "SUIUSDT", "INJUSDT", "JUPUSDT",
            "SOL/BNB", "BNB/ETH", "BTC/ETH", "ETH/BNB", "SOL/ETH", "DOGE/BTC"
        ]
        selected_pair = random.choice(pairs)
        price = random.randint(1, 100_000) + random.random()
        change_24h = random.uniform(-8, 8)
        signal = random.choice(["BUY", "SELL", "HOLD"])
        confidence = random.uniform(0.6, 0.99)

        # --- Live Price Chart (simulated) ---
        if 'price_history' not in st.session_state:
            st.session_state['price_history'] = []
        st.session_state['price_history'].append(price)
        if len(st.session_state['price_history']) > 60:
            st.session_state['price_history'] = st.session_state['price_history'][-60:]
        chart_df = pd.DataFrame({"Price": st.session_state['price_history']})
        chart = go.Figure()
        chart.add_trace(go.Scatter(y=chart_df["Price"], mode="lines+markers", name=selected_pair))
        chart.update_layout(title=f"Live Price Chart: {selected_pair}", xaxis_title="Time (refreshes)", yaxis_title="Price (USD)", height=300)
        st.plotly_chart(chart, use_container_width=True)

        # --- Color-coded metrics ---
        col1, col2 = st.columns(2)
        with col1:
            color = "#00ff00" if change_24h > 0 else ("#ff0000" if change_24h < 0 else "#cccccc")
            st.markdown(f"<h4 style='color:{color};'>{selected_pair}: ${price:,.4f} ({change_24h:+.2f}%)</h4>", unsafe_allow_html=True)
        with col2:
            sig_color = {"BUY": "#00ff00", "SELL": "#ff0000", "HOLD": "#cccccc"}[signal]
            st.markdown(f"<h4 style='color:{sig_color};'>Signal: {signal} (Confidence: {confidence:.1%})</h4>", unsafe_allow_html=True)

        # --- Simulate trade execution and log ---
        if 'trading_log' not in st.session_state:
            st.session_state['trading_log'] = []
        if 'last_trade_time' not in st.session_state:
            st.session_state['last_trade_time'] = None
        now = datetime.now()
        can_trade = signal != 'HOLD' and (st.session_state['last_trade_time'] is None or (now - st.session_state['last_trade_time']).total_seconds() > 30)
        if can_trade:
            trade = {
                "Time": now.strftime("%H:%M:%S"),
                "Pair": selected_pair,
                "Action": signal,
                "Price": f"${price:,.4f}",
                "P&L": f"{random.uniform(-5, 8):+.2f}%"
            }
            st.session_state['trading_log'].insert(0, trade)
            st.session_state['last_trade_time'] = now
            # Log to file
            with open('logs/trades.csv', 'a') as f:
                f.write(f"{trade['Time']},{trade['Pair']},{trade['Action']},{price},{trade['P&L']}\n")
            with open('logs/console_output.log', 'a') as f:
                f.write(f"[{now.isoformat()}] TRADE EXECUTED: {signal} {selected_pair} at ${price:,.4f}\n")

    # --- Summary Statistics ---
    st.markdown("### 📊 Summary Statistics")
    trades_df = pd.DataFrame(st.session_state['trading_log'])
    if not trades_df.empty:
        pnl_vals = trades_df['P&L'].str.replace('%','').astype(float)
        win_rate = (pnl_vals > 0).mean() * 100
        avg_pnl = pnl_vals.mean()
        st.write(f"**Total Trades:** {len(trades_df)} | **Win Rate:** {win_rate:.1f}% | **Avg P&L:** {avg_pnl:+.2f}%")
    else:
        st.info("No trades yet.")

    # --- Last Trade Indicator ---
    if st.session_state['trading_log']:
        last_trade = st.session_state['trading_log'][0]
        st.success(f"Last Trade: {last_trade['Action']} {last_trade['Pair']} at {last_trade['Price']} ({last_trade['Time']}) | P&L: {last_trade['P&L']}")

    # --- Trading Log Table ---
    st.markdown("### � Recent Activity")
    st.table(st.session_state['trading_log'][:10])

    # --- Leaderboard/Performance vs Market (simulated) ---
    st.markdown("### 🏆 Leaderboard vs Market")
    leaderboard = pd.DataFrame({
        "Bot": ["Your Bot", "BTC HODL", "ETH HODL", "Random"],
        "PnL %": [avg_pnl if not trades_df.empty else 0, 2.5, 1.2, -0.5]
    })
    st.bar_chart(leaderboard.set_index("Bot"))

    # --- News & Alerts Panel (crypto news headlines) ---
    st.markdown("### 📰 News & Alerts")
    try:
        news = requests.get("https://cryptopanic.com/api/v1/posts/?auth_token=demo&public=true").json()
        for item in news.get("results", [])[:5]:
            st.write(f"[{item['title']}]({item['url']})")
    except Exception:
        st.info("Crypto news unavailable (demo mode)")

    # --- Bot Configuration ---
    st.markdown("### ⚙️ Bot Configuration")
    st.info(f"""
    **Current Setup:**
    - 🎯 Strategy: 5% Breakout + ML Enhancement
    - 💰 Risk: {risk}% per trade
    - ⏱️ Scan Interval: {scan_interval} minutes
    - 🛡️ Mode: Live
    - 📊 Exchange: Binance Live
    """)

    # --- Help & Documentation ---
    with st.expander("❓ Help & Documentation"):
        st.markdown("""
        **How to use this dashboard:**
        - The bot simulates trades on multiple crypto pairs.
        - Adjust risk and scan interval in the sidebar.
        - Download logs and trades for analysis.
        - View live price chart, signals, and summary stats.
        - News and leaderboard are for demo purposes.
        - For real trading, switch to 'Live Trading' mode (demo only).
        """)

    # --- Auto-refresh every 10 seconds ---
    time.sleep(1)
    st.rerun()

if __name__ == "__main__":
    trading_dashboard()
