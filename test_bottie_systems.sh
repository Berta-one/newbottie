#!/bin/bash
# Bottie System Health Check Script
# Tests all endpoints: health, sentiment, ML monitoring, and cross-pair trading

echo "🔍 Bottie System Health Check"
echo "============================="
echo

API_URL="${1:-http://localhost:8000}"
echo "🌐 Testing API at: $API_URL"
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to test endpoint
test_endpoint() {
    local name="$1"
    local endpoint="$2"
    local expected_key="$3"
    
    echo -n "🔸 Testing $name... "
    
    response=$(curl -s "$API_URL$endpoint" 2>/dev/null)
    if [ $? -eq 0 ]; then
        if [[ "$response" == *"$expected_key"* ]]; then
            echo -e "${GREEN}✅ PASS${NC}"
            if command -v jq &> /dev/null; then
                echo "$response" | jq . 2>/dev/null | head -10
            else
                echo "$response" | head -10
            fi
        else
            echo -e "${YELLOW}⚠️  PARTIAL${NC}"
            echo "   Response: $response"
        fi
    else
        echo -e "${RED}❌ FAIL${NC}"
        echo "   Could not connect to $API_URL$endpoint"
    fi
    echo
}

# Basic Health Check
echo "🏥 BASIC HEALTH CHECKS"
echo "====================="
test_endpoint "Basic Health" "/health" "ok"

# Sentiment System
echo "💭 SENTIMENT SYSTEM"
echo "=================="
test_endpoint "Sentiment Health" "/health" "sentiment"
test_endpoint "Sentiment Scores" "/sentiment" "score"
test_endpoint "Sentiment Debug" "/sentiment/debug" "samples"

# ML Monitoring
echo "🧠 ML MONITORING SYSTEM" 
echo "======================"
test_endpoint "ML Status" "/ml/status" "sample_count"
test_endpoint "ML Components" "/metrics/components" "performance"

# Cross-Pair Trading
echo "🔄 CROSS-PAIR TRADING"
echo "===================="
test_endpoint "Cross-Pair Status" "/cross-pairs/status" "enabled"
test_endpoint "Cross-Pair Opportunities" "/cross-pairs/opportunities" "opportunities"
test_endpoint "Portfolio Cross-Pairs" "/portfolio/cross-pairs" "portfolio_assets"
test_endpoint "Rebalancing Suggestions" "/portfolio/rebalancing-suggestions" "suggestions"

# Additional Tests
echo "📊 ADDITIONAL CHECKS"
echo "==================="
test_endpoint "Trading Signals" "/signals" "signals"
test_endpoint "System Status" "/status" "timestamp"

echo "🔍 DETAILED SENTIMENT CHECK"
echo "==========================="
echo "Checking for sentiment activity..."

# Check sentiment debug for actual data
echo -n "🔸 Sentiment keyword matching... "
sentiment_debug=$(curl -s "$API_URL/sentiment/debug" 2>/dev/null)
if echo "$sentiment_debug" | grep -q "samples"; then
    if command -v jq &> /dev/null; then
        sample_count=$(echo "$sentiment_debug" | jq -r '.samples | to_entries | length' 2>/dev/null)
        if [ "$sample_count" -gt 0 ]; then
            echo -e "${GREEN}✅ Found samples for $sample_count assets${NC}"
            echo "$sentiment_debug" | jq -r '.samples | to_entries[] | "   \(.key): \(.value | length) samples"' 2>/dev/null
        else
            echo -e "${YELLOW}⚠️  No samples found - check keywords/sources${NC}"
        fi
    else
        echo -e "${GREEN}✅ Response received${NC}"
    fi
else
    echo -e "${RED}❌ No sentiment data${NC}"
fi
echo

