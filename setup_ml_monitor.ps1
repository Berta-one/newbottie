# Bottie ML Monitor Installation Script for Windows PowerShell

Write-Host "🧠 Setting up Bottie ML Learning Monitor..." -ForegroundColor Cyan

# Create monitoring directory
Write-Host "📁 Creating monitoring directory..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "monitoring" | Out-Null
Set-Location "monitoring"

# Install Python dependencies
Write-Host "📦 Installing Python packages..." -ForegroundColor Yellow
pip install rich matplotlib requests numpy pandas

Write-Host "📄 Creating monitor files..." -ForegroundColor Yellow

# Create PowerShell scripts for Windows
@"
# Bottie ML Monitor - Live Dashboard
Write-Host "🚀 Starting Bottie ML Monitor..." -ForegroundColor Green
python ..\ml_monitor.py --continuous --api-url http://localhost:8000
"@ | Out-File -FilePath "start_monitor.ps1" -Encoding UTF8

@"
# Bottie ML Monitor - Generate Report
Write-Host "📊 Generating ML Learning Report..." -ForegroundColor Green
python ..\ml_monitor.py --report --api-url http://localhost:8000
"@ | Out-File -FilePath "generate_report.ps1" -Encoding UTF8

@"
# Bottie ML Monitor - Plot Trends
Write-Host "📈 Generating Trend Plots..." -ForegroundColor Green
python ..\ml_monitor.py --plot --save-plot ml_trends.png --api-url http://localhost:8000
"@ | Out-File -FilePath "plot_trends.ps1" -Encoding UTF8

# Create batch files for easier execution
@"
@echo off
echo 🚀 Starting Bottie ML Monitor...
python ..\ml_monitor.py --continuous --api-url http://localhost:8000
pause
"@ | Out-File -FilePath "start_monitor.bat" -Encoding ASCII

@"
@echo off
echo 📊 Generating ML Learning Report...
python ..\ml_monitor.py --report --api-url http://localhost:8000
pause
"@ | Out-File -FilePath "generate_report.bat" -Encoding ASCII

@"
@echo off
echo 📈 Generating Trend Plots...
python ..\ml_monitor.py --plot --save-plot ml_trends.png --api-url http://localhost:8000
pause
"@ | Out-File -FilePath "plot_trends.bat" -Encoding ASCII

Write-Host "✅ Installation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "🎯 Usage Options:" -ForegroundColor White
Write-Host "1. Live Dashboard:    .\start_monitor.bat (or .\start_monitor.ps1)" -ForegroundColor Cyan
Write-Host "2. Generate Report:   .\generate_report.bat (or .\generate_report.ps1)" -ForegroundColor Cyan
Write-Host "3. Plot Trends:       .\plot_trends.bat (or .\plot_trends.ps1)" -ForegroundColor Cyan
Write-Host "4. Direct Usage:      python ..\ml_monitor.py --continuous" -ForegroundColor Cyan
Write-Host ""
Write-Host "📝 Configuration:" -ForegroundColor White
Write-Host "- Edit API URL in scripts if not using localhost:8000" -ForegroundColor Gray
Write-Host "- Dashboard auto-refreshes every 30 seconds" -ForegroundColor Gray
Write-Host "- Reports saved to ml_learning_report.txt" -ForegroundColor Gray
Write-Host ""
Write-Host "🔧 Backend Requirements:" -ForegroundColor White
Write-Host "- /ml/status endpoint added to your API ✅" -ForegroundColor Green
Write-Host "- /metrics/components endpoint added to your API ✅" -ForegroundColor Green
Write-Host "- Ensure API runs on port 8000 or update scripts" -ForegroundColor Gray
Write-Host ""
Write-Host "🚀 Quick Start:" -ForegroundColor Yellow
Write-Host "   cd monitoring" -ForegroundColor White
Write-Host "   .\start_monitor.bat" -ForegroundColor White
