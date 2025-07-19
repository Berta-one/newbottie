"""
dashboard.py (Modular Analytics)
================================
Provides advanced analytics rendering for integration into hybrid_bot.py.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import json
import os
from datetime import datetime
from typing import Dict, List, Any
import io


class TradingDashboard:
    def __init__(self):
        self.trade_data_file = 'logs/trades.csv'
        self.performance_file = 'logs/performance.json'
        self.scan_results_file = 'logs/latest_scan.json'
        self.positions_file = 'logs/active_positions.json'

    # -------------------------------
    # Data Loaders
    # -------------------------------
    def load_trade_data(self) -> pd.DataFrame:
        try:
            if os.path.exists(self.trade_data_file):
                df = pd.read_csv(self.trade_data_file)
                if not df.empty:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df['trade_date'] = df['timestamp'].dt.date
                    df['trade_hour'] = df['timestamp'].dt.hour
                    df['cumulative_pnl'] = df['pnl_percent'].cumsum()
                    df['performance_category'] = df['pnl_percent'].apply(
                        lambda x: 'Win' if x > 0 else 'Loss' if x < 0 else 'Break-even'
                    )
                    return df
            return pd.DataFrame(columns=[
                'timestamp', 'symbol', 'signal_type', 'entry_price', 'exit_price',
                'quantity', 'pnl_percent', 'pnl_amount', 'confidence', 'reason',
                'time_held_minutes', 'category', 'volatility', 'volume_ratio'
            ])
        except Exception as e:
            st.error(f"Error loading trade data: {e}")
            return pd.DataFrame()

    def load_scan_results(self) -> Dict[str, Any]:
        try:
            if os.path.exists(self.scan_results_file):
                with open(self.scan_results_file, 'r') as f:
                    return json.load(f)
            return {"opportunities": [], "scan_time": datetime.now().isoformat()}
        except Exception as e:
            st.error(f"Error loading scan results: {e}")
            return {"opportunities": [], "scan_time": datetime.now().isoformat()}

    def load_active_positions(self) -> List[Dict[str, Any]]:
        try:
            if os.path.exists(self.positions_file):
                with open(self.positions_file, 'r') as f:
                    data = json.load(f)
                    return list(data.get('active', {}).values())
            return []
        except Exception as e:
            st.error(f"Error loading positions: {e}")
            return []

    # -------------------------------
    # Metrics Calculation
    # -------------------------------
    def calculate_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        if df.empty:
            return {
                'total_trades': 0, 'win_rate': 0.0, 'total_pnl_percent': 0.0,
                'average_win': 0.0, 'average_loss': 0.0, 'profit_factor': 0.0,
                'sharpe_ratio': 0.0, 'max_drawdown': 0.0, 'volatility': 0.0,
                'max_consecutive_losses': 0, 'best_trade': 0.0, 'worst_trade': 0.0,
                'avg_hold_time': 0.0, 'total_pnl_usd': 0.0
            }

        wins = df[df['pnl_percent'] > 0]
        losses = df[df['pnl_percent'] < 0]

        total_trades = len(df)
        win_rate = len(wins) / total_trades * 100 if total_trades > 0 else 0
        total_pnl_percent = df['pnl_percent'].sum()
        total_pnl_usd = df['pnl_amount'].sum() if 'pnl_amount' in df.columns else 0

        average_win = wins['pnl_percent'].mean() if len(wins) > 0 else 0
        average_loss = abs(losses['pnl_percent'].mean()) if len(losses) > 0 else 0
        profit_factor = (wins['pnl_percent'].sum() / abs(losses['pnl_percent'].sum())) if len(losses) > 0 else float('inf')

        returns = df['pnl_percent'].values
        volatility = np.std(returns) if len(returns) > 1 else 0
        sharpe_ratio = (np.mean(returns) / volatility) if volatility > 0 else 0

        cumulative = df['cumulative_pnl'].values
        peak = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - peak)
        max_drawdown = abs(np.min(drawdown)) if len(drawdown) > 0 else 0

        consecutive_losses = 0
        max_consecutive_losses = 0
        for pnl in df['pnl_percent']:
            if pnl < 0:
                consecutive_losses += 1
                max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
            else:
                consecutive_losses = 0

        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'total_pnl_percent': total_pnl_percent,
            'total_pnl_usd': total_pnl_usd,
            'average_win': average_win,
            'average_loss': average_loss,
            'profit_factor': profit_factor,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'volatility': volatility,
            'max_consecutive_losses': max_consecutive_losses,
            'best_trade': df['pnl_percent'].max(),
            'worst_trade': df['pnl_percent'].min(),
            'avg_hold_time': df['time_held_minutes'].mean() if 'time_held_minutes' in df.columns else 0
        }

    # -------------------------------
    # Rendering Functions for Analytics Tab
    # -------------------------------
    def render_analytics_dashboard(self):
        df = self.load_trade_data()
        metrics = self.calculate_metrics(df)

        self.render_performance_overview(df, metrics)
        st.markdown("---")
        self.render_performance_charts(df)
        st.markdown("---")
        self.render_trade_analysis(df)
        st.markdown("---")
        self.render_recent_trades(df)
        st.markdown("---")
        self.render_scan_results()
        st.markdown("---")
        self.render_risk_metrics(df, metrics)
        st.markdown("---")
        self.render_advanced_analytics(df)

    # ✅ Implementations for render_* methods will reuse your original code snippets
    def render_performance_overview(self, df, metrics):
        st.header("📊 Performance Overview")
        st.write(metrics)

    def render_performance_charts(self, df):
        st.subheader("Performance Charts Coming Soon...")

    def render_trade_analysis(self, df):
        st.subheader("Detailed Trade Analysis Coming Soon...")

    def render_recent_trades(self, df):
        st.subheader("Recent Trades Coming Soon...")

    def render_scan_results(self):
        st.subheader("Scan Results Coming Soon...")

    def render_risk_metrics(self, df, metrics):
        st.subheader("Risk Analysis Coming Soon...")

    def render_advanced_analytics(self, df):
        st.subheader("Advanced Analytics Coming Soon...")