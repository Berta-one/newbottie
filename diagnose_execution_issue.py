#!/usr/bin/env python3
"""
Diagnose why bot is not executing trades despite having signals
"""

import requests
import json

def diagnose_execution_issues(bot_url):
    """Diagnose execution issues"""
    print("🔍 DIAGNOSING EXECUTION ISSUES")
    print("=" * 50)
    
    try:
        # Get signals
        signals_resp = requests.get(f"{bot_url}/signals")
        signals_data = signals_resp.json()
        
        # Get trading status
        trading_resp = requests.get(f"{bot_url}/trading/status")
        trading_data = trading_resp.json()
        
        # Get positions
        positions_resp = requests.get(f"{bot_url}/positions")
        positions_data = positions_resp.json()
        
        # Get trades
        trades_resp = requests.get(f"{bot_url}/trades")
        trades_data = trades_resp.json()
        
        print("📊 EXECUTION ANALYSIS:")
        
        # Check signals
        signals = signals_data.get('signals', [])
        executable_signals = [s for s in signals if s.get('executable', False)]
        
        print(f"   📡 Total Signals: {len(signals)}")
        print(f"   ⚡ Executable Signals: {len(executable_signals)}")
        
        if executable_signals:
            print("   🎯 Ready to Execute:")
            for signal in executable_signals[:5]:  # Show first 5
                symbol = signal.get('symbol', 'Unknown')
                signal_type = signal.get('signal', 'UNKNOWN')
                conf = signal.get('conf', 0)
                print(f"      {symbol}: {signal_type} ({conf:.1%} confidence)")
        
        # Check trading configuration
        print(f"\n⚙️ TRADING CONFIGURATION:")
        print(f"   Trading Enabled: {trading_data.get('trading_enabled', 'Unknown')}")
        print(f"   Mode: {trading_data.get('mode', 'Unknown')}")
        
        # Check positions vs trades
        total_positions = positions_data.get('summary', {}).get('total_positions', 0)
        total_trades = trades_data.get('summary', {}).get('total_trades', 0)
        
        print(f"\n💼 PORTFOLIO STATUS:")
        print(f"   Positions: {total_positions}")
        print(f"   Recent Trades: {total_trades}")
        
        # Identify issues
        issues = []
        
        if len(executable_signals) > 0 and total_trades == 0:
            issues.append("🚨 CRITICAL: Signals present but no trades executing")
        
        if trading_data.get('mode') == 'MINIMAL':
            issues.append("⚠️ Bot is in MINIMAL mode - may have limited execution")
        
        if total_positions > 0 but not positions_data.get('positions'):
            issues.append("⚠️ Position count mismatch - API connection issue")
        
        # Check for execution loop
        try:
            # Try to get execution status
            exec_resp = requests.get(f"{bot_url}/trading/execution")
            if exec_resp.status_code == 404:
                issues.append("❌ Execution loop endpoint not available")
        except:
            pass
        
        if issues:
            print(f"\n🚨 ISSUES IDENTIFIED:")
            for i, issue in enumerate(issues, 1):
                print(f"   {i}. {issue}")
        
        # Generate specific recommendations
        print(f"\n💡 SPECIFIC RECOMMENDATIONS:")
        
        if len(executable_signals) > 0 and total_trades == 0:
            print("   1. 🔧 Check if execution loop is running")
            print("   2. 🔑 Verify API keys have trading permissions")
            print("   3. 💰 Check minimum order size requirements (20 USDT)")
            print("   4. ⚡ Verify EXECUTION_RUNTIME_ENABLED=true")
        
        if trading_data.get('mode') == 'MINIMAL':
            print("   5. 🔄 Switch to FULL mode for complete trading")
            print("   6. 📊 Check if execution intervals are too long")
        
        print("   7. 🌐 Check Render logs for execution errors")
        print("   8. 🔍 Verify WebSocket connections for real-time data")
        
        return {
            'signals': len(signals),
            'executable': len(executable_signals),
            'trades': total_trades,
            'positions': total_positions,
            'issues': issues
        }
        
    except Exception as e:
        print(f"❌ Diagnosis failed: {e}")
        return None

if __name__ == "__main__":
    bot_url = "https://bottie-1.onrender.com"
    result = diagnose_execution_issues(bot_url)
    
    if result:
        print(f"\n📋 SUMMARY:")
        print(f"   Signals: {result['signals']} ({result['executable']} executable)")
        print(f"   Trades: {result['trades']}")
        print(f"   Issues: {len(result['issues'])}")
        
        if result['executable'] > 0 and result['trades'] == 0:
            print(f"\n🎯 MAIN ISSUE: Execution system not running")
            print(f"   The bot is generating signals but not executing trades")
            print(f"   This is likely a configuration or runtime issue")