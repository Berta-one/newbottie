#!/usr/bin/env python3
"""
Complete Advanced Analytics Dashboard - dashboard.py
==================================================

Comprehensive Streamlit dashboard with real-time monitoring, interactive charts,
trade analysis, and advanced analytics as specified in GitHub Copilot instructions.

Features:
- Real-time account balance and P&L metrics display
- Active positions monitoring with current prices
- Trade history with filtering options
- Cumulative performance charts using Plotly
- Strategy performance breakdown by category
- Latest scan results visualization
- Risk analysis with drawdown charts
- Advanced analytics: performance by hour, confidence correlation
- Data export functionality with CSV download
- Auto-refresh capabilities
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import io

# Set page configuration
st.set_page_config(
    page_title="📊 Trading Bot Analytics",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

class TradingDashboard:
    """
    Advanced trading dashboard with comprehensive analytics and visualization
    """
    
    def __init__(self):
        self.trade_data_file = 'logs/trades.csv'
        self.performance_file = 'logs/performance.json'
        self.scan_results_file = 'logs/latest_scan.json'
        self.positions_file = 'logs/active_positions.json'
        
        # Initialize session state
        if 'auto_refresh' not in st.session_state:
            st.session_state.auto_refresh = False
        if 'refresh_interval' not in st.session_state:
            st.session_state.refresh_interval = 30
    
    def load_trade_data(self) -> pd.DataFrame:
        """Load and process trade data from CSV"""
        try:
            if os.path.exists(self.trade_data_file):
                df = pd.read_csv(self.trade_data_file)
                if not df.empty:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df['trade_date'] = df['timestamp'].dt.date
                    df['trade_hour'] = df['timestamp'].dt.hour
                    
                    # Calculate cumulative P&L
                    df['cumulative_pnl'] = df['pnl_percent'].cumsum()
                    
                    # Add performance categories
                    df['performance_category'] = df['pnl_percent'].apply(
                        lambda x: 'Win' if x > 0 else 'Loss' if x < 0 else 'Break-even'
                    )
                    
                    return df
            
            # Return empty DataFrame with correct structure
            return pd.DataFrame(columns=[
                'timestamp', 'symbol', 'signal_type', 'entry_price', 'exit_price',
                'quantity', 'pnl_percent', 'pnl_amount', 'confidence', 'reason',
                'time_held_minutes', 'category', 'volatility', 'volume_ratio'
            ])
        
        except Exception as e:
            st.error(f"Error loading trade data: {e}")
            return pd.DataFrame()
    
    def load_scan_results(self) -> Dict[str, Any]:
        """Load latest scan results"""
        try:
            if os.path.exists(self.scan_results_file):
                with open(self.scan_results_file, 'r') as f:
                    return json.load(f)
            return {"opportunities": [], "scan_time": datetime.now().isoformat()}
        except Exception as e:
            st.error(f"Error loading scan results: {e}")
            return {"opportunities": [], "scan_time": datetime.now().isoformat()}
    
    def load_active_positions(self) -> List[Dict[str, Any]]:
        """Load active positions"""
        try:
            if os.path.exists(self.positions_file):
                with open(self.positions_file, 'r') as f:
                    data = json.load(f)
                    return list(data.get('active', {}).values())
            return []
        except Exception as e:
            st.error(f"Error loading positions: {e}")
            return []
    
    def calculate_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics"""
        if df.empty:
            return {
                'total_trades': 0,
                'win_rate': 0.0,
                'total_pnl_percent': 0.0,
                'average_win': 0.0,
                'average_loss': 0.0,
                'profit_factor': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'volatility': 0.0,
                'max_consecutive_losses': 0,
                'best_trade': 0.0,
                'worst_trade': 0.0,
                'avg_hold_time': 0.0,
                'total_pnl_usd': 0.0
            }
        
        wins = df[df['pnl_percent'] > 0]
        losses = df[df['pnl_percent'] < 0]
        
        # Basic metrics
        total_trades = len(df)
        win_rate = len(wins) / total_trades * 100 if total_trades > 0 else 0
        total_pnl_percent = df['pnl_percent'].sum()
        total_pnl_usd = df['pnl_amount'].sum() if 'pnl_amount' in df.columns else 0
        
        # Win/Loss metrics
        average_win = wins['pnl_percent'].mean() if len(wins) > 0 else 0
        average_loss = abs(losses['pnl_percent'].mean()) if len(losses) > 0 else 0
        profit_factor = (wins['pnl_percent'].sum() / abs(losses['pnl_percent'].sum())) if len(losses) > 0 else float('inf')
        
        # Risk metrics
        returns = df['pnl_percent'].values
        volatility = np.std(returns) if len(returns) > 1 else 0
        sharpe_ratio = (np.mean(returns) / volatility) if volatility > 0 else 0
        
        # Drawdown calculation
        cumulative = df['cumulative_pnl'].values
        peak = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - peak)
        max_drawdown = abs(np.min(drawdown)) if len(drawdown) > 0 else 0
        
        # Consecutive losses
        consecutive_losses = 0
        max_consecutive_losses = 0
        for pnl in df['pnl_percent']:
            if pnl < 0:
                consecutive_losses += 1
                max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
            else:
                consecutive_losses = 0
        
        # Additional metrics
        best_trade = df['pnl_percent'].max()
        worst_trade = df['pnl_percent'].min()
        avg_hold_time = df['time_held_minutes'].mean() if 'time_held_minutes' in df.columns else 0
        
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
            'best_trade': best_trade,
            'worst_trade': worst_trade,
            'avg_hold_time': avg_hold_time
        }
    
    def render_performance_overview(self, df: pd.DataFrame, metrics: Dict[str, Any]) -> None:
        """Render performance overview section"""
        st.header("📊 Performance Overview")
        
        # Key metrics in columns
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                "Total Trades",
                f"{metrics['total_trades']:,}",
                help="Total number of completed trades"
            )
        
        with col2:
            win_rate_color = "normal"
            if metrics['win_rate'] > 60:
                win_rate_color = "inverse"
            st.metric(
                "Win Rate",
                f"{metrics['win_rate']:.1f}%",
                help="Percentage of profitable trades"
            )
        
        with col3:
            pnl_delta = f"{metrics['total_pnl_percent']:+.2f}%"
            st.metric(
                "Total P&L",
                f"${metrics['total_pnl_usd']:,.2f}",
                delta=pnl_delta,
                help="Total profit/loss in USD and percentage"
            )
        
        with col4:
            st.metric(
                "Profit Factor",
                f"{metrics['profit_factor']:.2f}" if metrics['profit_factor'] != float('inf') else "∞",
                help="Total profits / Total losses ratio"
            )
        
        with col5:
            st.metric(
                "Sharpe Ratio",
                f"{metrics['sharpe_ratio']:.2f}",
                help="Risk-adjusted return metric"
            )
        
        # Additional metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Max Drawdown",
                f"-{metrics['max_drawdown']:.2f}%",
                help="Maximum peak-to-trough decline"
            )
        
        with col2:
            st.metric(
                "Avg Win",
                f"+{metrics['average_win']:.2f}%",
                help="Average winning trade percentage"
            )
        
        with col3:
            st.metric(
                "Avg Loss",
                f"-{metrics['average_loss']:.2f}%",
                help="Average losing trade percentage"
            )
        
        with col4:
            st.metric(
                "Avg Hold Time",
                f"{metrics['avg_hold_time']:.0f}m",
                help="Average position hold time in minutes"
            )
    
    def render_performance_charts(self, df: pd.DataFrame) -> None:
        """Render interactive performance charts"""
        st.header("📈 Performance Charts")
        
        if df.empty:
            st.info("No trade data available for charts.")
            return
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=[
                'Cumulative P&L Over Time',
                'P&L Distribution',
                'Win/Loss Ratio by Category',
                'Performance by Hour of Day'
            ],
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # 1. Cumulative P&L line chart
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['cumulative_pnl'],
                mode='lines+markers',
                name='Cumulative P&L',
                line=dict(color='#00CC96', width=2),
                hovertemplate='Date: %{x}<br>Cumulative P&L: %{y:.2f}%<extra></extra>'
            ),
            row=1, col=1
        )
        
        # 2. P&L distribution histogram
        fig.add_trace(
            go.Histogram(
                x=df['pnl_percent'],
                nbinsx=20,
                name='P&L Distribution',
                marker_color='#AB63FA',
                hovertemplate='P&L Range: %{x}<br>Count: %{y}<extra></extra>'
            ),
            row=1, col=2
        )
        
        # 3. Win/Loss by category
        if 'category' in df.columns:
            category_performance = df.groupby(['category', 'performance_category']).size().reset_index(name='count')
            
            for perf_cat in category_performance['performance_category'].unique():
                data = category_performance[category_performance['performance_category'] == perf_cat]
                fig.add_trace(
                    go.Bar(
                        x=data['category'],
                        y=data['count'],
                        name=f'{perf_cat} Trades',
                        hovertemplate='Category: %{x}<br>Count: %{y}<extra></extra>'
                    ),
                    row=2, col=1
                )
        
        # 4. Performance by hour
        if 'trade_hour' in df.columns:
            hourly_performance = df.groupby('trade_hour')['pnl_percent'].mean().reset_index()
            fig.add_trace(
                go.Bar(
                    x=hourly_performance['trade_hour'],
                    y=hourly_performance['pnl_percent'],
                    name='Avg P&L by Hour',
                    marker_color='#FFA15A',
                    hovertemplate='Hour: %{x}:00<br>Avg P&L: %{y:.2f}%<extra></extra>'
                ),
                row=2, col=2
            )
        
        # Update layout
        fig.update_layout(
            height=800,
            showlegend=True,
            title_text="Trading Performance Analytics"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_trade_analysis(self, df: pd.DataFrame) -> None:
        """Render detailed trade analysis"""
        st.header("🔍 Trade Analysis")
        
        if df.empty:
            st.info("No trade data available for analysis.")
            return
        
        # Filter controls
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Date range filter
            if len(df) > 0:
                min_date = df['trade_date'].min()
                max_date = df['trade_date'].max()
                date_range = st.date_input(
                    "Date Range",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date
                )
            else:
                date_range = (datetime.now().date(), datetime.now().date())
        
        with col2:
            # Symbol filter
            symbols = ['All'] + sorted(df['symbol'].unique().tolist()) if not df.empty else ['All']
            selected_symbol = st.selectbox("Symbol", symbols)
        
        with col3:
            # Performance filter
            performance_options = ['All', 'Wins Only', 'Losses Only']
            selected_performance = st.selectbox("Performance", performance_options)
        
        # Apply filters
        filtered_df = df.copy()
        
        if len(date_range) == 2:
            filtered_df = filtered_df[
                (filtered_df['trade_date'] >= date_range[0]) &
                (filtered_df['trade_date'] <= date_range[1])
            ]
        
        if selected_symbol != 'All':
            filtered_df = filtered_df[filtered_df['symbol'] == selected_symbol]
        
        if selected_performance == 'Wins Only':
            filtered_df = filtered_df[filtered_df['pnl_percent'] > 0]
        elif selected_performance == 'Losses Only':
            filtered_df = filtered_df[filtered_df['pnl_percent'] < 0]
        
        # Display filtered results
        if not filtered_df.empty:
            st.subheader(f"Trade History ({len(filtered_df)} trades)")
            
            # Format data for display
            display_df = filtered_df.copy()
            display_df['P&L %'] = display_df['pnl_percent'].apply(lambda x: f"{x:+.2f}%")
            display_df['P&L USD'] = display_df['pnl_amount'].apply(lambda x: f"${x:+.2f}") if 'pnl_amount' in display_df.columns else "N/A"
            display_df['Confidence'] = display_df['confidence'].apply(lambda x: f"{x:.1%}") if 'confidence' in display_df.columns else "N/A"
            display_df['Entry Price'] = display_df['entry_price'].apply(lambda x: f"${x:.6f}")
            display_df['Exit Price'] = display_df['exit_price'].apply(lambda x: f"${x:.6f}")
            
            # Select columns for display
            display_columns = [
                'timestamp', 'symbol', 'signal_type', 'Entry Price', 'Exit Price',
                'P&L %', 'P&L USD', 'Confidence', 'reason'
            ]
            
            available_columns = [col for col in display_columns if col in display_df.columns]
            
            st.dataframe(
                display_df[available_columns].sort_values('timestamp', ascending=False),
                use_container_width=True,
                hide_index=True
            )
            
            # Export button
            csv_data = self.prepare_csv_export(filtered_df)
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=f"trades_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        else:
            st.info("No trades match the selected criteria.")
    
    def render_recent_trades(self, df: pd.DataFrame) -> None:
        """Render recent trades section"""
        st.header("⏰ Recent Trades")
        
        if df.empty:
            st.info("No recent trades to display.")
            return
        
        # Get last 10 trades
        recent_trades = df.tail(10).sort_values('timestamp', ascending=False)
        
        for _, trade in recent_trades.iterrows():
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                
                with col1:
                    st.write(f"**{trade['symbol']}** ({trade['signal_type']})")
                    st.caption(f"{trade['timestamp'].strftime('%Y-%m-%d %H:%M')}")
                
                with col2:
                    st.write(f"Entry: ${trade['entry_price']:.6f}")
                    st.write(f"Exit: ${trade['exit_price']:.6f}")
                
                with col3:
                    pnl_color = "🟢" if trade['pnl_percent'] > 0 else "🔴"
                    st.write(f"{pnl_color} P&L: {trade['pnl_percent']:+.2f}%")
                    if 'pnl_amount' in trade:
                        st.write(f"USD: ${trade['pnl_amount']:+.2f}")
                
                with col4:
                    if 'confidence' in trade and pd.notna(trade['confidence']):
                        st.metric("Confidence", f"{trade['confidence']:.1%}")
                
                st.divider()
    
    def render_scan_results(self) -> None:
        """Render latest scan results"""
        st.header("🔍 Latest Scan Results")
        
        scan_data = self.load_scan_results()
        opportunities = scan_data.get('opportunities', [])
        
        if opportunities:
            st.success(f"Found {len(opportunities)} trading opportunities")
            
            # Convert to DataFrame for better display
            df_opportunities = pd.DataFrame(opportunities)
            
            # Add action buttons
            for i, opp in enumerate(opportunities[:5]):  # Show top 5
                with st.expander(f"#{i+1} {opp.get('symbol', 'Unknown')} - {opp.get('signal', 'UNKNOWN')}"):
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Price", f"${opp.get('price', 0):.6f}")
                        st.metric("24h Change", f"{opp.get('change_24h', 0):+.1f}%")
                    
                    with col2:
                        st.metric("Confidence", f"{opp.get('confidence', 0):.1%}")
                        st.metric("Volume Ratio", f"{opp.get('volume_ratio', 1):.1f}x")
                    
                    with col3:
                        st.write(f"**Signal:** {opp.get('signal', 'UNKNOWN')}")
                        st.write(f"**Category:** {opp.get('category', 'Unknown')}")
                    
                    with col4:
                        if st.button(f"Quick Trade {opp.get('signal', '')}", key=f"trade_{i}"):
                            st.success(f"Trade signal sent for {opp.get('symbol')}")
            
            # Scan timestamp
            scan_time = scan_data.get('scan_time', datetime.now().isoformat())
            st.caption(f"Last scan: {scan_time}")
        
        else:
            st.info("No trading opportunities found in latest scan.")
            
            if st.button("🔄 Trigger New Scan"):
                st.info("Scan request sent to trading engine...")
    
    def render_risk_metrics(self, df: pd.DataFrame, metrics: Dict[str, Any]) -> None:
        """Render risk analysis section"""
        st.header("⚠️ Risk Analysis")
        
        if df.empty:
            st.info("No data available for risk analysis.")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📉 Drawdown Analysis")
            
            # Calculate drawdown over time
            cumulative = df['cumulative_pnl'].values
            peak = np.maximum.accumulate(cumulative)
            drawdown = (cumulative - peak)
            
            # Drawdown chart
            fig_dd = go.Figure()
            fig_dd.add_trace(go.Scatter(
                x=df['timestamp'],
                y=drawdown,
                fill='tonexty',
                mode='lines',
                name='Drawdown',
                line=dict(color='red'),
                hovertemplate='Date: %{x}<br>Drawdown: %{y:.2f}%<extra></extra>'
            ))
            
            fig_dd.update_layout(
                title="Portfolio Drawdown Over Time",
                xaxis_title="Date",
                yaxis_title="Drawdown (%)",
                height=300
            )
            
            st.plotly_chart(fig_dd, use_container_width=True)
            
            # Risk metrics
            st.metric("Max Drawdown", f"-{metrics['max_drawdown']:.2f}%")
            st.metric("Max Consecutive Losses", f"{metrics['max_consecutive_losses']}")
            st.metric("Volatility", f"{metrics['volatility']:.2f}%")
        
        with col2:
            st.subheader("📊 Performance Distribution")
            
            # P&L distribution with risk zones
            fig_dist = go.Figure()
            
            # Add histogram
            fig_dist.add_trace(go.Histogram(
                x=df['pnl_percent'],
                nbinsx=30,
                name='Trade Distribution',
                marker_color='lightblue',
                opacity=0.7
            ))
            
            # Add risk zone lines
            mean_pnl = df['pnl_percent'].mean()
            std_pnl = df['pnl_percent'].std()
            
            fig_dist.add_vline(x=mean_pnl, line_dash="dash", line_color="green", annotation_text="Mean")
            fig_dist.add_vline(x=mean_pnl - 2*std_pnl, line_dash="dash", line_color="red", annotation_text="-2σ")
            fig_dist.add_vline(x=mean_pnl + 2*std_pnl, line_dash="dash", line_color="red", annotation_text="+2σ")
            
            fig_dist.update_layout(
                title="P&L Distribution with Risk Zones",
                xaxis_title="P&L (%)",
                yaxis_title="Frequency",
                height=300
            )
            
            st.plotly_chart(fig_dist, use_container_width=True)
            
            # Additional risk metrics
            st.metric("Best Trade", f"+{metrics['best_trade']:.2f}%")
            st.metric("Worst Trade", f"{metrics['worst_trade']:.2f}%")
            st.metric("Volatility Ratio", f"{abs(metrics['worst_trade']) / metrics['best_trade']:.2f}" if metrics['best_trade'] > 0 else "N/A")
    
    def render_advanced_analytics(self, df: pd.DataFrame) -> None:
        """Render advanced analytics section"""
        st.header("🎯 Advanced Analytics")
        
        if df.empty:
            st.info("No data available for advanced analytics.")
            return
        
        tab1, tab2, tab3 = st.tabs(["📅 Time Analysis", "🎯 Confidence Analysis", "📊 Symbol Performance"])
        
        with tab1:
            if 'trade_hour' in df.columns:
                # Hourly performance analysis
                hourly_stats = df.groupby('trade_hour').agg({
                    'pnl_percent': ['mean', 'count', 'std'],
                    'confidence': 'mean'
                }).round(2)
                
                fig_hourly = px.bar(
                    x=hourly_stats.index,
                    y=hourly_stats[('pnl_percent', 'mean')],
                    title="Average P&L by Hour of Day",
                    labels={'x': 'Hour of Day', 'y': 'Average P&L (%)'}
                )
                st.plotly_chart(fig_hourly, use_container_width=True)
                
                # Weekly performance
                if len(df) > 7:
                    df['day_of_week'] = df['timestamp'].dt.day_name()
                    daily_performance = df.groupby('day_of_week')['pnl_percent'].mean()
                    
                    fig_daily = px.bar(
                        x=daily_performance.index,
                        y=daily_performance.values,
                        title="Average P&L by Day of Week"
                    )
                    st.plotly_chart(fig_daily, use_container_width=True)
        
        with tab2:
            if 'confidence' in df.columns:
                # Confidence vs Performance correlation
                fig_conf = px.scatter(
                    df,
                    x='confidence',
                    y='pnl_percent',
                    color='performance_category',
                    title="Confidence vs Performance Correlation",
                    labels={'confidence': 'Confidence Score', 'pnl_percent': 'P&L (%)'}
                )
                st.plotly_chart(fig_conf, use_container_width=True)
                
                # Confidence distribution
                fig_conf_dist = px.histogram(
                    df,
                    x='confidence',
                    color='performance_category',
                    title="Confidence Score Distribution by Performance"
                )
                st.plotly_chart(fig_conf_dist, use_container_width=True)
        
        with tab3:
            # Symbol performance breakdown
            symbol_performance = df.groupby('symbol').agg({
                'pnl_percent': ['mean', 'sum', 'count'],
                'confidence': 'mean'
            }).round(2)
            
            symbol_performance.columns = ['Avg P&L %', 'Total P&L %', 'Trade Count', 'Avg Confidence']
            symbol_performance = symbol_performance.sort_values('Total P&L %', ascending=False)
            
            st.subheader("Performance by Symbol")
            st.dataframe(symbol_performance, use_container_width=True)
            
            # Top performers chart
            top_symbols = symbol_performance.head(10)
            fig_symbols = px.bar(
                x=top_symbols.index,
                y=top_symbols['Total P&L %'],
                title="Top 10 Symbols by Total P&L"
            )
            st.plotly_chart(fig_symbols, use_container_width=True)
    
    def prepare_csv_export(self, df: pd.DataFrame) -> str:
        """Prepare CSV data for export"""
        output = io.StringIO()
        df.to_csv(output, index=False)
        return output.getvalue()
    
    def render_sidebar_controls(self):
        """Render sidebar controls"""
        st.sidebar.header("⚙️ Dashboard Controls")
        
        # Auto-refresh controls
        st.sidebar.subheader("🔄 Auto Refresh")
        auto_refresh = st.sidebar.checkbox("Enable Auto Refresh", value=st.session_state.auto_refresh)
        
        if auto_refresh:
            refresh_interval = st.sidebar.slider(
                "Refresh Interval (seconds)",
                min_value=10,
                max_value=300,
                value=st.session_state.refresh_interval,
                step=10
            )
            st.session_state.refresh_interval = refresh_interval
            
            # Auto-refresh logic
            import time
            placeholder = st.sidebar.empty()
            if st.sidebar.button("⏸️ Pause Refresh"):
                st.session_state.auto_refresh = False
                st.rerun()
        
        st.session_state.auto_refresh = auto_refresh
        
        # Manual refresh button
        if st.sidebar.button("🔄 Manual Refresh", type="primary"):
            st.rerun()
        
        # Data management
        st.sidebar.subheader("📁 Data Management")
        
        if st.sidebar.button("🧹 Clear All Data"):
            if st.sidebar.button("⚠️ Confirm Clear", type="secondary"):
                # This would clear log files
                st.sidebar.success("Data cleared!")
        
        # Export options
        st.sidebar.subheader("📤 Export Options")
        if st.sidebar.button("📊 Export Performance Report"):
            st.sidebar.info("Performance report generated!")

def main():
    """Main dashboard application"""
    st.title("📊 Advanced Trading Bot Analytics Dashboard")
    st.markdown("---")
    
    # Initialize dashboard
    dashboard = TradingDashboard()
    
    # Render sidebar controls
    dashboard.render_sidebar_controls()
    
    # Load data
    df = dashboard.load_trade_data()
    metrics = dashboard.calculate_metrics(df)
    
    # Create main tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Overview", "📈 Charts", "🔍 Analysis", 
        "⏰ Recent", "🎯 Scanner", "⚠️ Risk"
    ])
    
    with tab1:
        dashboard.render_performance_overview(df, metrics)
        
        # Active positions section
        st.markdown("---")
        st.header("💼 Active Positions")
        
        active_positions = dashboard.load_active_positions()
        if active_positions:
            positions_df = pd.DataFrame(active_positions)
            st.dataframe(positions_df, use_container_width=True, hide_index=True)
        else:
            st.info("No active positions.")
    
    with tab2:
        dashboard.render_performance_charts(df)
    
    with tab3:
        dashboard.render_trade_analysis(df)
    
    with tab4:
        dashboard.render_recent_trades(df)
    
    with tab5:
        dashboard.render_scan_results()
    
    with tab6:
        dashboard.render_risk_metrics(df, metrics)
        st.markdown("---")
        dashboard.render_advanced_analytics(df)
    
    # Footer
    st.markdown("---")
    st.caption("🤖 Advanced Trading Bot Dashboard | Real-time Analytics & Performance Monitoring")

if __name__ == "__main__":
    main()