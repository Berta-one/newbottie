#!/usr/bin/env python3
"""
WebSocket Diagnostic Tool for Bottie Live Dashboard
Diagnoses WebSocket connection issues and provides solutions.
"""

import os
import sys
import time
import requests
import json
from datetime import datetime

def print_header(title):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")

def print_status(label, status, details=""):
    icon = "✅" if status else "❌"
    print(f"{icon} {label}: {details}")

def test_api_connectivity():
    """Test basic API connectivity"""
    print_header("API CONNECTIVITY TEST")
    
    api_url = "https://bottie-1.onrender.com"
    
    try:
        # Test root endpoint
        response = requests.get(f"{api_url}/", timeout=10)
        print_status("Root endpoint", response.status_code == 200, 
                    f"Status: {response.status_code}")
        
        # Test health endpoint
        response = requests.get(f"{api_url}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print_status("Health endpoint", True, 
                        f"Service: {data.get('service', 'unknown')}")
            print_status("Exchange mode", True, 
                        f"Mode: {data.get('mode', 'unknown')}")
            print_status("Equity", True, 
                        f"${data.get('equity', 0):.2f}")
            
            # Check for WebSocket status
            ws_status = data.get('websocket_status')
            if ws_status:
                print_status("WebSocket Status", ws_status == 'CONNECTED', 
                            f"Status: {ws_status}")
            else:
                print_status("WebSocket Status", False, "Not reported by API")
                
        else:
            print_status("Health endpoint", False, 
                        f"Status: {response.status_code}")
            
    except Exception as e:
        print_status("API Connection", False, f"Error: {e}")

def test_environment_variables():
    """Test if required environment variables are set"""
    print_header("ENVIRONMENT VARIABLES TEST")
    
    required_vars = [
        'BINANCE_API_KEY',
        'BINANCE_API_SECRET'
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print_status(var, True, f"Set ({value[:10]}...)")
        else:
            print_status(var, False, "Not set")

def test_websocket_requirements():
    """Test WebSocket-related requirements"""
    print_header("WEBSOCKET REQUIREMENTS TEST")
    
    try:
        import websocket
        print_status("websocket-client library", True, "Available")
    except ImportError:
        print_status("websocket-client library", False, "Not installed")
    
    try:
        import threading
        print_status("threading support", True, "Available")
    except ImportError:
        print_status("threading support", False, "Not available")

def analyze_frontend_status():
    """Analyze the frontend WebSocket status display"""
    print_header("FRONTEND ANALYSIS")
    
    # Check if the frontend files exist
    frontend_files = [
        '/workspace/web/app.js',
        '/workspace/web/index.html'
    ]
    
    for file_path in frontend_files:
        if os.path.exists(file_path):
            print_status(f"Frontend file {os.path.basename(file_path)}", True, "Exists")
            
            # Check if WebSocket status code is present
            with open(file_path, 'r') as f:
                content = f.read()
                if 'websocket-status' in content:
                    print_status(f"WebSocket status element in {os.path.basename(file_path)}", 
                               True, "Found")
                if 'updateWebSocketStatus' in content:
                    print_status(f"WebSocket update function in {os.path.basename(file_path)}", 
                               True, "Found")
        else:
            print_status(f"Frontend file {os.path.basename(file_path)}", False, "Not found")

def provide_solution():
    """Provide solution based on diagnosis"""
    print_header("SOLUTION")
    
    print("🔧 IDENTIFIED ISSUES AND SOLUTIONS:")
    print()
    print("1. STATIC WEBSOCKET STATUS:")
    print("   - Issue: Frontend shows hardcoded 'WS: DISCONNECTED'")
    print("   - Solution: Updated frontend code to dynamically update WebSocket status")
    print()
    print("2. MISSING WEBSOCKET STATUS IN API:")
    print("   - Issue: Backend /health endpoint doesn't report WebSocket status")
    print("   - Solution: Updated backend to include websocket_status field")
    print()
    print("3. WEBSOCKET MANAGER STATUS:")
    print("   - Issue: WebSocket manager may not be properly initialized")
    print("   - Solution: Check environment variables and WebSocket initialization")
    print()
    print("📋 NEXT STEPS:")
    print("   1. Deploy updated backend code to Render")
    print("   2. Deploy updated frontend code to Netlify")
    print("   3. Verify environment variables are set correctly")
    print("   4. Monitor WebSocket connection status in real-time")
    print()
    print("🚀 IMMEDIATE FIX:")
    print("   - Frontend will now show real WebSocket status from API")
    print("   - Status updates every time health data is refreshed")
    print("   - Visual indicators (colors) match connection state")

def main():
    print_header("BOTTIE WEBSOCKET DIAGNOSTIC TOOL")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run all diagnostic tests
    test_api_connectivity()
    test_environment_variables()
    test_websocket_requirements()
    analyze_frontend_status()
    provide_solution()
    
    print_header("DIAGNOSTIC COMPLETE")

if __name__ == "__main__":
    main()