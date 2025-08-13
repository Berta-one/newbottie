@echo off
echo 🏛️ BOTTIE PROFESSIONAL TRADING SYSTEM
echo =====================================
echo ✅ All dashboard issues resolved
echo 🔥 NEW: Professional Trading Grid implemented!
echo.
echo 📊 Features:
echo   • Portfolio holdings (Y) vs Top 50 volume cryptos (X)
echo   • Up to 300 cross-pair combinations
echo   • Live Binance volume data
echo   • WebSocket-optimized performance
echo   • ALL crypto-to-crypto atomic swaps (not just USDT)
echo.
echo 🌐 Starting server...
python -m uvicorn api.app:app --host 0.0.0.0 --port 8000
