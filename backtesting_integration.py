#!/usr/bin/env python3
"""
Backtesting Integration for Bottie App
=====================================

This module integrates your BacktestEngineReal with the main Bottie application,
providing a comprehensive backtesting tab in the dashboard.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import os
import json
import threading
import time
from typing import Dict, List, Any

# Import your existing modules
try:
    from backtest_engine_real import BacktestEngineReal
    from smart_imports import smart_imports
    BACKTESTING_AVAILABLE = True
except ImportError:
    BACKTESTING_AVAILABLE = False

class BacktestingIntegration:
    """Integrates backtesting functionality with the main Bottie app"""
    
    def __init__(self):
        self.results_dir = "backtest_output"
        self.cache_file = "backtest_cache.json"
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Initialize session state for backtesting
        if 'backtest_state' not in st.session_state:
            st.session_state.backtest_state = {
                'running': False,
                'results': None,
                'progress': 0,
                'current_pair': '',
                'optimal_weights': {},
                'performance_history': []
            }
    
    def render_backtesting_tab(self):
        """Main backtesting tab in the Bottie dashboard"""
        
        st.header("🔬 Strategy Backtesting & Optimization")
        
        if not BACKTESTING_AVAILABLE:
            st.error("❌ Backtesting engine not available. Please install required dependencies.")
            return
        
        # Create tabs within backtesting
        bt_tab1, bt_tab2, bt_tab3, bt_tab4 = st.tabs([
            "🚀 Run Backtest",
            "📊 Results Analysis", 
            "⚙️ Optimization",
            "📈 Performance"
        ])
        
        with bt_tab1:
            self.render_backtest_runner()
        
        with bt_tab2:
            self.render_results_analysis()
        
        with bt_tab3:
            self.render_optimization_tools()
        
        with bt_tab4:
            self.render_performance_tracking()
    
    def render_backtest_runner(self):
        """Backtest execution interface"""
        
        st.subheader("🚀 Configure & Run Backtest")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Backtest configuration
            st.markdown("### 📋 Backtest Configuration")
            
            # Trading pairs selection
            pair_option = st.selectbox(
                "Select Trading Pairs",
                ["Quick Test (3 pairs)", "Major Pairs (8 pairs)", "Full Portfolio (15+ pairs)", "Custom Selection"]
            )
            
            if pair_option == "Quick Test (3 pairs)":
                selected_pairs = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
            elif pair_option == "Major Pairs (8 pairs)":
                selected_pairs = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "SOLUSDT", "DOTUSDT", "LINKUSDT", "AVAXUSDT"]
            elif pair_option == "Full Portfolio (15+ pairs)":
                selected_pairs = [
                    "BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "SOLUSDT", "DOTUSDT", "LINKUSDT", "AVAXUSDT",
                    "MATICUSDT", "ATOMUSDT", "NEARUSDT", "LTCUSDT", "UNIUSDT", "AAVEUSDT", "COMPUSDT"
                ]
            else:  # Custom
                custom_pairs = st.text_area(
                    "Enter custom pairs (one per line)",
                    value="BTCUSDT\nETHUSDT\nSOLUSDT",
                    height=100
                )
                selected_pairs = [pair.strip() for pair in custom_pairs.split('\n') if pair.strip()]
            
            st.info(f"Selected {len(selected_pairs)} pairs: {', '.join(selected_pairs[:5])}{' ...' if len(selected_pairs) > 5 else ''}")
            
            # Backtest parameters
            col_param1, col_param2 = st.columns(2)
            
            with col_param1:
                timeframe = st.selectbox("Timeframe", ["1h", "4h", "1d"], index=0)
                capital = st.number_input("Starting Capital (USDT)", min_value=100, value=1000, step=100)
                
            with col_param2:
                lookback_days = st.number_input("Lookback Period (days)", min_value=7, max_value=365, value=30)
                fee_rate = st.number_input("Trading Fee %", min_value=0.0, max_value=1.0, value=0.1, step=0.01) / 100
            
            # Strategy weight testing
            st.markdown("### ⚛️ Strategy Weight Testing")
            
            test_mode = st.radio(
                "Testing Mode",
                ["Quick Test (5 combinations)", "Standard Test (25 combinations)", "Comprehensive (125 combinations)"],
                index=1
            )
            
            if test_mode == "Quick Test (5 combinations)":
                weight_steps = [0, 50, 100]
            elif test_mode == "Standard Test (25 combinations)":
                weight_steps = [0, 25, 50, 75, 100]
            else:  # Comprehensive
                weight_steps = [0, 20, 40, 60, 80, 100]
            
            total_combinations = self.calculate_combinations(weight_steps)
            st.info(f"Will test {total_combinations} weight combinations across {len(selected_pairs)} pairs")
            
        with col2:
            # Backtest status and controls
            st.markdown("### 🎛️ Backtest Control")
            
            if st.session_state.backtest_state['running']:
                st.warning("🔄 Backtest in progress...")
                st.progress(st.session_state.backtest_state['progress'] / 100)
                
                if st.session_state.backtest_state['current_pair']:
                    st.text(f"Testing: {st.session_state.backtest_state['current_pair']}")
                
                if st.button("🛑 Stop Backtest"):
                    st.session_state.backtest_state['running'] = False
                    st.rerun()
            else:
                if st.button("🚀 Start Backtest", type="primary", use_container_width=True):
                    self.start_backtest(selected_pairs, timeframe, capital, fee_rate, weight_steps, lookback_days)
                
                # Quick actions
                st.markdown("---")
                st.markdown("### ⚡ Quick Actions")
                
                if st.button("📈 Load Last Results", use_container_width=True):
                    self.load_last_results()
                
                if st.button("🔄 Demo Backtest", use_container_width=True):
                    self.run_demo_backtest()
    
    def calculate_combinations(self, weight_steps):
        """Calculate total weight combinations"""
        count = 0
        for ml in weight_steps:
            for quantum in weight_steps:
                tech = 100 - (ml + quantum)
                if tech >= 0:
                    count += 1
        return count
    
    def start_backtest(self, pairs, timeframe, capital, fee_rate, weight_steps, lookback_days):
        """Start backtesting process"""
        
        st.session_state.backtest_state['running'] = True
        st.session_state.backtest_state['progress'] = 0
        
        # Run backtest in a separate thread (simplified for demo)
        def run_backtest():
            try:
                engine = BacktestEngineReal(
                    pairs=pairs,
                    timeframe=timeframe,
                    capital=capital,
                    fee_rate=fee_rate
                )
                
                # Override weight steps
                engine.weight_steps = weight_steps
                
                # Run backtest with progress updates
                results = engine.run_backtest()
                
                # Save results
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                results_file = f"{self.results_dir}/backtest_results_{timestamp}.csv"
                results.to_csv(results_file, index=False)
                
                # Update session state
                st.session_state.backtest_state['results'] = results
                st.session_state.backtest_state['running'] = False
                st.session_state.backtest_state['progress'] = 100
                
                # Calculate optimal weights
                optimal_weights = self.calculate_optimal_weights(results)
                st.session_state.backtest_state['optimal_weights'] = optimal_weights
                
            except Exception as e:
                st.session_state.backtest_state['running'] = False
                st.error(f"Backtest failed: {str(e)}")
        
        # For demonstration, we'll use the demo version
        # In production, you'd use: threading.Thread(target=run_backtest).start()
        self.run_demo_backtest()
    
    def run_demo_backtest(self):
        """Run a demo backtest with simulated results"""
        
        # Create demo results similar to your example
        demo_data = {
            "Pair": ["BTCUSDT", "ETHUSDT", "SOLUSDT", "ADAUSDT", "BNBUSDT"] * 5,
            "ML Weight": [20, 40, 60, 80, 40] * 5,
            "Quantum Weight": [60, 40, 20, 0, 40] * 5,
            "Technical Weight": [20, 20, 20, 20, 20] * 5,
            "ROI (USDT)": np.random.uniform(50, 200, 25),
            "Win Rate": np.random.uniform(45, 75, 25),
            "Trades": np.random.randint(20, 60, 25),
            "Max Drawdown (%)": np.random.uniform(10, 30, 25)
        }
        
        results_df = pd.DataFrame(demo_data)
        
        # Add some realistic correlations
        results_df.loc[results_df["ML Weight"] > 60, "Win Rate"] *= 1.1
        results_df.loc[results_df["Quantum Weight"] > 60, "ROI (USDT)"] *= 1.15
        
        st.session_state.backtest_state['results'] = results_df
        st.session_state.backtest_state['running'] = False
        st.session_state.backtest_state['optimal_weights'] = self.calculate_optimal_weights(results_df)
        
        st.success("✅ Demo backtest completed!")
        st.rerun()
    
    def calculate_optimal_weights(self, results_df):
        """Calculate optimal weights from backtest results"""
        
        # Find best performing combination for each pair
        optimal_weights = {}
        
        for pair in results_df['Pair'].unique():
            pair_results = results_df[results_df['Pair'] == pair]
            
            # Score based on ROI and Win Rate (weighted)
            pair_results['Score'] = (
                pair_results['ROI (USDT)'].rank(pct=True) * 0.6 +
                pair_results['Win Rate'].rank(pct=True) * 0.4
            )
            
            best_row = pair_results.loc[pair_results['Score'].idxmax()]
            
            optimal_weights[pair] = {
                'ml_weight': best_row['ML Weight'],
                'quantum_weight': best_row['Quantum Weight'],
                'technical_weight': best_row['Technical Weight'],
                'roi': best_row['ROI (USDT)'],
                'win_rate': best_row['Win Rate'],
                'trades': best_row['Trades'],
                'max_drawdown': best_row['Max Drawdown (%)']
            }
        
        return optimal_weights
    
    def render_results_analysis(self):
        """Display backtest results analysis"""
        
        st.subheader("📊 Backtest Results Analysis")
        
        if st.session_state.backtest_state['results'] is None:
            st.info("📋 No backtest results available. Run a backtest first.")
            return
        
        results_df = st.session_state.backtest_state['results']
        
        # Overall performance summary
        st.markdown("### 📈 Performance Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_roi = results_df['ROI (USDT)'].mean()
            st.metric("Average ROI", f"${avg_roi:.1f}", f"{avg_roi/10:.1f}%")
        
        with col2:
            avg_win_rate = results_df['Win Rate'].mean()
            st.metric("Average Win Rate", f"{avg_win_rate:.1f}%")
        
        with col3:
            total_trades = results_df['Trades'].sum()
            st.metric("Total Trades", f"{total_trades:,}")
        
        with col4:
            max_drawdown = results_df['Max Drawdown (%)'].max()
            st.metric("Max Drawdown", f"{max_drawdown:.1f}%")
        
        # Best performing strategies
        st.markdown("### 🏆 Top Performing Strategies")
        
        # Calculate combined score
        results_df['Combined Score'] = (
            results_df['ROI (USDT)'].rank(pct=True) * 0.4 +
            results_df['Win Rate'].rank(pct=True) * 0.3 +
            (100 - results_df['Max Drawdown (%)']).rank(pct=True) * 0.3
        )
        
        top_strategies = results_df.nlargest(10, 'Combined Score')[
            ['Pair', 'ML Weight', 'Quantum Weight', 'Technical Weight', 'ROI (USDT)', 'Win Rate', 'Max Drawdown (%)']
        ]
        
        st.dataframe(top_strategies, use_container_width=True, hide_index=True)
        
        # Performance visualization
        st.markdown("### 📊 Performance Visualization")
        
        # ROI vs Win Rate scatter plot
        fig_scatter = px.scatter(
            results_df,
            x='Win Rate',
            y='ROI (USDT)',
            color='Pair',
            size='Trades',
            hover_data=['ML Weight', 'Quantum Weight', 'Technical Weight'],
            title="ROI vs Win Rate by Trading Pair"
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        # Weight distribution analysis
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            # ML Weight vs Performance
            fig_ml = px.box(
                results_df,
                x='ML Weight',
                y='ROI (USDT)',
                title="ML Weight Impact on ROI"
            )
            st.plotly_chart(fig_ml, use_container_width=True)
        
        with col_chart2:
            # Quantum Weight vs Performance
            fig_quantum = px.box(
                results_df,
                x='Quantum Weight',
                y='Win Rate',
                title="Quantum Weight Impact on Win Rate"
            )
            st.plotly_chart(fig_quantum, use_container_width=True)
    
    def render_optimization_tools(self):
        """Strategy optimization tools"""
        
        st.subheader("⚙️ Strategy Optimization")
        
        if st.session_state.backtest_state['optimal_weights']:
            st.markdown("### 🎯 Optimal Weight Recommendations")
            
            optimal_weights = st.session_state.backtest_state['optimal_weights']
            
            # Display optimal weights for each pair
            for pair, weights in optimal_weights.items():
                with st.expander(f"📈 {pair} - Optimal Configuration"):
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("ML Weight", f"{weights['ml_weight']}%")
                        st.metric("Expected ROI", f"${weights['roi']:.1f}")
                    
                    with col2:
                        st.metric("Quantum Weight", f"{weights['quantum_weight']}%")
                        st.metric("Win Rate", f"{weights['win_rate']:.1f}%")
                    
                    with col3:
                        st.metric("Technical Weight", f"{weights['technical_weight']}%")
                        st.metric("Max Drawdown", f"{weights['max_drawdown']:.1f}%")
                    
                    # Configuration for live trading
                    st.markdown("**Live Trading Configuration:**")
                    st.code(f"""