echo "🔍 DETAILED ML CHECK"
echo "==================="
echo -n "🔸 ML learning progress... "
ml_status=$(curl -s "$API_URL/ml/status" 2>/dev/null)
if echo "$ml_status" | grep -q "sample_count"; then
    if command -v jq &> /dev/null; then
        sample_count=$(echo "$ml_status" | jq -r '.sample_count // 0' 2>/dev/null)
        brier_score=$(echo "$ml_status" | jq -r '.brier_score // "null"' 2>/dev/null)
        quantum_rank=$(echo "$ml_status" | jq -r '.quantum_feature_rank // "null"' 2>/dev/null)
        
        echo -e "${GREEN}✅ Active${NC}"
        echo "   Sample Count: $sample_count"
        echo "   Brier Score: $brier_score"
        echo "   Quantum Rank: #$quantum_rank"
        
        if [ "$sample_count" -gt 50 ]; then
            echo -e "   ${GREEN}Good sample size for analysis${NC}"
        elif [ "$sample_count" -gt 0 ]; then
            echo -e "   ${YELLOW}Building sample size ($sample_count/50 minimum)${NC}"
        else
            echo -e "   ${YELLOW}No samples yet - need trading activity${NC}"
        fi
    else
        echo -e "${GREEN}✅ Response received${NC}"
    fi
else
    echo -e "${RED}❌ No ML data${NC}"
fi
echo

echo "🔍 CROSS-PAIR PORTFOLIO CHECK"
echo "============================="
echo -n "🔸 Portfolio discovery... "
portfolio_data=$(curl -s "$API_URL/portfolio/cross-pairs" 2>/dev/null)
if echo "$portfolio_data" | grep -q "portfolio_assets"; then
    if command -v jq &> /dev/null; then
        enabled=$(echo "$portfolio_data" | jq -r '.enabled // false' 2>/dev/null)
        asset_count=$(echo "$portfolio_data" | jq -r '.total_assets // 0' 2>/dev/null)
        pair_count=$(echo "$portfolio_data" | jq -r '.total_pairs // 0' 2>/dev/null)
        
        if [ "$enabled" = "true" ]; then
            echo -e "${GREEN}✅ Enabled${NC}"
            echo "   Portfolio Assets: $asset_count"
            echo "   Available Pairs: $pair_count"
            
            if [ "$asset_count" -gt 1 ]; then
                echo -e "   ${GREEN}Good portfolio diversity${NC}"
            else
                echo -e "   ${YELLOW}Need more assets for cross-pair trading${NC}"
            fi
        else
            echo -e "${YELLOW}⚠️  Disabled${NC}"
        fi
    else
        echo -e "${GREEN}✅ Response received${NC}"
    fi
else
    echo -e "${RED}❌ No portfolio data${NC}"
fi
echo

echo "📋 SUMMARY & RECOMMENDATIONS"
echo "============================"

# Generate recommendations based on test results
if curl -s "$API_URL/health" | grep -q "sentiment.*true"; then
    echo -e "${GREEN}✅ Sentiment system operational${NC}"
else
    echo -e "${YELLOW}⚠️  Check sentiment configuration and API keys${NC}"
fi

if curl -s "$API_URL/ml/status" | grep -q "sample_count"; then
    echo -e "${GREEN}✅ ML monitoring operational${NC}"
else
    echo -e "${YELLOW}⚠️  Check ML learner integration${NC}"
fi

if curl -s "$API_URL/portfolio/cross-pairs" | grep -q "enabled.*true"; then
    echo -e "${GREEN}✅ Cross-pair trading ready${NC}"
else
    echo -e "${YELLOW}⚠️  Check Binance API keys and portfolio${NC}"
fi

echo
echo "🚀 Quick Start Commands:"
echo "  View ML dashboard:     python ml_monitor.py --continuous"
echo "  Generate ML report:    python ml_monitor.py --report"
echo "  Test cross-pairs:      python cross_pair/portfolio_cross_trading.py"
echo
echo "📖 Integration guides in:"
echo "  ML Monitor:       ML_MONITOR_README.md"
echo "  Cross-Pair:       cross_pair/README.md"
