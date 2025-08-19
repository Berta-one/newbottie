#!/usr/bin/env python3
"""
Daily Report Generator for Bottie Trading System
Generates comprehensive daily reports and can be scheduled
"""
import requests
import json
import time
from datetime import datetime, timedelta
import os

class DailyReportGenerator:
    def __init__(self):
        self.api_base = "https://bottie-1.onrender.com"
        self.report_time = datetime.now()
        
    def fetch_endpoint(self, endpoint):
        """Fetch data from API endpoint"""
        try:
            response = requests.get(f"{self.api_base}{endpoint}", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"⚠️ {endpoint}: HTTP {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ {endpoint}: {e}")
            return None
    
    def generate_daily_report(self):
        """Generate comprehensive daily trading report"""
        print(f"📊 Generating Daily Report - {self.report_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Fetch all data
        print("📡 Fetching data...")
        health = self.fetch_endpoint("/health")
        status = self.fetch_endpoint("/status") 
        trades = self.fetch_endpoint("/trades?limit=100")
        ml_status = self.fetch_endpoint("/ml/status")
        signals = self.fetch_endpoint("/signals")
        
        report = {
            "report_date": self.report_time.isoformat(),
            "report_type": "daily_summary",
            "system_health": self.analyze_system_health(health),
            "trading_performance": self.analyze_trading_performance(trades, status),
            "ml_performance": self.analyze_ml_performance(ml_status),
            "signal_analysis": self.analyze_signals(signals),
            "recommendations": self.generate_recommendations(trades, ml_status, signals)
        }
        
        # Print report
        self.print_report(report)
        
        # Save report
        self.save_report(report)
        
        return report
    
    def analyze_system_health(self, health):
        """Analyze system health metrics"""
        if not health:
            return {"status": "unknown", "issues": ["Health endpoint unavailable"]}
        
        print("\n🏥 SYSTEM HEALTH:")
        print(f"   Status: {health.get('status', 'Unknown')}")
        print(f"   Mode: {health.get('mode', 'Unknown')}")
        print(f"   Exchange: {health.get('exchange', 'Unknown')}")
        print(f"   Equity: ${health.get('equity', 0):.2f}")
        
        return {
            "status": health.get('status', 'Unknown'),
            "mode": health.get('mode', 'Unknown'),
            "exchange": health.get('exchange', 'Unknown'),
            "equity": health.get('equity', 0),
            "features": health.get('features', {})
        }
    
    def analyze_trading_performance(self, trades_data, status):
        """Analyze trading performance for the day"""
        if not trades_data or not trades_data.get('trades'):
            return {"status": "no_data"}
        
        trades = trades_data['trades']
        summary = trades_data.get('summary', {})
        
        # Filter today's trades
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_trades = [
            t for t in trades 
            if datetime.fromtimestamp(t['timestamp']) >= today_start
        ]
        
        print(f"\n📈 TRADING PERFORMANCE:")
        print(f"   Total Trades: {len(trades)}")
        print(f"   Today's Trades: {len(today_trades)}")
        print(f"   Total P&L: ${summary.get('net_pnl', 0):.2f}")
        print(f"   Win Rate: {summary.get('win_rate', 0):.1f}%")
        print(f"   Total Volume: ${summary.get('total_volume', 0):.2f}")
        
        # Calculate today's P&L
        today_pnl = sum(t.get('pnl', 0) for t in today_trades)
        print(f"   Today's P&L: ${today_pnl:.2f}")
        
        return {
            "total_trades": len(trades),
            "today_trades": len(today_trades),
            "total_pnl": summary.get('net_pnl', 0),
            "today_pnl": today_pnl,
            "win_rate": summary.get('win_rate', 0),
            "total_volume": summary.get('total_volume', 0),
            "active_positions": status.get('active_trades', 0) if status else 0
        }
    
    def analyze_ml_performance(self, ml_data):
        """Analyze ML model performance"""
        if not ml_data:
            return {"status": "no_data"}
        
        print(f"\n🧠 ML PERFORMANCE:")
        print(f"   Accuracy: {(ml_data.get('accuracy', 0) * 100):.1f}%")
        print(f"   Confidence: {(ml_data.get('confidence', 0) * 100):.1f}%")
        print(f"   Total Predictions: {ml_data.get('total_predictions', 0)}")
        print(f"   Successful Predictions: {ml_data.get('successful_predictions', 0)}")
        
        return {
            "accuracy": ml_data.get('accuracy', 0),
            "confidence": ml_data.get('confidence', 0),
            "total_predictions": ml_data.get('total_predictions', 0),
            "successful_predictions": ml_data.get('successful_predictions', 0),
            "data_quality": ml_data.get('data_quality', 0)
        }
    
    def analyze_signals(self, signals_data):
        """Analyze current trading signals"""
        if not signals_data or not signals_data.get('signals'):
            return {"status": "no_data"}
        
        signals = signals_data['signals']
        
        buy_signals = [s for s in signals if s.get('signal') == 'BUY']
        sell_signals = [s for s in signals if s.get('signal') == 'SELL']
        hold_signals = [s for s in signals if s.get('signal') == 'HOLD']
        
        print(f"\n📡 CURRENT SIGNALS:")
        print(f"   BUY signals: {len(buy_signals)}")
        print(f"   SELL signals: {len(sell_signals)}")
        print(f"   HOLD signals: {len(hold_signals)}")
        
        if buy_signals:
            best_buy = max(buy_signals, key=lambda x: x.get('final_prob', 0))
            print(f"   Best BUY: {best_buy['symbol']} ({best_buy['final_prob']:.3f})")
        
        return {
            "total_signals": len(signals),
            "buy_count": len(buy_signals),
            "sell_count": len(sell_signals),
            "hold_count": len(hold_signals),
            "best_buy": buy_signals[0] if buy_signals else None,
            "best_sell": sell_signals[0] if sell_signals else None
        }
    
    def generate_recommendations(self, trades_data, ml_data, signals_data):
        """Generate actionable recommendations"""
        recommendations = []
        
        if trades_data and trades_data.get('summary'):
            win_rate = trades_data['summary'].get('win_rate', 0)
            if win_rate < 40:
                recommendations.append("⚠️ Win rate below 40% - consider adjusting ML thresholds")
            elif win_rate > 70:
                recommendations.append("🎯 Excellent win rate - consider increasing position sizes")
        
        if ml_data:
            accuracy = ml_data.get('accuracy', 0)
            if accuracy < 0.6:
                recommendations.append("🧠 ML accuracy below 60% - retrain model with recent data")
            elif accuracy > 0.85:
                recommendations.append("🚀 Excellent ML performance - model is well-tuned")
        
        if signals_data and signals_data.get('signals'):
            signals = signals_data['signals']
            high_conf_signals = [s for s in signals if s.get('final_prob', 0) > 0.8]
            if high_conf_signals:
                recommendations.append(f"💡 {len(high_conf_signals)} high-confidence signals available")
        
        print(f"\n💡 RECOMMENDATIONS:")
        for rec in recommendations:
            print(f"   {rec}")
        
        return recommendations
    
    def print_report(self, report):
        """Print formatted report"""
        print(f"\n📋 DAILY REPORT SUMMARY:")
        print(f"   Generated: {report['report_date']}")
        print(f"   System Status: {report['system_health']['status']}")
        print(f"   Trading Mode: {report['system_health']['mode']}")
        
        if report['trading_performance']['status'] != 'no_data':
            tp = report['trading_performance']
            print(f"   Today's Trades: {tp['today_trades']}")
            print(f"   Today's P&L: ${tp['today_pnl']:.2f}")
            print(f"   Total P&L: ${tp['total_pnl']:.2f}")
        
        if report['ml_performance']['status'] != 'no_data':
            ml = report['ml_performance']
            print(f"   ML Accuracy: {(ml['accuracy'] * 100):.1f}%")
            print(f"   ML Confidence: {(ml['confidence'] * 100):.1f}%")
    
    def save_report(self, report):
        """Save report to file"""
        filename = f"daily_report_{self.report_time.strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\n💾 Report saved: {filename}")
        except Exception as e:
            print(f"❌ Error saving report: {e}")

def main():
    """Main function - can be called manually or via cron"""
    print("🚀 Bottie Daily Report Generator")
    print("=" * 60)
    
    generator = DailyReportGenerator()
    report = generator.generate_daily_report()
    
    print("\n" + "=" * 60)
    print("✅ Daily report generation complete!")
    print("\n🕐 TO SCHEDULE DAILY REPORTS:")
    print("Add this to your cron job (runs at 6 PM daily):")
    print("0 18 * * * cd /path/to/bottie && python3 daily_report_generator.py")
    
    return report

if __name__ == "__main__":
    main()