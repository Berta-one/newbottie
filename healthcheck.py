#!/usr/bin/env python3
"""
Health monitoring script for Railway bot
"""

import requests
import time
import os
import json
from datetime import datetime


def check_bot_health():
    """Check if bot is responding"""
    base_url = os.getenv("RAILWAY_URL", "http://localhost:8501")

    try:
        response = requests.get(f"{base_url}/health", timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Bot alive - Uptime: {data.get('uptime_seconds', 0):.0f}s")
            return True
        else:
            print(f"❌ Bot unhealthy - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def check_dashboard():
    """Check if dashboard is accessible"""
    base_url = os.getenv("RAILWAY_URL", "http://localhost:8501")

    try:
        response = requests.get(base_url, timeout=30)
        if response.status_code == 200:
            print("✅ Dashboard accessible")
            return True
        else:
            print(f"⚠️ Dashboard returned {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Dashboard check failed: {e}")
        return False


def monitor_continuously():
    """Monitor bot continuously"""
    consecutive_failures = 0
    check_count = 0

    print("🔍 Starting continuous monitoring...")

    while True:
        try:
            check_count += 1
            print(f"\n🔍 Check #{check_count} - {datetime.now().strftime('%H:%M:%S')}")

            health_ok = check_bot_health()
            dashboard_ok = check_dashboard()

            if health_ok or dashboard_ok:
                consecutive_failures = 0
                print("✅ Bot is healthy")
            else:
                consecutive_failures += 1
                print(f"❌ Failed (consecutive: {consecutive_failures})")

            if consecutive_failures >= 5:
                print("🚨 ALERT: Bot appears down!")

            time.sleep(300)  # 5 minutes

        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped")
            break
        except Exception as e:
            print(f"❌ Monitor error: {e}")
            time.sleep(60)


def quick_check():
    """Quick status check"""
    print("🔍 Quick Bot Status Check")
    print("=" * 30)

    health_ok = check_bot_health()
    dashboard_ok = check_dashboard()

    if health_ok and dashboard_ok:
        print("\n✅ HEALTHY - All systems responding")
    elif health_ok or dashboard_ok:
        print("\n⚠️ PARTIAL - Some systems responding")
    else:
        print("\n❌ DOWN - No systems responding")

    return health_ok or dashboard_ok


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "monitor":
        monitor_continuously()
    else:
        quick_check()
