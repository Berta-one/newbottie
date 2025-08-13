#!/usr/bin/env python3
"""
Test script to diagnose the reported issues:
1. Trades stopping at 12:00
2. ML Tab boxes empty with "insufficient data"
3. Sentiment analysis disabled in main menu
"""

import requests
import json
from datetime import datetime, timedelta
import sys

BASE_URL = "http://localhost:8000"

def test_endpoint(endpoint, description):
    """Test an endpoint and return the response"""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"Endpoint: {endpoint}")
    print(f"{'='*60}")
    
    try:
        response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            return data
        else:
            print(f"Error: {response.text}")
            return None
    except Exception as e:
        print(f"Request failed: {e}")
        return None

def analyze_trades_timing():
    """Check if trades are stopping at 12:00"""
    print(f"\n{'*'*80}")
    print("ISSUE 1: TRADES TIMING ANALYSIS")
    print(f"{'*'*80}")
    
    # Check current trades
    trades_data = test_endpoint("/trades", "Current Trades")
    if trades_data:
        trades = trades_data.get("trades", [])
        if trades:
            print(f"\nFound {len(trades)} trades")
            
            # Analyze timing patterns
            current_time = datetime.now()
            today_noon = current_time.replace(hour=12, minute=0, second=0, microsecond=0)
            
            recent_trades = []
            for trade in trades[-10:]:  # Last 10 trades
                timestamp = trade.get("timestamp", 0)
                if timestamp:
                    trade_time = datetime.fromtimestamp(timestamp)
                    recent_trades.append({
                        "time": trade_time.strftime("%Y-%m-%d %H:%M:%S"),
                        "symbol": trade.get("symbol", "unknown"),
                        "side": trade.get("side", "unknown")
                    })
            
            print(f"\nRecent trades:")
            for trade in recent_trades:
                print(f"  {trade['time']} - {trade['symbol']} - {trade['side']}")
                
            # Check if last trade was before noon today
            if recent_trades:
                last_trade_time = datetime.strptime(recent_trades[-1]["time"], "%Y-%m-%d %H:%M:%S")
                print(f"\nLast trade: {last_trade_time}")
                print(f"Today noon: {today_noon}")
                
                if last_trade_time < today_noon and last_trade_time.date() == current_time.date():
                    print("⚠️  WARNING: Last trade was before noon today - trading may have stopped!")
                else:
                    print("✅ Trades appear to be continuing after noon")
        else:
            print("⚠️  No trades found")
    
    # Check execution status
    status_data = test_endpoint("/status", "System Status")
    if status_data:
        exec_enabled = status_data.get("execution_enabled", False)
        print(f"\nExecution enabled: {exec_enabled}")
        if not exec_enabled:
            print("⚠️  WARNING: Execution is disabled!")

def analyze_ml_data():
    """Check ML data availability"""
    print(f"\n{'*'*80}")
    print("ISSUE 2: ML DATA ANALYSIS")
    print(f"{'*'*80}")
    
    # Check ML status
    ml_status = test_endpoint("/ml/status", "ML Status")
    if ml_status:
        samples = ml_status.get("samples", 0)
        print(f"ML Samples: {samples}")
        if samples == 0:
            print("⚠️  WARNING: No ML samples - this explains 'insufficient data'")
    
    # Check ML performance
    ml_performance = test_endpoint("/ml/performance", "ML Performance")
    if ml_performance:
        timeframes = ml_performance.get("timeframes", {})
        print(f"Available timeframes: {list(timeframes.keys())}")
        
        for tf, data in timeframes.items():
            samples = len(data.get("accuracy", []))
            print(f"  {tf}: {samples} data points")
            if samples == 0:
                print(f"    ⚠️  No data for {tf}")
    
    # Check signals for ML component
    signals_data = test_endpoint("/signals", "Signals")
    if signals_data:
        signals = signals_data.get("signals", [])
        if signals:
            ml_signals = [s for s in signals if s.get("ml") is not None]
            print(f"\nSignals with ML component: {len(ml_signals)}/{len(signals)}")
            if len(ml_signals) == 0:
                print("⚠️  WARNING: No signals have ML predictions")

def analyze_sentiment_status():
    """Check sentiment analysis status"""
    print(f"\n{'*'*80}")
    print("ISSUE 3: SENTIMENT ANALYSIS STATUS")
    print(f"{'*'*80}")
    
    # Check health endpoint for sentiment status
    health_data = test_endpoint("/health", "Health Check")
    if health_data:
        sentiment_status = health_data.get("sentiment", {})
        enabled = sentiment_status.get("enabled", False)
        print(f"Sentiment enabled in health: {enabled}")
        
        quantum_status = health_data.get("quantum", {})
        quantum_enabled = quantum_status.get("enabled", False)
        print(f"Quantum enabled in health: {quantum_enabled}")
    
    # Check sentiment endpoint
    sentiment_data = test_endpoint("/sentiment", "Sentiment Data")
    if sentiment_data:
        snapshot = sentiment_data.get("snapshot", {})
        print(f"Sentiment snapshot keys: {list(snapshot.keys())}")
    
    # Check sentiment articles
    articles_data = test_endpoint("/sentiment/articles", "Sentiment Articles")
    if articles_data:
        articles = articles_data.get("articles", [])
        print(f"Available articles: {len(articles)}")
        if len(articles) == 0:
            print("⚠️  WARNING: No sentiment articles available")
        else:
            for i, article in enumerate(articles[:3]):  # Show first 3
                print(f"  Article {i+1}: {article.get('headline', 'No headline')[:50]}...")
    
    # Check if sentiment appears in signals
    signals_data = test_endpoint("/signals", "Signals for Sentiment")
    if signals_data:
        signals = signals_data.get("signals", [])
        if signals:
            sentiment_signals = [s for s in signals if s.get("sent") is not None]
            print(f"\nSignals with sentiment component: {len(sentiment_signals)}/{len(signals)}")
            if len(sentiment_signals) == 0:
                print("⚠️  WARNING: No signals have sentiment predictions")

def main():
    print("🔍 BOTTIE SYSTEM DIAGNOSTICS")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Testing server at: {BASE_URL}")
    
    # Test basic connectivity
    health_data = test_endpoint("/health", "Basic Health Check")
    if not health_data:
        print("❌ Cannot connect to server!")
        sys.exit(1)
    
    print("✅ Server is responsive")
    
    # Run specific issue analyses
    analyze_trades_timing()
    analyze_ml_data()
    analyze_sentiment_status()
    
    print(f"\n{'='*80}")
    print("SUMMARY OF FINDINGS")
    print(f"{'='*80}")
    print("Check the warnings (⚠️) above for specific issues to address.")

if __name__ == "__main__":
    main()
