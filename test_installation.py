import sys
import importlib

def test_import(module_name, package_name=None):
    """Test if a module can be imported"""
    try:
        importlib.import_module(module_name)
        print(f"✅ {package_name or module_name} - OK")
        return True
    except ImportError as e:
        print(f"❌ {package_name or module_name} - MISSING ({e})")
        return False

def main():
    print("🧪 Testing Advanced Trading System Dependencies")
    print("=" * 60)
    
    # Test basic dependencies
    print("\n📦 Basic Dependencies:")
    basic_deps = [
        ("numpy", "NumPy"),
        ("pandas", "Pandas"),
        ("requests", "Requests"),
        ("dotenv", "Python-dotenv"),
        ("binance", "Python-binance"),
        ("pytz", "PyTZ")
    ]
    
    basic_ok = all(test_import(module, name) for module, name in basic_deps)
    
    # Test ML dependencies
    print("\n🧠 Machine Learning Dependencies:")
    ml_deps = [
        ("sklearn", "Scikit-learn"),
        ("joblib", "Joblib"),
        ("scipy", "SciPy"),
        ("statsmodels", "Statsmodels")
    ]
    
    ml_ok = all(test_import(module, name) for module, name in ml_deps)
    
    # Test specific sklearn modules
    print("\n🔍 Scikit-learn Modules:")
    sklearn_modules = [
        ("sklearn.ensemble", "Ensemble Methods"),
        ("sklearn.preprocessing", "Preprocessing"),
        ("sklearn.model_selection", "Model Selection"),
        ("sklearn.metrics", "Metrics")
    ]
    
    sklearn_ok = all(test_import(module, name) for module, name in sklearn_modules)
    
    # Test technical analysis
    print("\n📊 Technical Analysis:")
    ta_libs = []
    
    # Try TA-Lib first
    if test_import("talib", "TA-Lib"):
        ta_libs.append(True)
    else:
        # Try talib-binary
        if test_import("talib", "talib-binary"):
            ta_libs.append(True)
        else:
            ta_libs.append(False)
    
    ta_ok = any(ta_libs)
    
    # Test async dependencies
    print("\n⚡ Async Dependencies:")
    async_deps = [
        ("aiohttp", "aiohttp"),
        ("asyncio", "asyncio (built-in)")
    ]
    
    async_ok = all(test_import(module, name) for module, name in async_deps)
    
    # Test dashboard dependencies
    print("\n📈 Dashboard Dependencies:")
    dashboard_deps = [
        ("streamlit", "Streamlit"),
        ("plotly", "Plotly"),
        ("plotly.graph_objects", "Plotly Graph Objects"),
        ("plotly.express", "Plotly Express")
    ]
    
    dashboard_ok = all(test_import(module, name) for module, name in dashboard_deps)
    
    # Test monitoring dependencies
    print("\n🔍 Monitoring Dependencies:")
    monitor_deps = [
        ("colorlog", "Colorlog"),
        ("tqdm", "tqdm"),
        ("logging", "Logging (built-in)")
    ]
    
    monitor_ok = all(test_import(module, name) for module, name in monitor_deps)
    
    # Overall results
    print("\n" + "=" * 60)
    print("📊 INSTALLATION TEST RESULTS:")
    print("=" * 60)
    
    results = {
        "Basic Dependencies": basic_ok,
        "Machine Learning": ml_ok,
        "Scikit-learn Modules": sklearn_ok,
        "Technical Analysis": ta_ok,
        "Async Dependencies": async_ok,
        "Dashboard Dependencies": dashboard_ok,
        "Monitoring Dependencies": monitor_ok
    }
    
    all_passed = True
    for category, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{category:<25} {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("🎉 ALL TESTS PASSED! You can now run the advanced trading system.")
        print("\n🚀 Next Steps:")
        print("1. Run: streamlit run advanced_dashboard.py")
        print("2. Test ML features with your data")
        print("3. Integrate with your existing bot")
    else:
        print("⚠️  SOME TESTS FAILED. Please install missing dependencies.")
        print("\n🔧 Quick Fix Commands:")
        
        if not ml_ok or not sklearn_ok:
            print("pip install scikit-learn==1.3.0 joblib==1.3.0")
        
        if not ta_ok:
            print("pip install talib-binary==0.4.19")
        
        if not async_ok:
            print("pip install aiohttp==3.8.0")
        
        if not dashboard_ok:
            print("pip install streamlit==1.32.0 plotly==5.17.0")
        
        if not monitor_ok:
            print("pip install colorlog==6.7.0 tqdm==4.66.0")
    
    print("=" * 60)
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
