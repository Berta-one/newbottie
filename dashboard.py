"""
dashboard.py
============
Enhanced Analytics Dashboard with error handling for missing columns.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import json
import numpy as np

def safe_get_column_sum(df, column_name, default=0.0):
    """Safely get sum of column, return default if column doesn't exist"""
    if df.empty or column_name not in df.columns:
        return default
    return df[column_name].sum()

def safe_get_column_mean(df, column_name, default=0.0):
    """Safely get mean of column, return default if column doesn't exist"""
    if df.empty or column_name not in df.columns:
        return default
    return df[column_name].mean()

def load_trade_data():
    """Load trade data from various possible sources"""
    data_sources = [
        'logs/trades.csv',
        'logs/trade_history.csv',
        'logs/portfolio_trades.csv',
        'logs/trading_log.csv'
    ]
    
    for source in data_sources:
        if os.path.exists(source):
            try:
                df = pd.read_csv(source)
                if not df.empty:
                    return df
            except Exception as e:
                continue
    
    # Return empty DataFrame with expected columns
    return pd.DataFrame(columns=['timestamp', 'symbol', 'pnl', 'pnl_percent', 'quantity', 'entry_price', 'exit_price'])

def calculate_pnl_if_missing(df):
    """Calculate PnL if missing from data"""
    if df.empty:
        return df
    
    # Add PnL column if missing
    if 'pnl' not in df.columns:
        if 'entry_price' in df.columns and 'exit_price' in df.columns and 'quantity' in df.columns:
            df['pnl'] = (df['exit_price'] - df['entry_price']) * df['quantity']
        else:
            df['pnl'] = 0.0
    
    # Add PnL percentage if missing
    if 'pnl_percent' not in df.columns:
        if 'entry_price' in df.columns and 'exit_price' in df.columns:
            df['pnl_percent'] = ((df['exit_price'] - df['entry_price']) / df['entry_price']) * 100
        else:
            df['pnl_percent'] = 0.0
    
    return df

