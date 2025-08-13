#!/bin/bash
# Bottie ML Monitor Installation Script

echo "🧠 Setting up Bottie ML Learning Monitor..."

# Create monitoring directory
mkdir -p monitoring
cd monitoring

# Install Python dependencies
echo "📦 Installing Python packages..."
pip install rich matplotlib requests numpy pandas

echo "📄 Creating monitor files..."

# Create quick start scripts
cat > start_monitor.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting Bottie ML Monitor..."
python ../ml_monitor.py --continuous --api-url http://localhost:8000
EOF

cat > generate_report.sh << 'EOF'
#!/bin/bash
echo "📊 Generating ML Learning Report..."
python ../ml_monitor.py --report --api-url http://localhost:8000
EOF

cat > plot_trends.sh << 'EOF'
#!/bin/bash
echo "📈 Generating Trend Plots..."
python ../ml_monitor.py --plot --save-plot ml_trends.png --api-url http://localhost:8000
EOF

# Make scripts executable
chmod +x *.sh

echo "✅ Installation complete!"
echo ""
echo "🎯 Usage Options:"
echo "1. Live Dashboard:    cd monitoring && ./start_monitor.sh"
echo "2. Generate Report:   cd monitoring && ./generate_report.sh" 
echo "3. Plot Trends:       cd monitoring && ./plot_trends.sh"
echo "4. Direct Usage:      python ml_monitor.py --continuous"
echo ""
echo "📝 Configuration:"
echo "- Edit API URL in scripts if not using localhost:8000"
echo "- Dashboard auto-refreshes every 30 seconds"
echo "- Reports saved to ml_learning_report.txt"
echo ""
echo "🔧 Backend Requirements:"
echo "- Add /ml/status endpoint to your API"
echo "- Optionally add /metrics/components endpoint"
echo "- Ensure API runs on port 8000 or update scripts"
echo ""
