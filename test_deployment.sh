#!/bin/bash
# Quick deployment verification script

echo "🔍 Testing CORS Fix Deployment"
echo "================================"

SITE_URL="https://sntax.netlify.app"

echo "🌐 Testing site: $SITE_URL"

# Test if site loads
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$SITE_URL")
echo "📡 Site status: $HTTP_STATUS"

if [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ Site is accessible"
    
    # Check if our CORS fix is deployed
    if curl -s "$SITE_URL" | grep -q "v2024-01-17-fallback"; then
        echo "✅ CORS fix version detected - deployment successful!"
        echo "🎯 Expected console output:"
        echo "   🚀 ReportsManager initialized, version: v2024-01-17-fallback"
        echo "   API URL: https://bottie-1.onrender.com/api"
    else
        echo "⚠️  CORS fix not detected yet - deployment may still be processing"
    fi
else
    echo "❌ Site not accessible (Status: $HTTP_STATUS)"
fi

echo ""
echo "🧪 To verify CORS fix manually:"
echo "1. Open: $SITE_URL"  
echo "2. Press F12 → Console"
echo "3. Look for: '🚀 ReportsManager initialized'"
echo "4. Should NOT see CORS errors"
echo ""