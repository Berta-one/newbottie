#!/usr/bin/env python3
"""
Streamlit Backtesting Integration
Wraps BacktestEngineReal so hybrid_bot.py can render a working Backtesting tab.
"""

import io
import traceback
import streamlit as st
from datetime import datetime
import plotly.graph_objects as go  # for charts

# Dependency check
try:
    import ccxt  # noqa: F401
    import scipy  # noqa: F401
    DEPS_OK = True
    DEPS_ERR = None
except Exception as e:
    DEPS_OK = False
    DEPS_ERR = e

# Pull in your real backtest engine
from backtest_engine_real import BacktestEngineReal


class BacktestingIntegration:
    """
    Lightweight UI wrapper used by hybrid_bot.py.
    """

    def __init__(self):
        if not DEPS_OK:
            raise RuntimeError(
                f"Backtesting dependencies missing or broken: {DEPS_ERR}"
            )

    def _run_engine(self, pairs, timeframe, capital, fee_rate, days=365, refresh_cache=False):
        engine = BacktestEngineReal(
            pairs=pairs,
            timeframe=timeframe,
            capital=capital,
            fee_rate=fee_rate,
        )
        df = engine.run_backtest(days=days, refresh_cache=refresh_cache)

        # Save reference to raw OHLCV data (for charts)
        self.raw_data = getattr(engine, "raw_data", {})
        self.data_info = {pair: f"{days} days of {timeframe} data loaded" for pair in pairs}
        return df

    def _plot_price_chart(self, df_price, pair):
        """
        Create a simple candlestick chart using Plotly for the given pair's data.
        """
        fig = go.Figure(
            data=[
                go.Candlestick(
                    x=df_price["timestamp"],
                    open=df_price["open"],
                    high=df_price["high"],
                    low=df_price["low"],
                    close=df_price["close"],
                    name=pair
                )
            ]
        )
        fig.update_layout(
            title=f"{pair} Price History",
            xaxis_rangeslider_visible=False,
            template="plotly_dark",
            height=400
        )
        return fig

    def render_backtesting_tab(self):
        st.header("🔬 Backtesting")
        st.caption("Run historical strategy sweeps across ML / Quantum / Technical weights.")

        # --- Inputs ---
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            pairs_text = st.text_input(
                "Pairs (comma‑sep)",
                value="BTCUSDT,ETHUSDT,SOLUSDT",
                help="Symbols must exist on Binance. Use USDT quote.",
            )
        with col2:
            timeframe = st.selectbox(
                "Timeframe",
                ["1m", "5m", "15m", "1h", "4h", "1d"],
                index=3,  # default 1h
            )
        with col3:
            capital = st.number_input(
                "Starting Capital (USDT)",
                min_value=100,
                max_value=1_000_000,
                value=1_000,
                step=100,
            )
        with col4:
            fee_rate = st.number_input(
                "Fee Rate",
                min_value=0.0,
                max_value=0.01,
                value=0.001,
                step=0.0001,
                format="%.4f",
                help="Trading fee fraction per round‑trip.",
            )

        # --- Lookback Period ---
        lookback_option = st.selectbox(
            "Historical Lookback",
            ["1M", "3M", "6M", "1Y", "2Y"],
            index=3  # default 1Y
        )
        lookback_days = {
            "1M": 30,
            "3M": 90,
            "6M": 180,
            "1Y": 365,
            "2Y": 730
        }[lookback_option]

        refresh_cache = st.checkbox("Force re-download historical data", value=False)
        pairs = [p.strip().upper() for p in pairs_text.split(",") if p.strip()]

        run_bt = st.button("🚀 Run Backtest", type="primary")

        if run_bt:
            with st.spinner(f"Fetching data & running simulations ({lookback_option} lookback)..."):
                try:
                    df = self._run_engine(
                        pairs=pairs,
                        timeframe=timeframe,
                        capital=capital,
                        fee_rate=fee_rate,
                        days=lookback_days,
                        refresh_cache=refresh_cache,
                    )
                except Exception as e:
                    st.error(f"Backtest failed: {e}")
                    st.exception(e)
                    return

            if df is None or df.empty:
                st.warning("No results returned.")
                return

            # Display summary metrics
            st.subheader("Results")
            st.dataframe(df, use_container_width=True)

            # --- Show data info + charts ---
            if hasattr(self, "data_info"):
                for p, info in self.data_info.items():
                    st.caption(f"📊 {p}: {info}")
                    if p in self.raw_data:
                        st.plotly_chart(self._plot_price_chart(self.raw_data[p], p), use_container_width=True)

            # --- APPLY STRATEGY TO MULTI‑STRATEGY TAB ---
            weight_cols = {"Quantum Weight", "ML Weight", "Technical Weight"}
            if weight_cols.issubset(df.columns):
                st.subheader("🎯 Apply Strategy")
                st.caption("Click to push these weights into the Multi‑Strategy tab sliders.")

                for i, row in df.iterrows():
                    q = int(row["Quantum Weight"])
                    ml = int(row["ML Weight"])
                    tech = int(row["Technical Weight"])

                    # Normalize to 100 if needed
                    tot = q + ml + tech
                    if tot != 100 and tot > 0:
                        scale = 100 / tot
                        q = int(round(q * scale))
                        ml = int(round(ml * scale))
                        tech = 100 - q - ml

                    info_col, btn_col = st.columns([4, 1])
                    with info_col:
                        st.write(f"**{row['Pair']}** | Q:{q}% ML:{ml}% Tech:{tech}%")
                    with btn_col:
                        if st.button("Set", key=f"apply_strategy_{i}"):

                            st.session_state["weight_quantum"] = q
                            st.session_state["weight_ml"] = ml
                            st.session_state["weight_technical"] = tech
                            st.session_state["multi_quantum_weight_slider"] = q
                            st.session_state["multi_ml_weight_slider"] = ml
                            st.session_state["multi_technical_weight_slider"] = tech
                            st.session_state["last_applied_strategy"] = {
                                "source": row["Pair"],
                                "q": q,
                                "ml": ml,
                                "tech": tech,
                                "time": datetime.utcnow().isoformat(timespec="seconds") + "Z",
                            }
                            st.success(f"✅ Applied strategy from {row['Pair']}!")
                            st.rerun()

            # Aggregate performance
            agg = df.groupby("Pair").agg(
                {
                    "ROI (USDT)": "mean",
                    "Win Rate": "mean",
                    "Trades": "sum",
                    "Max Drawdown (%)": "mean",
                }
            )
            st.write("**Averages by Pair**")
            st.dataframe(agg, use_container_width=True)

            # Download
            csv_buf = io.StringIO()
            df.to_csv(csv_buf, index=False)
            st.download_button(
                "💾 Download CSV",
                data=csv_buf.getvalue(),
                file_name="backtest_results.csv",
                mime="text/csv",
            )

        # Diagnostics
        with st.expander("⚙️ Diagnostics"):
            st.write(f"Dependencies OK: {DEPS_OK}")
            if DEPS_ERR:
                st.write(f"Error: {DEPS_ERR}")
            st.code(traceback.format_exc(), language="python")
