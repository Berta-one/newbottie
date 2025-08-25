#!/usr/bin/env python3
"""
Minimal test to check what's causing Render deployment issues
"""

import os
import sys

print("🔍 RENDER DEPLOYMENT DIAGNOSTIC")
print("=" * 40)

# Test Python version
print(f"Python version: {sys.version}")

# Test environment
print(f"Environment: {os.getenv('ENVIRONMENT', 'not_set')}")
print(f"Port: {os.getenv('PORT', 'not_set')}")

# Test imports
try:
    import fastapi
    print(f"✅ FastAPI: {fastapi.__version__}")
except Exception as e:
    print(f"❌ FastAPI: {e}")

try:
    import uvicorn
    print(f"✅ Uvicorn: {uvicorn.__version__}")
except Exception as e:
    print(f"❌ Uvicorn: {e}")

try:
    import ccxt
    print(f"✅ CCXT: {ccxt.__version__}")
except Exception as e:
    print(f"❌ CCXT: {e}")

try:
    import requests
    print(f"✅ Requests: {requests.__version__}")
except Exception as e:
    print(f"❌ Requests: {e}")

# Test render_api import
try:
    from render_api import app
    print("✅ render_api imports successfully")
    
    # Test if app can be created
    print(f"✅ FastAPI app created: {type(app)}")
    
except Exception as e:
    print(f"❌ render_api import failed: {e}")
    import traceback
    traceback.print_exc()

print("\n🎯 DIAGNOSIS COMPLETE")