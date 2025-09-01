#!/usr/bin/env python3
"""
Test script for Bottie deployment on Render
Tests all endpoints including cross-pair trading functionality
"""

import requests
import json
import time
from typing import Dict, List, Any

class RenderDeploymentTester:
    def __init__(self, base_url: str = "https://bottie-1.onrender.com"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 15
        
    def test_endpoint(self, endpoint: str, method: str = "GET") -> Dict[str, Any]:
        """Test a single endpoint and return results"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url)
            else:
                response = self.session.request(method, url)
                
            return {
                "endpoint": endpoint,
                "status_code": response.status_code,
                "success": response.status_code < 400,
                "response_time": response.elapsed.total_seconds(),
                "data": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text[:200],
                "error": None
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "endpoint": endpoint,
                "status_code": None,
                "success": False,
                "response_time": None,
                "data": None,
                "error": str(e)
            }
    
    def run_comprehensive_test(self):
        """Run comprehensive test of all Bottie endpoints"""
        print("🚀 Testing Bottie Render Deployment")
        print(f"🌐 URL: {self.base_url}")
        print("=" * 60)
        print()
        
        # Core endpoints
        core_endpoints = [
            "/",
            "/health", 
            "/status",
            "/signals",
            "/portfolio",
            "/portfolio/balance",
            "/sentiment"
        ]
        
        # ML endpoints (if available)
        ml_endpoints = [
            "/ml/status",
            "/ml/health",
            "/metrics/components"
        ]
        
        # Cross-pair trading endpoints (if deployed)
        cross_pair_endpoints = [
            "/portfolio/cross-pairs",
            "/cross-pairs/opportunities", 
            "/cross-pairs/status",
            "/portfolio/rebalancing-suggestions"
        ]
        
        all_results = []
        
        # Test core endpoints
        print("📊 Core Endpoints:")
        print("-" * 30)
        for endpoint in core_endpoints:
            result = self.test_endpoint(endpoint)
            all_results.append(result)
            
            status = "✅" if result["success"] else "❌"
            response_time = f"{result['response_time']:.2f}s" if result["response_time"] else "timeout"
            print(f"{status} {endpoint:25} {result['status_code']} ({response_time})")
            
            if not result["success"] and result["error"]:
                print(f"   Error: {result['error']}")
        
        print()
        
        # Test ML endpoints
        print("🧠 ML Endpoints:")
        print("-" * 30)
        for endpoint in ml_endpoints:
            result = self.test_endpoint(endpoint)
            all_results.append(result)
            
            status = "✅" if result["success"] else "❌"
            response_time = f"{result['response_time']:.2f}s" if result["response_time"] else "timeout"
            print(f"{status} {endpoint:25} {result['status_code']} ({response_time})")
        
        print()
        
        # Test cross-pair endpoints
        print("🔄 Cross-Pair Trading Endpoints:")
        print("-" * 30)
        cross_pair_available = 0
        for endpoint in cross_pair_endpoints:
            result = self.test_endpoint(endpoint)
            all_results.append(result)
            
            status = "✅" if result["success"] else "❌"
            response_time = f"{result['response_time']:.2f}s" if result["response_time"] else "timeout"
            print(f"{status} {endpoint:25} {result['status_code']} ({response_time})")
            
            if result["success"]:
                cross_pair_available += 1
        
        print()
        
        # Analysis
        successful = sum(1 for r in all_results if r["success"])
        total = len(all_results)
        
        print("📈 Analysis:")
        print("=" * 60)
        print(f"✅ Successful endpoints: {successful}/{total}")
        print(f"❌ Failed endpoints: {total - successful}/{total}")
        print(f"🔄 Cross-pair endpoints available: {cross_pair_available}/{len(cross_pair_endpoints)}")
        print()
        
        # Detailed analysis
        if cross_pair_available == 0:
            print("🔧 Cross-Pair Trading Status: NOT DEPLOYED")
            print("   To deploy cross-pair trading:")
            print("   1. Run setup_cross_pair_trading.py locally")
            print("   2. Integrate the enhanced API code")
            print("   3. Deploy updated code to Render")
            print()
        elif cross_pair_available < len(cross_pair_endpoints):
            print("🔧 Cross-Pair Trading Status: PARTIALLY DEPLOYED")
            print("   Some cross-pair endpoints are missing")
            print()
        else:
            print("🎉 Cross-Pair Trading Status: FULLY DEPLOYED")
            print("   All cross-pair endpoints are available!")
            print()
        
        # Health check details
        health_result = next((r for r in all_results if r["endpoint"] == "/health"), None)
        if health_result and health_result["success"]:
            print("💊 System Health:")
            print("-" * 30)
            health_data = health_result["data"]
            if isinstance(health_data, dict):
                print(f"Status: {health_data.get('status', 'unknown')}")
                print(f"Service: {health_data.get('service', 'unknown')}")
                print(f"Equity: ${health_data.get('equity', 0):,.2f}")
                print(f"Exchange: {health_data.get('exchange', 'unknown')}")
                print(f"ML Enabled: {health_data.get('ml', {}).get('enabled', False)}")
                print(f"Quantum Enabled: {health_data.get('quantum', {}).get('enabled', False)}")
                print(f"Sentiment Enabled: {health_data.get('sentiment', {}).get('enabled', False)}")
        
        print()
        return all_results
    
    def test_cross_pair_functionality(self):
        """Specifically test cross-pair trading functionality"""
        print("🔄 Cross-Pair Trading Functionality Test")
        print("=" * 50)
        print()
        
        # Test cross-pair endpoints with detailed output
        endpoints_to_test = [
            ("/portfolio/cross-pairs", "Portfolio cross-pair availability"),
            ("/cross-pairs/opportunities", "Current cross-pair opportunities"),
            ("/portfolio/rebalancing-suggestions", "AI rebalancing suggestions")
        ]
        
        for endpoint, description in endpoints_to_test:
            print(f"Testing: {description}")
            print(f"Endpoint: {endpoint}")
            
            result = self.test_endpoint(endpoint)
            
            if result["success"]:
                print("✅ Available")
                if isinstance(result["data"], dict):
                    # Pretty print the response
                    print("Response:")
                    print(json.dumps(result["data"], indent=2))
                else:
                    print(f"Response: {result['data']}")
            else:
                print("❌ Not available")
                if result["error"]:
                    print(f"Error: {result['error']}")
            
            print("-" * 50)
            print()

def main():
    """Main test function"""
    tester = RenderDeploymentTester()
    
    # Run comprehensive test
    results = tester.run_comprehensive_test()
    
    # Test cross-pair functionality specifically
    tester.test_cross_pair_functionality()
    
    print("🎯 Recommendations:")
    print("-" * 30)
    
    # Check if cross-pair trading is deployed
    cross_pair_working = any(
        r["success"] for r in results 
        if r["endpoint"] in ["/portfolio/cross-pairs", "/cross-pairs/opportunities"]
    )
    
    if not cross_pair_working:
        print("1. Cross-pair trading is not deployed to Render")
        print("2. Run setup_cross_pair_trading.py to create the integration")
        print("3. Update your api/app.py with cross-pair endpoints")
        print("4. Deploy the updated code to Render")
        print("5. Test again with this script")
    else:
        print("1. ✅ Cross-pair trading is deployed and working!")
        print("2. Check the dashboard for cross-pair opportunities")
        print("3. Monitor AI rebalancing suggestions")
        print("4. Enable cross-pair trading in your environment variables")
    
    print()
    print("📊 Test completed!")

if __name__ == "__main__":
    main()
