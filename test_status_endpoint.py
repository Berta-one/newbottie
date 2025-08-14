import requests
import json

try:
    response = requests.get("http://127.0.0.1:8000/status", timeout=10)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("\n🎯 API Status Response:")
        print("="*50)
        print(f"Service: {data.get('service', 'Unknown')}")
        print(f"Mode: {data.get('mode', 'Unknown')}")
        print(f"Exchange: {data.get('exchange', 'Unknown')}")
        print(f"💰 EQUITY: ${data.get('equity', 'ERROR'):.2f}")
        print(f"Real Trading: {data.get('features', {}).get('real_trading', {}).get('enabled', False)}")
        print(f"Live Data: {data.get('features', {}).get('live_data', {}).get('enabled', False)}")
        print(f"Real Positions: {data.get('features', {}).get('real_positions', {}).get('enabled', False)}")
    else:
        print(f"HTTP Error: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"Connection Error: {e}")
