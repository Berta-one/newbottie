#!/usr/bin/env python3
"""
Complete Enhanced Crypto Trading Bot Dashboard
===========================================

Company: Rondanini Publishing Ltd.  
Website: https://www.rondanini.net

Copyright (c) 2025 Rondanini Publishing Ltd.

Usage:
    streamlit run hybrid_bot.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import os
import time
import threading
import subprocess
import sys
import signal
import requests
import random
import csv

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from binance.client import Client
    from binance.exceptions import BinanceAPIException
    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False

try:
    from quantum_engine import QuantumTradingEngine
    from quantum_trading_integration import get_quantum_trader
    QUANTUM_AVAILABLE = True
except ImportError:
    QUANTUM_AVAILABLE = False
    class QuantumTradingEngine:
        def __init__(self): pass
        def generate_quantum_trading_recommendation(self, *args, **kwargs):
            return {'quantum_signal': 'UNAVAILABLE', 'quantum_confidence': 0}

API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')
SCAN_INTERVAL = int(os.getenv('SCAN_INTERVAL', '300').split('#')[0].strip())
MIN_BALANCE_USD = float(os.getenv('MIN_BALANCE_USD', '10.0'))

TRADING_STRATEGIES = {
    'Scalping': {
        'description': 'Quick trades on 2-3% moves with high volume',
        'threshold': 2.0,
        'volume_req': 1.5,
        'hold_time': '30 minutes',
        'take_profit': '3-5%',
        'stop_loss': '2-3%',
        'confidence_min': 0.65
    },
    'Breakout': {
        'description': 'Trade 5% price breakouts with volume confirmation',
        'threshold': 5.0,
        'volume_req': 2.0,
        'hold_time': '2-4 hours',
        'take_profit': '8-15%',
        'stop_loss': '8-12%',
        'confidence_min': 0.70
    },
    'Swing': {
        'description': 'Capture 10-20% moves over longer periods',
        'threshold': 8.0,
        'volume_req': 1.2,
        'hold_time': '4-24 hours',
        'take_profit': '15-25%',
        'stop_loss': '10-15%',
        'confidence_min': 0.60
    },
    'Conservative': {
        'description': 'Safe trading with reduced risk and smaller positions',
        'threshold': 3.0,
        'volume_req': 1.8,
        'hold_time': '1-2 hours',
        'take_profit': '5-8%',
        'stop_loss': '3-5%',
        'confidence_min': 0.75
    }
}

RISK_LEVELS = {
    'Conservative': {
        'position_size_multiplier': 0.7,
        'max_positions': 2,
        'risk_per_trade': 0.01,
        'description': 'Lower risk, smaller positions'
    },
    'Balanced': {
        'position_size_multiplier': 1.0,
        'max_positions': 3,
        'risk_per_trade': 0.015,
        'description': 'Moderate risk, balanced approach'
    },
    'Aggressive': {
        'position_size_multiplier': 1.3,
        'max_positions': 5,
        'risk_per_trade': 0.025,
        'description': 'Higher risk, larger positions'
    }
}

def initialize_session_state():
    """Initialize all session state variables"""
    if 'dashboard_password' not in st.session_state:
        st.session_state['dashboard_password'] = os.getenv('DASHBOARD_PASSWORD', 'bottie')
    if 'password_authenticated' not in st.session_state:
        st.session_state['password_authenticated'] = False

    if 'background_bot_running' not in st.session_state:
        st.session_state['background_bot_running'] = False
    if 'bot_process' not in st.session_state:
        st.session_state['bot_process'] = None
    if 'bot_mode' not in st.session_state:
        st.session_state['bot_mode'] = 'Demo'
    if 'bot_running' not in st.session_state:
        st.session_state['bot_running'] = False

    if 'quantum_engine' not in st.session_state:
        st.session_state['quantum_engine'] = QuantumTradingEngine()

    if 'quantum_trader' not in st.session_state and QUANTUM_AVAILABLE:
        client = None
        if BINANCE_AVAILABLE and API_KEY and API_SECRET:
            try:
                client = Client(API_KEY, API_SECRET)
                if get_use_testnet():
                    client.API_URL = "https://testnet.binance.vision/api"
            except Exception as e:
                st.error(f"Failed to initialize Binance client: {e}")
        st.session_state['quantum_trader'] = get_quantum_trader(client) if QUANTUM_AVAILABLE else None

    if 'selected_strategy' not in st.session_state:
        st.session_state['selected_strategy'] = 'Breakout'
    if 'selected_risk_level' not in st.session_state:
        st.session_state['selected_risk_level'] = 'Balanced'
    if 'max_trade_percent' not in st.session_state:
        st.session_state['max_trade_percent'] = 10.0

    if 'scan_count' not in st.session_state:
        st.session_state['scan_count'] = 0
    if 'last_scan_time' not in st.session_state:
        st.session_state['last_scan_time'] = None
    if 'last_opportunities' not in st.session_state:
        st.session_state['last_opportunities'] = []

def main():
    """Main application entry point"""
    st.set_page_config(
        page_title="🤖 Crypto Trading Bot Dashboard",
        page_icon="🤖",
        layout="wide"
    )

    initialize_session_state()
    ensure_log_files()

    if not st.session_state['password_authenticated']:
        st.title("🔒 Enter Dashboard Password")
        password_input = st.text_input("Password", type="password")
        login_btn = st.button("🔓 Login", key="dashboard_login_btn")

        if login_btn:
            if password_input == st.session_state['dashboard_password']:
                st.session_state['password_authenticated'] = True
                st.success("✅ Access granted!")
                st.rerun()
            else:
                st.error("❌ Incorrect password")
                st.stop()
        else:
            st.stop()

    if 'background_bot_running' not in st.session_state or not st.session_state['background_bot_running']:
        start_background_bot()

    st.title("🤖 Crypto Trading Bot Dashboard")
    st.caption("Professional cryptocurrency trading with advanced market analysis and risk management")
    st.markdown("---")

    dashboard()

if __name__ == "__main__":
    main()