# Add to your .env file or Railway variables:
{pair.replace('USDT', '')}_ML_WEIGHT={weights['ml_weight']}
{pair.replace('USDT', '')}_QUANTUM_WEIGHT={weights['quantum_weight']}
{pair.replace('USDT', '')}_TECHNICAL_WEIGHT={weights['technical_weight']}
                    """)
        
        # Portfolio optimization
        st.markdown("### 📊 Portfolio Optimization")
        
        if st.button("🔄 Generate Portfolio Config"):
            self.generate_portfolio_config()
    
    def generate_portfolio_config(self):
        """Generate optimized portfolio configuration"""
        
        if not st.session_state.backtest_state['optimal_weights']:
            st.warning("No optimization data available. Run a backtest first.")
            return
        
        optimal_weights = st.session_state.backtest_state['optimal_weights']
        
        # Calculate portfolio-level recommendations
        portfolio_config = {
            "trading_pairs": [],
            "risk_allocation": {},
            "weight_config": {},
            "expected_performance": {}
        }
        
        total_expected_roi = 0
        total_pairs = len(optimal_weights)
        
        for pair, weights in optimal_weights.items():
            # Risk-adjusted allocation based on max drawdown
            risk_factor = 1 / (1 + weights['max_drawdown'] / 100)
            allocation = risk_factor / total_pairs
            
            portfolio_config["trading_pairs"].append(pair)
            portfolio_config["risk_allocation"][pair] = f"{allocation * 100:.1f}%"
            portfolio_config["weight_config"][pair] = {
                "ml": weights['ml_weight'],
                "quantum": weights['quantum_weight'], 
                "technical": weights['technical_weight']
            }
            
            total_expected_roi += weights['roi'] * allocation
        
        portfolio_config["expected_performance"] = {
            "portfolio_roi": f"${total_expected_roi:.1f}",
            "avg_win_rate": f"{np.mean([w['win_rate'] for w in optimal_weights.values()]):.1f}%",
            "max_risk": f"{max([w['max_drawdown'] for w in optimal_weights.values()]):.1f}%"
        }
        
        st.success("✅ Portfolio configuration generated!")
        st.json(portfolio_config)
        
        # Export configuration
        if st.button("💾 Export Configuration"):
            config_file = f"{self.results_dir}/portfolio_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(config_file, 'w') as f:
                json.dump(portfolio_config, f, indent=2)
            st.success(f"Configuration saved to: {config_file}")
    
    def render_performance_tracking(self):
        """Performance tracking and monitoring"""
        
        st.subheader("📈 Performance Tracking")
        
        # Live vs Backtest comparison
        st.markdown("### 🔄 Live vs Backtest Performance")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Backtest Performance**")
            if st.session_state.backtest_state['results'] is not None:
                results_df = st.session_state.backtest_state['results']
                bt_avg_roi = results_df['ROI (USDT)'].mean()
                bt_avg_win_rate = results_df['Win Rate'].mean()
                
                st.metric("Avg ROI", f"${bt_avg_roi:.1f}")
                st.metric("Avg Win Rate", f"{bt_avg_win_rate:.1f}%")
            else:
                st.info("No backtest data available")
        
        with col2:
            st.markdown("**Live Performance**")
            # This would connect to your actual trading logs
            # For demo, using simulated values
            live_roi = 85.3
            live_win_rate = 62.1
            
            st.metric("Current ROI", f"${live_roi:.1f}", f"{live_roi - 90:.1f}")
            st.metric("Live Win Rate", f"{live_win_rate:.1f}%", f"{live_win_rate - 60:.1f}%")
        
        # Performance history chart
        st.markdown("### 📊 Performance History")
        
        # Generate sample performance data
        dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
        backtest_performance = np.random.normal(1.02, 0.05, len(dates)).cumprod() * 1000
        live_performance = np.random.normal(1.018, 0.08, len(dates)).cumprod() * 1000
        
        performance_df = pd.DataFrame({
            'Date': dates,
            'Backtest': backtest_performance,
            'Live Trading': live_performance
        })
        
        fig_performance = go.Figure()
        
        fig_performance.add_trace(go.Scatter(
            x=performance_df['Date'],
            y=performance_df['Backtest'],
            mode='lines',
            name='Backtest Expected',
            line=dict(color='blue', dash='dash')
        ))
        
        fig_performance.add_trace(go.Scatter(
            x=performance_df['Date'],
            y=performance_df['Live Trading'],
            mode='lines',
            name='Live Performance',
            line=dict(color='green')
        ))
        
        fig_performance.update_layout(
            title="Backtest vs Live Performance Comparison",
            xaxis_title="Date",
            yaxis_title="Portfolio Value (USDT)",
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_performance, use_container_width=True)
        
        # Strategy performance alerts
        st.markdown("### 🚨 Performance Alerts")
        
        # Check for significant deviations
        if abs(live_roi - bt_avg_roi) > 20:
            st.warning(f"⚠️ Live performance deviating from backtest by ${abs(live_roi - bt_avg_roi):.1f}")
        
        if live_win_rate < bt_avg_win_rate - 10:
            st.error(f"🔴 Live win rate ({live_win_rate:.1f}%) significantly below backtest ({bt_avg_win_rate:.1f}%)")
        elif live_win_rate > bt_avg_win_rate + 5:
            st.success(f"🟢 Live win rate ({live_win_rate:.1f}%) exceeding backtest expectations!")
    
    def load_last_results(self):
        """Load the most recent backtest results"""
        
        try:
            # Find the most recent results file
            result_files = [f for f in os.listdir(self.results_dir) if f.startswith('backtest_results_')]
            
            if result_files:
                latest_file = max(result_files, key=lambda x: os.path.getctime(os.path.join(self.results_dir, x)))
                results_df = pd.read_csv(os.path.join(self.results_dir, latest_file))
                
                st.session_state.backtest_state['results'] = results_df
                st.session_state.backtest_state['optimal_weights'] = self.calculate_optimal_weights(results_df)
                
                st.success(f"✅ Loaded results from: {latest_file}")
                st.rerun()
            else:
                st.warning("No previous backtest results found.")
                
        except Exception as e:
            st.error(f"Failed to load results: {str(e)}")

# Integration function for your main app
def add_backtesting_to_app():
    """
    Add this function to your main hybrid_bot.py to integrate backtesting
    
    Usage in hybrid_bot.py:
    
    # Add this import at the top
    from backtesting_integration import BacktestingIntegration
    
    # Add this tab to your main tabs
    tabs = st.tabs(["🏠 Dashboard", "✋ Manual Trading", "⚛️ Quantum", 
                   "📈 Portfolio", "📊 Performance", "🔬 Backtesting"])
    
    # Add this in the backtesting tab
    with tabs[5]:
        backtesting = BacktestingIntegration()
        backtesting.render_backtesting_tab()
    """
    pass

# Example usage for testing
if __name__ == "__main__":
    st.set_page_config(page_title="Backtesting Integration Demo", layout="wide")
    
    backtesting = BacktestingIntegration()
    backtesting.render_backtesting_tab()