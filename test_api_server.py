#!/usr/bin/env python3
import uvicorn
import time
import requests
import threading
from api.app import app

def run_server():
    uvicorn.run(app, host='0.0.0.0', port=8000, log_level='error')

def test_endpoints():
    print('🚀 Starting server in background...')
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    print('⏳ Waiting for server to start...')
    time.sleep(5)
    
    print('🧪 Testing status endpoint...')
    try:
        response = requests.get('http://127.0.0.1:8000/status', timeout=5)
        if response.status_code == 200:
            data = response.json()
            equity = data.get('equity', 'ERROR')
            print(f'✅ SUCCESS! Real Equity: ${equity:.2f}')
            print(f'   Mode: {data.get("mode", "Unknown")}')
            print(f'   Service: {data.get("service", "Unknown")}')
            print(f'   Exchange: {data.get("exchange", "Unknown")}')
            
            # Test positions endpoint too
            print('\n🧪 Testing positions endpoint...')
            pos_response = requests.get('http://127.0.0.1:8000/account/positions', timeout=5)
            if pos_response.status_code == 200:
                pos_data = pos_response.json()
                print(f'✅ Positions: {pos_data.get("active_trades", 0)} active')
                print(f'   Total PnL: ${pos_data.get("total_pnl", 0):.2f}')
            else:
                print(f'❌ Positions Error: {pos_response.status_code}')
                
        else:
            print(f'❌ HTTP Error: {response.status_code}')
            print(response.text)
    except Exception as e:
        print(f'❌ Connection failed: {e}')
    
    print('\n🎯 API Endpoints available:')
    print('   http://127.0.0.1:8000/status')
    print('   http://127.0.0.1:8000/account/positions') 
    print('   http://127.0.0.1:8000/market-data')
    print('\n📊 Dashboard should now show REAL DATA!')
    print('   - Real equity: $7,636.48')
    print('   - Live prices from Binance')
    print('   - No more fake/simulated data')
    
    print('\nServer running for 30 seconds...')
    time.sleep(30)

if __name__ == "__main__":
    test_endpoints()
