# dashboard.py - Complete Streamlit Dashboard
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import os
from datetime import datetime, timedelta
import numpy as np

# Configure Streamlit page
st.set_page_config(
    page_title="Crypto Trading Bot Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

class TradingDashboard:
    def __init__(self):
        self.logs_dir = 'logs'
        self.trade_log_file = os.path.join(self.logs_dir, 'multi_pair_trades.json')
        self.single_pair_log = os.path.join(self.logs_dir, 'single_pair_performance.json')
        self.performance_file = os.path.join(self.logs_dir, 'performance.json')
        
    def load_trade_data(self):
        """Load trade data from JSON files"""
        trade_data = []
        
        # Load multi-pair trades
        if os.path.exists(self.trade_log_file):
            try:
                with open(self.trade_log_file, 'r') as f:
                    multi_data = json.load(f)
                    if isinstance(multi_data, list):
                        trade_data.extend(multi_data)
            except Exception as e:
                st.error(f"Error loading multi-pair trades: {e}")
        
        # Load single-pair trades
        if os.path.exists(self.single_pair_log):
            try:
                with open(self.single_pair_log, 'r') as f:
                    single_data = json.load(f)
                    if isinstance(single_data, list):
                        trade_data.extend(single_data)
            except Exception as e:
                st.error(f"Error loading single-pair trades: {e}")
        
        if trade_data:
            df = pd.DataFrame(trade_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            return df
        
        return pd.DataFrame()
    
    def load_scan_results(self):
        """Load latest scan results"""
        scan_files = []
        if os.path.exists(self.logs_dir):
            for file in os.listdir(self.logs_dir):
                if file.startswith('scan_results_') and file.endswith('.json'):
                    scan_files.append(os.path.join(self.logs_dir, file))
        
        if scan_files:
            # Get most recent scan file
            latest_scan = max(scan_files, key=os.path.getctime)
            try:
                with open(latest_scan, 'r') as f:
                    return json.load(f)
            except:
                return None
        return None
    
    def calculate_metrics(self, df):
        """Calculate comprehensive trading metrics"""
        if df.empty:
            return {}
        
        # Basic metrics
        total_trades = len(df)
        winning_trades = len(df[df['pnl_percent'] > 0])
        losing_trades = len(df[df['pnl_percent'] < 0])
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        
        # P&L metrics
        total_pnl = df['pnl_percent'].sum()
        avg_win = df[df['pnl_percent'] > 0]['pnl_percent'].mean() if winning_trades > 0 else 0
        avg_loss = df[df['pnl_percent'] < 0]['pnl_percent'].mean() if losing_trades > 0 else 0
        
        # Risk metrics
        max_win = df['pnl_percent'].max()
        max_loss = df['pnl_percent'].min()
        volatility = df['pnl_percent'].std()
        
        # Profit factor
        total_wins = df[df['pnl_percent'] > 0]['pnl_percent'].sum()
        total_losses = abs(df[df['pnl_percent'] < 0]['pnl_percent'].sum())
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
        
        # Sharpe ratio (simplified)
        sharpe_ratio = total_pnl / volatility if volatility > 0 else 0
        
        # Maximum drawdown
        df['cumulative_pnl'] = df['pnl_percent'].cumsum()
        running_max = df['cumulative_pnl'].cummax()
        drawdown = (df['cumulative_pnl'] - running_max)
        max_drawdown = drawdown.min() if not drawdown.empty else 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'max_win': max_win,
            'max_loss': max_loss,
            'profit_factor': profit_factor,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'volatility': volatility
        }
    
    def render_header(self):
        """Render dashboard header"""
        st.title("🤖 Crypto Trading Bot Dashboard")
        st.markdown("---")
        
        # Status indicators
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if os.path.exists(self.trade_log_file):
                st.success("🟢 Multi-Pair Bot Active")
            else:
                st.warning("🟡 Multi-Pair Bot Inactive")
        
        with col2:
            if os.path.exists(self.single_pair_log):
                st.success("🟢 Single-Pair Bot Data")
            else:
                st.info("🔵 No Single-Pair Data")
        
        with col3:
            scan_data = self.load_scan_results()
            if scan_data:
                scan_time = datetime.fromisoformat(scan_data['scan_timestamp'])
                time_diff = datetime.now() - scan_time
                if time_diff.total_seconds() < 600:  # 10 minutes
                    st.success("🟢 Recent Scan Data")
                else:
                    st.warning("🟡 Scan Data Outdated")
            else:
                st.error("🔴 No Scan Data")
        
        with col4:
            st.info(f"🕐 Last Updated: {datetime.now().strftime('%H:%M:%S')}")
    
    def render_performance_overview(self, df, metrics):
        """Render performance overview section"""
        st.header("📊 Performance Overview")
        
        if df.empty:
            st.warning("No trading data available yet.")
            return
        
        # Key metrics row
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                "Total Trades",
                metrics['total_trades'],
                delta=None
            )
        
        with col2:
            st.metric(
                "Win Rate",
                f"{metrics['win_rate']:.1f}%",
                delta=f"{metrics['winning_trades']} wins"
            )
        
        with col3:
            st.metric(
                "Total P&L",
                f"{metrics['total_pnl']:+.2f}%",
                delta=f"Avg: {metrics['total_pnl']/metrics['total_trades']:.2f}%" if metrics['total_trades'] > 0 else None
            )
        
        with col4:
            st.metric(
                "Profit Factor",
                f"{metrics['profit_factor']:.2f}",
                delta="Excellent" if metrics['profit_factor'] > 2 else "Good" if metrics['profit_factor'] > 1.5 else "Needs Work"
            )
        
        with col5:
            st.metric(
                "Max Drawdown",
                f"{metrics['max_drawdown']:.2f}%",
                delta="Low Risk" if metrics['max_drawdown'] > -5 else "Moderate" if metrics['max_drawdown'] > -10 else "High Risk"
            )
        
        # Performance charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Cumulative P&L chart
            df['cumulative_pnl'] = df['pnl_percent'].cumsum()
            fig_pnl = px.line(
                df, 
                x='timestamp', 
                y='cumulative_pnl',
                title='Cumulative P&L Over Time',
                labels={'cumulative_pnl': 'Cumulative P&L (%)', 'timestamp': 'Date'}
            )
            fig_pnl.update_layout(height=400)
            st.plotly_chart(fig_pnl, use_container_width=True)
        
        with col2:
            # P&L distribution
            fig_dist = px.histogram(
                df,
                x='pnl_percent',
                nbins=20,
                title='P&L Distribution',
                labels={'pnl_percent': 'P&L (%)', 'count': 'Number of Trades'}
            )
            fig_dist.add_vline(x=0, line_dash="dash", line_color="red")
            fig_dist.update_layout(height=400)
            st.plotly_chart(fig_dist, use_container_width=True)
    def render_trade_analysis(self, df):
        """Render detailed trade analysis"""
        st.header("📈 Trade Analysis")
        
        if df.empty:
            st.warning("No trade data available for analysis.")
            return
        
        # Time period selector
        col1, col2 = st.columns([1, 3])
        with col1:
            time_filter = st.selectbox(
                "Time Period",
                ["All Time", "Last 30 Days", "Last 7 Days", "Last 24 Hours"]
            )
        
        # Filter data based on selection
        if time_filter != "All Time":
            days_map = {"Last 30 Days": 30, "Last 7 Days": 7, "Last 24 Hours": 1}
            cutoff_date = datetime.now() - timedelta(days=days_map[time_filter])
            filtered_df = df[df['timestamp'] >= cutoff_date]
        else:
            filtered_df = df
        
        if filtered_df.empty:
            st.warning(f"No trades found for {time_filter}")
            return
        
        # Category performance
        if 'category' in filtered_df.columns:
            st.subheader("📊 Performance by Category")
            
            category_stats = filtered_df.groupby('category').agg({
                'pnl_percent': ['count', 'mean', 'sum'],
                'symbol': 'count'
            }).round(2)
            
            category_stats.columns = ['Trades', 'Avg P&L (%)', 'Total P&L (%)', 'Symbols']
            category_stats['Win Rate (%)'] = filtered_df.groupby('category').apply(
                lambda x: (x['pnl_percent'] > 0).sum() / len(x) * 100
            ).round(1)
            
            st.dataframe(category_stats, use_container_width=True)
            
            # Category performance chart
            fig_cat = px.bar(
                category_stats.reset_index(),
                x='category',
                y='Total P&L (%)',
                title='Total P&L by Category',
                color='Total P&L (%)',
                color_continuous_scale='RdYlGn'
            )
            st.plotly_chart(fig_cat, use_container_width=True)
        
        # Symbol performance
        st.subheader("💰 Top Performing Symbols")
        
        symbol_stats = filtered_df.groupby('symbol').agg({
            'pnl_percent': ['count', 'mean', 'sum']
        }).round(2)
        symbol_stats.columns = ['Trades', 'Avg P&L (%)', 'Total P&L (%)']
        symbol_stats = symbol_stats.sort_values('Total P&L (%)', ascending=False)
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Best Performers**")
            st.dataframe(symbol_stats.head(10), use_container_width=True)
        
        with col2:
            st.write("**Worst Performers**")
            st.dataframe(symbol_stats.tail(10), use_container_width=True)
    
    def render_recent_trades(self, df):
        """Render recent trades table"""
        st.header("📋 Recent Trades")
        
        if df.empty:
            st.warning("No recent trades to display.")
            return
        
        # Show last 20 trades
        recent_trades = df.tail(20).copy()
        recent_trades = recent_trades.sort_values('timestamp', ascending=False)
        
        # Format the dataframe for display
        display_df = recent_trades[['timestamp', 'symbol', 'pnl_percent', 'reason', 'confidence']].copy()
        display_df['timestamp'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
        display_df['pnl_percent'] = display_df['pnl_percent'].round(2)
        display_df['confidence'] = display_df['confidence'].round(2)
        
        # Color code P&L
        def color_pnl(val):
            color = 'green' if val > 0 else 'red' if val < 0 else 'black'
            return f'color: {color}'
        
        styled_df = display_df.style.applymap(color_pnl, subset=['pnl_percent'])
        st.dataframe(styled_df, use_container_width=True)
    
    def render_scan_results(self):
        """Render latest scan results"""
        st.header("🔍 Latest Scan Results")
        
        scan_data = self.load_scan_results()
        
        if not scan_data:
            st.warning("No scan results available.")
            return
        
        # Scan overview
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Scan Time", scan_data.get('scan_timestamp', 'Unknown'))
        
        with col2:
            st.metric("Total Opportunities", scan_data.get('total_opportunities', 0))
        
        with col3:
            st.metric("Trading Opportunities", scan_data.get('trading_opportunities', 0))
        
        with col4:
            scan_time = datetime.fromisoformat(scan_data['scan_timestamp'])
            time_ago = datetime.now() - scan_time
            st.metric("Time Ago", f"{int(time_ago.total_seconds() / 60)} min")
        
        # Opportunities table
        if 'opportunities' in scan_data and scan_data['opportunities']:
            opportunities_df = pd.DataFrame(scan_data['opportunities'])
            
            # Filter for trading signals
            trading_opps = opportunities_df[opportunities_df['decision'].isin(['BUY_LONG', 'BUY_SHORT'])]
            
            if not trading_opps.empty:
                st.subheader("🎯 Current Trading Opportunities")
                
                display_cols = ['symbol', 'current_price', 'decision', 'confidence', 'price_change_2h', 'category']
                display_opps = trading_opps[display_cols].copy()
                display_opps['current_price'] = display_opps['current_price'].round(4)
                display_opps['confidence'] = display_opps['confidence'].round(2)
                display_opps['price_change_2h'] = display_opps['price_change_2h'].round(2)
                
                # Sort by confidence
                display_opps = display_opps.sort_values('confidence', ascending=False)
                
                st.dataframe(display_opps, use_container_width=True)
            else:
                st.info("No trading opportunities found in latest scan.")

def main():
    """Main dashboard function"""
    dashboard = TradingDashboard()
    
    # Render sidebar
    st.sidebar.header("🎛️ Dashboard Controls")
    
    # Auto-refresh toggle
    auto_refresh = st.sidebar.checkbox("Auto Refresh (30s)", value=False)
    
    if auto_refresh:
        st.rerun()
    
    # Manual refresh button
    if st.sidebar.button("🔄 Refresh Data"):
        st.rerun()
    
    # Render main dashboard
    dashboard.render_header()
    
    # Load data
    df = dashboard.load_trade_data()
    metrics = dashboard.calculate_metrics(df)
    
    # Create tabs for different sections
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Overview", 
        "📈 Analysis", 
        "📋 Recent Trades", 
        "🔍 Scan Results"
    ])
    
    with tab1:
        dashboard.render_performance_overview(df, metrics)
    
    with tab2:
        dashboard.render_trade_analysis(df)
    
    with tab3:
        dashboard.render_recent_trades(df)
    
    with tab4:
        dashboard.render_scan_results()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "🤖 **Crypto Trading Bot Dashboard** | "
        f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
        "⚠️ Trading involves risk - only trade what you can afford to lose"
    )

if __name__ == "__main__":
    main()
