# generate_sentiment_for_render.ps1
# PowerShell helper script for generating sentiment variables for Render deployment

Write-Host "🧠 Sentiment Variables Generator for Bottie Render Deployment" -ForegroundColor Cyan
Write-Host "=" -repeat 65 -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python first." -ForegroundColor Red
    exit 1
}

# Options menu
Write-Host "Choose sentiment coverage option:" -ForegroundColor Yellow
Write-Host "1. Top 50 assets (testing/small deployment)" -ForegroundColor White
Write-Host "2. Top 100 assets (balanced coverage)" -ForegroundColor White  
Write-Host "3. Top 300 assets (production recommended)" -ForegroundColor Green
Write-Host "4. All assets (comprehensive, 400+ variables)" -ForegroundColor White
Write-Host "5. Custom amount" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Enter choice (1-5)"

switch ($choice) {
    "1" { $topByVolume = "50" }
    "2" { $topByVolume = "100" }
    "3" { $topByVolume = "300" }
    "4" { $topByVolume = "0" }
    "5" { 
        $topByVolume = Read-Host "Enter number of top assets (0 = all)"
        if (-not $topByVolume) { $topByVolume = "100" }
    }
    default { 
        Write-Host "Invalid choice. Using default (Top 100)" -ForegroundColor Yellow
        $topByVolume = "100" 
    }
}

# Include stablecoins option
$includeStables = Read-Host "Include stablecoins (USDT, USDC, etc.)? [y/N]"
$includeStablesFlag = if ($includeStables -match "^[yY]") { "1" } else { "0" }

Write-Host ""
Write-Host "🔄 Generating sentiment variables..." -ForegroundColor Cyan

# Set environment variables and run generator
$env:TOP_BY_VOLUME = $topByVolume
$env:INCLUDE_STABLES = $includeStablesFlag
$env:ONLY_SPOT = "1"

try {
    # Generate variables
    $output = python generate_all_sentiment_vars.py 2>&1
    $outputLines = $output -split "`n"
    $validLines = $outputLines | Where-Object { $_ -match "^SENTIMENT_KW_" }
    
    if ($validLines.Count -gt 0) {
        # Save to file
        $filename = "sentiment_render_vars.env"
        $validLines | Out-File -FilePath $filename -Encoding UTF8
        
        Write-Host "✅ Generated $($validLines.Count) sentiment variables" -ForegroundColor Green
        Write-Host "📁 Saved to: $filename" -ForegroundColor Cyan
        Write-Host ""
        
        # Show preview
        Write-Host "📋 Preview (first 5 variables):" -ForegroundColor Yellow
        Write-Host "-" -repeat 50 -ForegroundColor Gray
        $validLines | Select-Object -First 5 | ForEach-Object { Write-Host $_ -ForegroundColor White }
        if ($validLines.Count -gt 5) {
            Write-Host "... and $($validLines.Count - 5) more" -ForegroundColor Gray
        }
        
        Write-Host ""
        Write-Host "🚀 Ready for Render Deployment:" -ForegroundColor Green
        Write-Host "1. Copy contents of $filename" -ForegroundColor White
        Write-Host "2. Paste into Render → Environment Variables" -ForegroundColor White
        Write-Host "3. Deploy and test cross-pair trading with sentiment!" -ForegroundColor White
        
        # Optional: Check coverage
        Write-Host ""
        $checkCoverage = Read-Host "Check sentiment coverage against your live portfolio? [y/N]"
        if ($checkCoverage -match "^[yY]") {
            Write-Host "🔍 Checking sentiment coverage..." -ForegroundColor Cyan
            try {
                python check_sentiment_env.py --api https://bottie-1.onrender.com --env-file $filename --top $topByVolume --include-stables $includeStablesFlag
            } catch {
                Write-Host "⚠️ Coverage check failed. Install: pip install ccxt python-dotenv" -ForegroundColor Yellow
            }
        }
        
    } else {
        Write-Host "❌ No variables generated. Check if ccxt is installed: pip install ccxt" -ForegroundColor Red
    }
    
} catch {
    Write-Host "❌ Error running generator: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Try: pip install ccxt" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