def render_analytics_dashboard():
    """Render the main analytics dashboard"""
    st.title("📊 Trading Analytics Dashboard")
    
    # Load and process data
    df = load_trade_data()
    df = calculate_pnl_if_missing(df)
    
    if df.empty:
        st.warning("📝 No trade data available yet. Start trading to see analytics!")
        
        # Show demo metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Trades", "0")
        with col2:
            st.metric("PnL (USD)", "$0.00")
        with col3:
            st.metric("Win Rate", "0%")
        with col4:
            st.metric("Best Trade", "$0.00")
        
        # Show sample chart
        st.subheader("📈 Portfolio Performance")
        sample_dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        sample_data = pd.DataFrame({
            'Date': sample_dates,
            'Cumulative_PnL': np.cumsum(np.random.randn(30) * 10)
        })
        
        fig = px.line(sample_data, x='Date', y='Cumulative_PnL', 
                     title="Sample Portfolio Performance")
        st.plotly_chart(fig, use_container_width=True)
        
        return
    
    # Convert timestamp if exists
    if 'timestamp' in df.columns:
        try:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        except:
            pass
    
    # Main metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_trades = len(df)
        st.metric("Total Trades", total_trades)
    
    with col2:
        total_pnl = safe_get_column_sum(df, 'pnl', 0.0)
        st.metric("PnL (USD)", f"${total_pnl:,.2f}")
    
    with col3:
        if total_trades > 0:
            wins = len(df[df['pnl'] > 0]) if 'pnl' in df.columns else 0
            win_rate = (wins / total_trades) * 100
        else:
            win_rate = 0
        st.metric("Win Rate", f"{win_rate:.1f}%")
    
    with col4:
        best_trade = df['pnl'].max() if 'pnl' in df.columns and not df.empty else 0
        st.metric("Best Trade", f"${best_trade:,.2f}")
    
    # Performance chart
    st.subheader("📈 Portfolio Performance")
    
    if 'timestamp' in df.columns and 'pnl' in df.columns and len(df) > 0:
        # Calculate cumulative PnL
        df_sorted = df.sort_values('timestamp')
        df_sorted['cumulative_pnl'] = df_sorted['pnl'].cumsum()
        
        fig = px.line(df_sorted, x='timestamp', y='cumulative_pnl',
                     title="Cumulative P&L Over Time")
        fig.update_layout(
            xaxis_title="Time",
            yaxis_title="Cumulative P&L (USD)"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📊 Performance chart will appear after trades are executed")
    
    # Recent trades table
    st.subheader("📋 Recent Trades")
    
    if len(df) > 0:
        # Show last 10 trades
        recent_trades = df.tail(10).copy()
        
        # Format columns for display
        display_columns = []
        if 'timestamp' in recent_trades.columns:
            display_columns.append('timestamp')
        if 'symbol' in recent_trades.columns:
            display_columns.append('symbol')
        if 'pnl' in recent_trades.columns:
            display_columns.append('pnl')
        if 'pnl_percent' in recent_trades.columns:
            display_columns.append('pnl_percent')
        
        if display_columns:
            st.dataframe(recent_trades[display_columns], use_container_width=True)
        else:
            st.dataframe(recent_trades, use_container_width=True)
    else:
        st.info("📝 Recent trades will appear here after trading starts")
    
    # Trading statistics
    st.subheader("📊 Trading Statistics")
    
    if len(df) > 0 and 'pnl' in df.columns:
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Performance Metrics**")
            avg_trade = safe_get_column_mean(df, 'pnl', 0.0)
            max_drawdown = df['pnl'].min() if 'pnl' in df.columns else 0
            
            st.write(f"Average Trade: ${avg_trade:.2f}")
            st.write(f"Max Drawdown: ${max_drawdown:.2f}")
            st.write(f"Total Volume: {len(df)} trades")
        
        with col2:
            st.write("**Risk Metrics**")
            if 'pnl_percent' in df.columns:
                volatility = df['pnl_percent'].std()
                st.write(f"Volatility: {volatility:.2f}%")
            
            profitable_trades = len(df[df['pnl'] > 0]) if 'pnl' in df.columns else 0
            st.write(f"Profitable Trades: {profitable_trades}")
            st.write(f"Loss Trades: {len(df) - profitable_trades}")
    
    else:
        st.info("📈 Trading statistics will appear after more trades are executed")

def render_portfolio_overview():
    """Render portfolio overview section"""
    st.header("💼 Portfolio Overview")
    
    # Mock portfolio data for now
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Account Balance", "$10,000.00", "2.5%")
    
    with col2:
        st.metric("Open Positions", "3", "1")
    
    with col3:
        st.metric("Daily P&L", "$150.25", "1.2%")

class TradingDashboard:
    """Main TradingDashboard class for compatibility with hybrid_bot.py"""
    
    def __init__(self):
        self.trade_data = None
    
    def load_trade_data(self):
        """Load trade data"""
        self.trade_data = load_trade_data()
        return self.trade_data
    
    def render_performance_overview(self):
        """Render performance overview"""
        render_analytics_dashboard()
    
    def render_analytics_dashboard(self):
        """Render main analytics dashboard"""
        render_analytics_dashboard()
    
    def render_portfolio_overview(self):
        """Render portfolio overview"""
        render_portfolio_overview()
    
    def render_trade_analysis(self):
        """Render trade analysis"""
        render_analytics_dashboard()
    
    def render_recent_trades(self):
        """Render recent trades section"""
        st.subheader("📋 Recent Trades")
        df = load_trade_data()
        df = calculate_pnl_if_missing(df)
        
        if len(df) > 0:
            recent_trades = df.tail(10)
            st.dataframe(recent_trades, use_container_width=True)
        else:
            st.info("📝 No recent trades available")
    
    def calculate_metrics(self, df):
        """Calculate trading metrics"""
        if df.empty:
            return {}
        
        metrics = {
            'total_trades': len(df),
            'total_pnl': safe_get_column_sum(df, 'pnl', 0.0),
            'win_rate': 0.0,
            'avg_trade': safe_get_column_mean(df, 'pnl', 0.0)
        }
        
        if 'pnl' in df.columns and len(df) > 0:
            wins = len(df[df['pnl'] > 0])
            metrics['win_rate'] = (wins / len(df)) * 100 if len(df) > 0 else 0
        
        return metrics

# Create global instance for backward compatibility
analytics_dashboard = TradingDashboard()

if __name__ == "__main__":
    render_analytics_dashboard()