#!/bin/bash
echo "🚀 Checking Render deployment status..."
echo "========================================="

while true; do
    echo "$(date): Checking https://bottie-1.onrender.com/"
    
    # Check for enhanced dashboard
    if curl -s https://bottie-1.onrender.com/ | grep -q "Enhanced Dashboard v2.0"; then
        echo "✅ SUCCESS: Enhanced Dashboard v2.0 is LIVE!"
        echo "🎉 Visit: https://bottie-1.onrender.com/"
        break
    else
        echo "⏳ Still deploying... (checking again in 30 seconds)"
        sleep 30
    fi
done
