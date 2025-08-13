# Bottie API Health Check - Manual Commands
# Use these curl commands to test your API endpoints

# Replace YOUR_API_URL with your actual API URL (e.g., https://your-bot.herokuapp.com or http://localhost:8000)
API_URL="http://localhost:8000"

echo "🔍 Bottie API Health Check Commands"
echo "Replace \$API_URL with your actual URL"
echo

echo "1️⃣ BASIC HEALTH CHECK"
echo "curl -s \$API_URL/health | jq ."
echo "Expected: {\"ok\": true, \"sentiment\": {\"enabled\": true}}"
echo

echo "2️⃣ SENTIMENT SYSTEM CHECKS"
echo "# Health check (should show sentiment: {enabled: true})"
echo "curl -s \$API_URL/health | jq .sentiment"
echo
echo "# Sentiment scores (shows current sentiment for each asset)"
echo "curl -s \$API_URL/sentiment | jq ."
echo "Expected: {\"BTC\": {\"score\": 0.123, \"n\": 45}, \"ETH\": {...}}"
echo
echo "# Debug view (shows sample headlines being analyzed)"
echo "curl -s \$API_URL/sentiment/debug | jq .samples"
echo "Expected: {\"BTC\": [\"bitcoin hits new high...\", ...], \"ETH\": [...]}"
echo

echo "3️⃣ ML MONITORING CHECKS"
echo "# ML learning status"
echo "curl -s \$API_URL/ml/status | jq ."
echo "Expected: {\"sample_count\": 123, \"brier_score\": 0.21, \"accuracy\": 0.67, ...}"
echo
echo "# Advanced ML metrics"
echo "curl -s \$API_URL/metrics/components | jq ."
echo

echo "4️⃣ CROSS-PAIR TRADING CHECKS"
echo "# Cross-pair status"
echo "curl -s \$API_URL/cross-pairs/status | jq ."
echo
echo "# Available cross-pairs in portfolio"
echo "curl -s \$API_URL/portfolio/cross-pairs | jq ."
echo "Expected: {\"enabled\": true, \"total_assets\": 5, \"total_pairs\": 20, ...}"
echo
echo "# Current opportunities"
echo "curl -s \$API_URL/cross-pairs/opportunities | jq ."
echo
echo "# AI rebalancing suggestions"
echo "curl -s \$API_URL/portfolio/rebalancing-suggestions | jq ."
echo

echo "5️⃣ TRADING SIGNALS"
echo "# Enhanced signals (includes cross-pairs)"
echo "curl -s \$API_URL/signals | jq ."
echo

echo "🔍 TROUBLESHOOTING CHECKLIST"
echo "If endpoints fail:"
echo
echo "❌ Connection refused → API server not running"
echo "   Start your API: python api_app.py or python api/app.py"
echo
echo "❌ 404 Not Found → Endpoint not implemented"
echo "   Add ML/cross-pair endpoints to your API"
echo
echo "❌ 500 Internal Error → Check API logs"
echo "   Look for import errors or missing dependencies"
echo
echo "✅ Sentiment shows n=0 → Keywords not matching"
echo "   Check FINNHUB_API_KEY and keyword configuration"
echo
echo "✅ ML shows sample_count=0 → Need trading activity"
echo "   Wait for trades to generate training data"
echo
echo "✅ Cross-pair disabled → Missing API keys"
echo "   Set BINANCE_API_KEY, BINANCE_API_SECRET, CROSS_PAIR_ENABLED=1"
echo

echo "📋 QUICK VERIFICATION COMMANDS"
echo "# Check if API is running"
echo "curl -I \$API_URL/health"
echo
echo "# Get sentiment sample count only"
echo "curl -s \$API_URL/sentiment | jq 'to_entries | map(select(.value.n > 0)) | length'"
echo
echo "# Get ML sample count only"  
echo "curl -s \$API_URL/ml/status | jq .sample_count"
echo
echo "# Check if cross-pair is enabled"
echo "curl -s \$API_URL/portfolio/cross-pairs | jq .enabled"
echo

echo "🎯 EXPECTED LOG PATTERNS"
echo "In your API logs, you should see:"
echo "[Finnhub] BTC: 12 matches (kw=['bitcoin','btc','btc/usdt']...)"
echo "[Sentiment] BTC: added 12 texts (window=900s)"
echo "[ML] Updated features for sample 45"
echo "[CrossPair] Found 15 opportunities in portfolio"
