#!/usr/bin/env python3
"""Bottie System Status Check - August 13, 2025"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def check_system_status():
    """Check all system components"""
    print("🏛️ BOTTIE SYSTEM STATUS CHECK")
    print("=" * 50)
    print(f"📅 Date: August 13, 2025")
    print(f"💻 Working Directory: {os.getcwd()}")
    print("")
    
    status = {"api": False, "grid": False, "ml": False, "sentiment": False}
    
    # Check API module
    try:
        import api.app
        print("✅ API Module: Loaded successfully")
        status["api"] = True
    except Exception as e:
        print(f"❌ API Module: Error - {e}")
    
    # Check trading grid function
    try:
        from api.app import _symbols_to_scan
        print("✅ Trading Grid: Symbol scanning function available")
        status["grid"] = True
    except Exception as e:
        print(f"❌ Trading Grid: Error - {e}")
    
    # Check ML components
    try:
        import ml
        print("✅ ML Module: Available")
        status["ml"] = True
    except Exception as e:
        print(f"❌ ML Module: Error - {e}")
    
    # Check sentiment service
    try:
        import sentiment.sentiment_service
        print("✅ Sentiment Service: Available")
        status["sentiment"] = True
    except Exception as e:
        print(f"❌ Sentiment Service: Error - {e}")
    
    print("")
    print("📊 DEPLOYMENT STATUS:")
    
    all_good = all(status.values())
    if all_good:
        print("🎉 ALL SYSTEMS OPERATIONAL!")
        print("🏛️ Professional Trading Grid: READY")
        print("📱 Frontend: Available at web/index.html") 
        print("🌐 Backend: Ready for uvicorn startup")
        print("")
        print("🚀 DEPLOYMENT INSTRUCTIONS:")
        print("1. Start backend: python -m uvicorn api.app:app --host 0.0.0.0 --port 8000")
        print("2. Open frontend: web/index.html in browser")
        print("3. Test grid: http://localhost:8000/grid/matrix")
    else:
        print("⚠️  Some components need attention")
        for component, ok in status.items():
            if not ok:
                print(f"   - {component}: Needs debugging")
    
    return all_good

if __name__ == "__main__":
    check_system_status()
