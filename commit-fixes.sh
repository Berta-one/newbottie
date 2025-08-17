#!/bin/bash

echo "🔧 Committing Real Data Only + Chart Fixes"
echo "=========================================="

# Add all changes
git add .

# Commit the fixes
git commit -m "Remove sample data, fix charts, real data only

MAJOR CHANGES:
✅ Remove all sample data generation - real data only
✅ Fix chart sizing - compact 256px height instead of full screen
✅ Fix JavaScript errors - resolved duplicate winRate declarations
✅ API-only report generation - no fallback to sample data
✅ Better error messages - inform users when APIs unavailable

CHART IMPROVEMENTS:
- Fixed height container (h-64 = 256px)
- Fewer data points (15 for trading, 8 for others)
- Smaller fonts (10-11px)
- Compact labels (T1, T2 instead of Trade 1, Trade 2)
- Responsive sizing with proper scaling

REAL DATA ONLY:
- Trading reports: Only from /api/trades endpoint
- ML reports: Only from /api/ml/performance endpoint  
- Backtest reports: Only from /api/backtest/run endpoint
- Sentiment reports: Only from /api/sentiment/analysis endpoint
- Portfolio reports: Only from /api/portfolio/overview endpoint
- No sample data fallbacks - shows empty state if no real data

ERROR HANDLING:
- Clear error messages when APIs unavailable
- Validation that data exists before creating reports
- Graceful handling of missing endpoints
- User-friendly error notifications

This ensures the tool only shows real trading data and analytics."

# Push to feature branch
git push origin cursor/build-a-netlify-report-visualization-tool-879b

echo ""
echo "✅ Changes committed to feature branch!"
echo ""
echo "🔀 Now merge to main with these commands:"
echo "   git checkout main"
echo "   git merge cursor/build-a-netlify-report-visualization-tool-879b"
echo "   git push origin main"
echo ""
echo "📊 After deployment, your dashboard will:"
echo "   - Only show real data from your APIs"
echo "   - Have compact, properly-sized charts"
echo "   - Display 'No reports found' if no real data available"
echo "   - Generate reports only from live trading system"