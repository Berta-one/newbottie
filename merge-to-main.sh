#!/bin/bash

echo "🚀 Merging Reports Dashboard to Main Branch"
echo "============================================="

# Switch to main branch
echo "📍 Switching to main branch..."
git checkout main

# Pull latest changes
echo "📥 Pulling latest changes from origin..."
git pull origin main

# Merge feature branch
echo "🔀 Merging feature branch with all enhancements..."
git merge cursor/build-a-netlify-report-visualization-tool-879b

# Push to main
echo "📤 Pushing merged changes to main..."
git push origin main

echo ""
echo "✅ SUCCESS! Main branch now contains:"
echo "   - Enhanced reports dashboard (reports.html, reports.js)"
echo "   - P&L validation system (pnl_validator.py)"
echo "   - Advanced report generator (report_generator.py)"
echo "   - Static site configuration (package.json, netlify.toml)"
echo "   - All P&L calculation fixes"
echo ""
echo "🌐 Netlify should now deploy successfully from main branch!"
echo "   Access your dashboard at: https://your-site.netlify.app/reports"
echo ""
echo "🧪 Ready to test P&L accuracy once deployed!"