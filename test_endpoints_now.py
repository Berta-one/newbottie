#!/usr/bin/env python3
"""
Comprehensive endpoint testing to diagnose frontend vs backend issues
"""

import requests
import json
import time
from urllib.parse import urljoin

class EndpointTester:
    def __init__(self, base_url="https://bottie-1.onrender.com"):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_token = None
        self.results = {}
        
    def test_endpoint(self, endpoint, method="GET", data=None, auth_required=False):
        """Test a single endpoint and return detailed results"""
        url = urljoin(self.base_url, endpoint)
        headers = {"Content-Type": "application/json"}
        
        if auth_required and self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        try:
            start_time = time.time()
            
            if method == "GET":
                response = self.session.get(url, headers=headers, timeout=10)
            elif method == "POST":
                response = self.session.post(url, headers=headers, json=data, timeout=10)
            else:
                return {"success": False, "error": f"Unsupported method: {method}"}
            
            response_time = time.time() - start_time
            
            result = {
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "response_time": round(response_time, 3),
                "content_type": response.headers.get("Content-Type", ""),
                "url": url
            }
            
            # Try to parse JSON response
            try:
                if response.headers.get("Content-Type", "").startswith("application/json"):
                    result["data"] = response.json()
                    result["data_type"] = "json"
                else:
                    result["data"] = response.text[:500]  # First 500 chars
                    result["data_type"] = "text"
            except:
                result["data"] = response.text[:500]
                result["data_type"] = "text"
            
            return result
            
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout (10s)", "url": url}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Connection Error", "url": url}
        except Exception as e:
            return {"success": False, "error": str(e), "url": url}
    
    def authenticate(self):
        """Test authentication"""
        print("🔐 Testing Authentication...")
        
        # Test with any credentials (should work due to bypass)
        auth_data = {"username": "test", "password": "test"}
        result = self.test_endpoint("/auth/login", "POST", auth_data)
        
        if result["success"] and isinstance(result.get("data"), dict):
            self.auth_token = result["data"].get("access_token")
            print(f"✅ Auth successful: {result['data'].get('user', {})}")
            return True
        else:
            print(f"❌ Auth failed: {result}")
            return False
    
    def test_all_endpoints(self):
        """Test all expected endpoints"""
        print(f"🧪 Testing all endpoints on {self.base_url}")
        print("=" * 80)
        
        # Basic connectivity
        endpoints_basic = [
            ("/", "Root endpoint"),
            ("/health", "Health check"),
            ("/debug/auth", "Debug auth info"),
        ]
        
        print("\n📡 Basic Connectivity Tests:")
        print("-" * 40)
        for endpoint, description in endpoints_basic:
            result = self.test_endpoint(endpoint)
            self.results[endpoint] = result
            
            status = "✅" if result["success"] else "❌"
            print(f"{status} {description}: {endpoint}")
            print(f"    Status: {result.get('status_code', 'N/A')}")
            print(f"    Time: {result.get('response_time', 'N/A')}s")
            
            if result["success"] and result.get("data_type") == "json":
                data = result["data"]
                if isinstance(data, dict):
                    # Show key data points
                    for key in ["status", "service", "version", "ok", "time"][:3]:
                        if key in data:
                            print(f"    {key}: {data[key]}")
            else:
                print(f"    Error: {result.get('error', 'Failed')}")
            print()
        
        # Authentication test
        auth_success = self.authenticate()
        print()
        
        # Dashboard endpoints
        endpoints_dashboard = [
            ("/status", "Status/Portfolio data"),
            ("/signals", "Trading signals"),
            ("/sentiment", "Sentiment analysis"),
            ("/positions", "Position data"),
            ("/trades", "Trade history"),
            ("/logs/last", "System logs"),
            ("/ml/status", "ML system status"),
            ("/quantum/details", "Quantum system"),
            ("/grid/matrix", "Cross-pair grid"),
        ]
        
        print("📊 Dashboard Data Tests:")
        print("-" * 40)
        for endpoint, description in endpoints_dashboard:
            result = self.test_endpoint(endpoint, auth_required=auth_success)
            self.results[endpoint] = result
            
            status = "✅" if result["success"] else "❌"
            print(f"{status} {description}: {endpoint}")
            print(f"    Status: {result.get('status_code', 'N/A')}")
            print(f"    Time: {result.get('response_time', 'N/A')}s")
            
            if result["success"] and result.get("data_type") == "json":
                data = result["data"]
                if isinstance(data, dict):
                    # Show relevant data structure
                    if endpoint == "/status":
                        print(f"    Equity: {data.get('equity', 'N/A')}")
                        print(f"    Positions: {len(data.get('positions', {}))}")
                    elif endpoint == "/signals":
                        signals = data.get('signals', []) if isinstance(data, dict) else data
                        if isinstance(signals, list):
                            print(f"    Signals count: {len(signals)}")
                            if signals:
                                print(f"    Sample signal: {signals[0].get('symbol', 'N/A')} -> {signals[0].get('signal', 'N/A')}")
                        else:
                            print(f"    Signals: {signals}")
                    elif endpoint == "/sentiment":
                        scores = data.get('scores', data)
                        print(f"    Sentiment data: {len(scores) if isinstance(scores, dict) else 'Invalid'}")
                    elif endpoint == "/ml/status":
                        print(f"    Accuracy: {data.get('accuracy', 'N/A')}")
                        print(f"    Predictions: {data.get('total_predictions', 'N/A')}")
                    elif endpoint == "/grid/matrix":
                        print(f"    Rows: {len(data.get('rows', []))}")
                        print(f"    Cols: {len(data.get('cols', []))}")
                    else:
                        # Show first few keys
                        keys = list(data.keys())[:4]
                        print(f"    Keys: {keys}")
            else:
                print(f"    Error: {result.get('error', 'Failed')}")
            print()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        total = len(self.results)
        successful = sum(1 for r in self.results.values() if r.get("success"))
        failed = total - successful
        
        print("\n" + "=" * 80)
        print("📋 ENDPOINT TEST SUMMARY")
        print("=" * 80)
        print(f"Total endpoints tested: {total}")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"Success rate: {successful/total*100:.1f}%")
        
        if failed > 0:
            print(f"\n❌ Failed Endpoints:")
            for endpoint, result in self.results.items():
                if not result.get("success"):
                    status = result.get("status_code", "Error")
                    error = result.get("error", "Unknown error")
                    print(f"  {endpoint}: {status} - {error}")
        
        print("\n🎯 Dashboard Data Analysis:")
        
        # Check what data is actually available
        working_data = {}
        for endpoint, result in self.results.items():
            if result.get("success") and result.get("data_type") == "json":
                working_data[endpoint] = result["data"]
        
        if "/status" in working_data:
            status_data = working_data["/status"]
            print(f"💰 Portfolio: Equity ${status_data.get('equity', 0):,.2f}")
            positions = status_data.get('positions', {})
            print(f"📊 Positions: {len(positions)} active")
            
        if "/signals" in working_data:
            signals_data = working_data["/signals"]
            signals = signals_data.get('signals', []) if isinstance(signals_data, dict) else signals_data
            if isinstance(signals, list):
                print(f"📡 Signals: {len(signals)} active")
            
        if "/ml/status" in working_data:
            ml_data = working_data["/ml/status"]
            print(f"🧠 ML: {ml_data.get('accuracy', 0)*100:.1f}% accuracy, {ml_data.get('total_predictions', 0)} predictions")
            
        # Identify the issue
        print(f"\n🔍 DIAGNOSIS:")
        if successful == 0:
            print("❌ BACKEND ISSUE: No endpoints working - Render deployment failed")
        elif successful < 5:
            print("⚠️  PARTIAL BACKEND ISSUE: Only basic endpoints working")
        elif failed > 0:
            print("⚠️  MIXED ISSUE: Some endpoints missing - API incomplete")
        else:
            print("✅ BACKEND WORKING: All endpoints responding - Issue likely frontend")

def main():
    print("🧪 Comprehensive Endpoint Testing")
    print("Testing connection between Netlify frontend and Render backend")
    print()
    
    tester = EndpointTester()
    tester.test_all_endpoints()

if __name__ == "__main__":
    main()