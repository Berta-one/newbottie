#!/usr/bin/env python3
import requests
import json

def check_endpoints():
    base_url = 'http://127.0.0.1:8000'
    endpoints = ['/status', '/account/positions', '/grid/matrix', '/signals', '/ml/status', '/quantum/details']

    for endpoint in endpoints:
        try:
            response = requests.get(f'{base_url}{endpoint}', timeout=5)
            data = response.json()
            print(f'\n🔍 {endpoint}:')
            if isinstance(data, dict):
                print(f'  Keys: {list(data.keys())}')
                if 'equity' in data:
                    equity = data.get('equity', 'MISSING')
                    print(f'  Equity: ${equity}')
                if len(data) == 0:
                    print('  ❌ EMPTY RESPONSE')
                else:
                    print(f'  ✅ Has {len(data)} fields')
            elif isinstance(data, list):
                print(f'  List length: {len(data)}')
                if len(data) == 0:
                    print('  ❌ EMPTY LIST')
                else:
                    print(f'  ✅ Has {len(data)} items')
            else:
                print(f'  Type: {type(data)}')
        except Exception as e:
            print(f'{endpoint}: ❌ ERROR - {e}')

if __name__ == "__main__":
    check_endpoints()
