#!/usr/bin/env python3
import requests
import time
import json

print('🔍 COMPREHENSIVE DIAGNOSTIC - Running for 30 seconds...')
print('=' * 60)

base_url = 'https://bottie-1.onrender.com'
test_count = 0
success_count = 0
error_patterns = {}

# Test endpoints over time to see consistency
for i in range(6):  # 6 tests over 30 seconds
    test_count += 1
    print(f'\n📊 Test {test_count}/6 (every 5 seconds)')
    print('-' * 30)
    
    endpoints = ['/health', '/status', '/signals', '/ml/status']
    
    for endpoint in endpoints:
        try:
            start = time.time()
            response = requests.get(f'{base_url}{endpoint}', timeout=5)
            duration = time.time() - start
            
            if response.status_code == 200:
                print(f'✅ {endpoint}: OK ({duration:.2f}s)')
                success_count += 1
                
                # Show sample data for key endpoints
                if endpoint == '/status' and i == 0:  # Only first time
                    data = response.json()
                    print(f'   💰 Equity: ${data.get("equity", 0):,.2f}')
                    print(f'   📊 Positions: {len(data.get("positions", {}))}')
                elif endpoint == '/signals' and i == 0:
                    data = response.json()
                    signals = data.get('signals', data) if isinstance(data, dict) else data
                    if isinstance(signals, list):
                        print(f'   📡 Signals: {len(signals)}')
                        
            else:
                print(f'❌ {endpoint}: {response.status_code} ({duration:.2f}s)')
                error_key = f'{endpoint}:{response.status_code}'
                error_patterns[error_key] = error_patterns.get(error_key, 0) + 1
                
        except requests.exceptions.Timeout:
            print(f'⏰ {endpoint}: TIMEOUT (>5s)')
            error_patterns[f'{endpoint}:TIMEOUT'] = error_patterns.get(f'{endpoint}:TIMEOUT', 0) + 1
        except Exception as e:
            print(f'💥 {endpoint}: ERROR - {str(e)[:50]}')
            error_patterns[f'{endpoint}:ERROR'] = error_patterns.get(f'{endpoint}:ERROR', 0) + 1
    
    if i < 5:  # Don't sleep after last test
        print('⏳ Waiting 5 seconds...')
        time.sleep(5)

print(f'\n' + '=' * 60)
print('📋 DIAGNOSTIC SUMMARY')
print('=' * 60)
print(f'Total requests: {test_count * 4}')
print(f'Successful: {success_count}')
print(f'Success rate: {(success_count/(test_count * 4))*100:.1f}%')

if error_patterns:
    print(f'\n❌ Error Patterns:')
    for error, count in sorted(error_patterns.items(), key=lambda x: x[1], reverse=True):
        print(f'   {error}: {count} times')

print(f'\n🔍 DIAGNOSIS:')
if success_count == 0:
    print('❌ CRITICAL: Backend completely down')
elif success_count < (test_count * 4) * 0.5:
    print('⚠️  UNSTABLE: Backend intermittently failing (< 50% uptime)')
elif success_count < (test_count * 4) * 0.8:
    print('⚠️  DEGRADED: Backend partially working (50-80% uptime)')
else:
    print('✅ STABLE: Backend mostly working (> 80% uptime)')

# Additional checks
print(f'\n🔍 ADDITIONAL ANALYSIS:')

# Check if it's a Render cold start issue
print('Testing cold start behavior...')
try:
    # Make a request and measure response time
    start = time.time()
    r = requests.get(f'{base_url}/health', timeout=15)
    duration = time.time() - start
    
    if duration > 10:
        print('⚠️  SLOW RESPONSE: Likely Render cold start issue (>10s)')
    elif duration > 5:
        print('⚠️  SLOW RESPONSE: Possible Render scaling issue (5-10s)')
    else:
        print('✅ NORMAL RESPONSE: Response time acceptable (<5s)')
        
except Exception as e:
    print(f'❌ REQUEST FAILED: {e}')

# Test specific endpoint that frontend is calling
print('\nTesting problematic endpoints...')
problematic = ['/sentiment', '/positions', '/auth/login']
for endpoint in problematic:
    try:
        r = requests.get(f'{base_url}{endpoint}', timeout=5)
        print(f'{endpoint}: {r.status_code}')
    except Exception as e:
        print(f'{endpoint}: ERROR - {e}')