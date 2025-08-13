#!/usr/bin/env python3
"""
Bottie System Health Check (Python)
Tests all endpoints: health, sentiment, ML monitoring, and cross-pair trading
"""

import requests
import json
import sys
import time
from typing import Dict, Any, Optional

class BottieHealthChecker:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url.rstrip('/')
        self.results = {}
        
    def test_endpoint(self, name: str, endpoint: str, expected_key: str = None) -> bool:
        """Test a single endpoint"""
        print(f"🔸 Testing {name}... ", end="", flush=True)
        
        try:
            response = requests.get(f"{self.api_url}{endpoint}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.results[name] = {"status": "success", "data": data}
                
                if expected_key and expected_key not in str(data):
                    print("⚠️  PARTIAL")
                    print(f"   Missing expected key: {expected_key}")
                else:
                    print("✅ PASS")
                    if isinstance(data, dict) and len(str(data)) < 200:
                        print(f"   {json.dumps(data, indent=2)}")
                return True
            else:
                print(f"❌ FAIL (HTTP {response.status_code})")
                self.results[name] = {"status": "http_error", "code": response.status_code}
                return False
                
        except requests.exceptions.ConnectionError:
            print("❌ FAIL (Connection Error)")
            self.results[name] = {"status": "connection_error"}
            return False
        except requests.exceptions.Timeout:
            print("❌ FAIL (Timeout)")
            self.results[name] = {"status": "timeout"}
            return False
        except Exception as e:
            print(f"❌ FAIL ({str(e)})")
            self.results[name] = {"status": "error", "error": str(e)}
            return False
        finally:
            print()
    
    def run_health_check(self):
        """Run comprehensive health check"""
        print("🔍 Bottie System Health Check")
        print("=" * 30)
        print(f"🌐 Testing API at: {self.api_url}")
        print()
        
        # Basic Health Check
        print("🏥 BASIC HEALTH CHECKS")
        print("=" * 22)
        self.test_endpoint("Basic Health", "/health", "ok")
        
        # Sentiment System
        print("💭 SENTIMENT SYSTEM")
        print("=" * 19)
        self.test_endpoint("Sentiment Health", "/health")
        self.test_endpoint("Sentiment Scores", "/sentiment")
        self.test_endpoint("Sentiment Debug", "/sentiment/debug")
        
        # ML Monitoring
        print("🧠 ML MONITORING SYSTEM")
        print("=" * 23)
        self.test_endpoint("ML Status", "/ml/status")
        self.test_endpoint("ML Components", "/metrics/components")
        
        # Cross-Pair Trading
        print("🔄 CROSS-PAIR TRADING")
        print("=" * 21)
        self.test_endpoint("Cross-Pair Status", "/cross-pairs/status")
        self.test_endpoint("Cross-Pair Opportunities", "/cross-pairs/opportunities")
        self.test_endpoint("Portfolio Cross-Pairs", "/portfolio/cross-pairs")
        self.test_endpoint("Rebalancing Suggestions", "/portfolio/rebalancing-suggestions")
        
        # Additional Tests
        print("📊 ADDITIONAL CHECKS")
        print("=" * 20)
        self.test_endpoint("Trading Signals", "/signals")
        self.test_endpoint("System Status", "/status")
        
        self.analyze_results()
    
    def analyze_results(self):
        """Analyze test results and provide recommendations"""
        print("🔍 DETAILED ANALYSIS")
        print("=" * 20)
        
        # Sentiment Analysis
        sentiment_data = self.results.get("Sentiment Debug", {}).get("data", {})
        if sentiment_data and "samples" in sentiment_data:
            samples = sentiment_data["samples"]
            asset_count = len(samples)
            total_samples = sum(len(texts) for texts in samples.values())
            
            print(f"💭 Sentiment: {asset_count} assets, {total_samples} total samples")
            for asset, texts in samples.items():
                print(f"   {asset}: {len(texts)} samples")
                
            if total_samples == 0:
                print("   ⚠️  No samples - check keywords/API keys")
            elif total_samples < 10:
                print("   ⚠️  Low sample count - may need time to accumulate")
            else:
                print("   ✅ Good sample collection")
        else:
            print("💭 Sentiment: ❌ No data available")
        print()
        
        # ML Analysis
        ml_data = self.results.get("ML Status", {}).get("data", {})
        if ml_data:
            sample_count = ml_data.get("sample_count", 0)
            brier_score = ml_data.get("brier_score")
            quantum_rank = ml_data.get("quantum_feature_rank")
            
            print(f"🧠 ML Status:")
            print(f"   Sample Count: {sample_count}")
            print(f"   Brier Score: {brier_score}")
            print(f"   Quantum Rank: #{quantum_rank}")
            
            if sample_count >= 50:
                print("   ✅ Good sample size for analysis")
            elif sample_count > 0:
                print(f"   ⚠️  Building samples ({sample_count}/50 minimum)")
            else:
                print("   ⚠️  No samples - need trading activity")
        else:
            print("🧠 ML Status: ❌ No data available")
        print()
        
        # Cross-Pair Analysis
        portfolio_data = self.results.get("Portfolio Cross-Pairs", {}).get("data", {})
        if portfolio_data:
            enabled = portfolio_data.get("enabled", False)
            asset_count = portfolio_data.get("total_assets", 0)
            pair_count = portfolio_data.get("total_pairs", 0)
            
            print(f"🔄 Cross-Pair Status:")
            print(f"   Enabled: {enabled}")
            print(f"   Portfolio Assets: {asset_count}")
            print(f"   Available Pairs: {pair_count}")
            
            if enabled and asset_count > 1:
                print("   ✅ Ready for cross-pair trading")
            elif not enabled:
                print("   ⚠️  Disabled - check configuration")
            else:
                print("   ⚠️  Need more portfolio assets")
        else:
            print("🔄 Cross-Pair Status: ❌ No data available")
        print()
        
        self.generate_summary()
    
    def generate_summary(self):
        """Generate summary and recommendations"""
        print("📋 SUMMARY & RECOMMENDATIONS")
        print("=" * 29)
        
        # Count successful tests
        successful_tests = sum(1 for r in self.results.values() if r["status"] == "success")
        total_tests = len(self.results)
        
        print(f"Overall: {successful_tests}/{total_tests} endpoints responding")
        print()
        
        # System-specific recommendations
        if self.results.get("Sentiment Health", {}).get("status") == "success":
            print("✅ Sentiment system operational")
        else:
            print("⚠️  Check sentiment configuration and API keys")
            print("   - Verify FINNHUB_API_KEY in environment")
            print("   - Check sentiment service is running")
        
        if self.results.get("ML Status", {}).get("status") == "success":
            print("✅ ML monitoring operational")
        else:
            print("⚠️  Check ML learner integration")
            print("   - Verify online learner is initialized")
            print("   - Check ML model files exist")
        
        if self.results.get("Portfolio Cross-Pairs", {}).get("status") == "success":
            print("✅ Cross-pair trading ready")
        else:
            print("⚠️  Check Binance API keys and portfolio")
            print("   - Verify BINANCE_API_KEY and BINANCE_API_SECRET")
            print("   - Ensure portfolio has multiple assets")
        
        print()
        print("🚀 Quick Start Commands:")
        print("  View ML dashboard:     python ml_monitor.py --continuous")
        print("  Generate ML report:    python ml_monitor.py --report")
        print("  Test cross-pairs:      python cross_pair/portfolio_cross_trading.py")
        print()
        print("📖 Integration guides:")
        print("  ML Monitor:       ML_MONITOR_README.md")
        print("  Cross-Pair:       cross_pair/README.md")

def main():
    """Main function"""
    api_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    checker = BottieHealthChecker(api_url)
    checker.run_health_check()

if __name__ == "__main__":
    main()
