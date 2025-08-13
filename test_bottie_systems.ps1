# Bottie System Health Check Script (PowerShell)
# Tests all endpoints: health, sentiment, ML monitoring, and cross-pair trading

param(
    [string]$ApiUrl = "http://localhost:8000"
)

Write-Host "🔍 Bottie System Health Check" -ForegroundColor Cyan
Write-Host "=============================" -ForegroundColor Cyan
Write-Host

Write-Host "🌐 Testing API at: $ApiUrl" -ForegroundColor Blue
Write-Host

# Function to test endpoint
function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Endpoint,
        [string]$ExpectedKey
    )
    
    Write-Host "🔸 Testing $Name... " -NoNewline
    
    try {
        $response = Invoke-RestMethod -Uri "$ApiUrl$Endpoint" -Method GET -TimeoutSec 10 -ErrorAction Stop
        $responseText = $response | ConvertTo-Json -Depth 10
        
        if ($responseText -like "*$ExpectedKey*") {
            Write-Host "✅ PASS" -ForegroundColor Green
            if (Get-Command jq -ErrorAction SilentlyContinue) {
                $responseText | jq . | Select-Object -First 10
            } else {
                $responseText | Select-Object -First 10
            }
        } else {
            Write-Host "⚠️  PARTIAL" -ForegroundColor Yellow
            Write-Host "   Response: $responseText"
        }
    }
    catch {
        Write-Host "❌ FAIL" -ForegroundColor Red
        Write-Host "   Could not connect to $ApiUrl$Endpoint"
        Write-Host "   Error: $($_.Exception.Message)"
    }
    Write-Host
}

# Basic Health Check
Write-Host "🏥 BASIC HEALTH CHECKS" -ForegroundColor Yellow
Write-Host "=====================" -ForegroundColor Yellow
Test-Endpoint "Basic Health" "/health" "ok"

# Sentiment System
Write-Host "💭 SENTIMENT SYSTEM" -ForegroundColor Yellow
Write-Host "==================" -ForegroundColor Yellow
Test-Endpoint "Sentiment Health" "/health" "sentiment"
Test-Endpoint "Sentiment Scores" "/sentiment" "score"
Test-Endpoint "Sentiment Debug" "/sentiment/debug" "samples"

# ML Monitoring
Write-Host "🧠 ML MONITORING SYSTEM" -ForegroundColor Yellow
Write-Host "======================" -ForegroundColor Yellow
Test-Endpoint "ML Status" "/ml/status" "sample_count"
Test-Endpoint "ML Components" "/metrics/components" "performance"

# Cross-Pair Trading
Write-Host "🔄 CROSS-PAIR TRADING" -ForegroundColor Yellow
Write-Host "=====================" -ForegroundColor Yellow
Test-Endpoint "Cross-Pair Status" "/cross-pairs/status" "enabled"
Test-Endpoint "Cross-Pair Opportunities" "/cross-pairs/opportunities" "opportunities"
Test-Endpoint "Portfolio Cross-Pairs" "/portfolio/cross-pairs" "portfolio_assets"
Test-Endpoint "Rebalancing Suggestions" "/portfolio/rebalancing-suggestions" "suggestions"

# Additional Tests
Write-Host "📊 ADDITIONAL CHECKS" -ForegroundColor Yellow
Write-Host "===================" -ForegroundColor Yellow
Test-Endpoint "Trading Signals" "/signals" "signals"
Test-Endpoint "System Status" "/status" "timestamp"

# Detailed Sentiment Check
Write-Host "🔍 DETAILED SENTIMENT CHECK" -ForegroundColor Yellow
Write-Host "===========================" -ForegroundColor Yellow
Write-Host "Checking for sentiment activity..."

Write-Host "🔸 Sentiment keyword matching... " -NoNewline
try {
    $sentimentDebug = Invoke-RestMethod -Uri "$ApiUrl/sentiment/debug" -Method GET -TimeoutSec 10
    if ($sentimentDebug.samples) {
        $sampleCount = ($sentimentDebug.samples | Get-Member -MemberType NoteProperty).Count
        if ($sampleCount -gt 0) {
            Write-Host "✅ Found samples for $sampleCount assets" -ForegroundColor Green
            foreach ($asset in ($sentimentDebug.samples | Get-Member -MemberType NoteProperty).Name) {
                $count = $sentimentDebug.samples.$asset.Count
                Write-Host "   $asset`: $count samples"
            }
        } else {
            Write-Host "⚠️  No samples found - check keywords/sources" -ForegroundColor Yellow
        }
    } else {
        Write-Host "⚠️  No samples found" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "❌ No sentiment data" -ForegroundColor Red
}
Write-Host

# Detailed ML Check
Write-Host "🔍 DETAILED ML CHECK" -ForegroundColor Yellow
Write-Host "===================" -ForegroundColor Yellow
Write-Host "🔸 ML learning progress... " -NoNewline
try {
    $mlStatus = Invoke-RestMethod -Uri "$ApiUrl/ml/status" -Method GET -TimeoutSec 10
    if ($null -ne $mlStatus.sample_count) {
        Write-Host "✅ Active" -ForegroundColor Green
        Write-Host "   Sample Count: $($mlStatus.sample_count)"
        Write-Host "   Brier Score: $($mlStatus.brier_score)"
        Write-Host "   Quantum Rank: #$($mlStatus.quantum_feature_rank)"
        
        if ($mlStatus.sample_count -gt 50) {
            Write-Host "   Good sample size for analysis" -ForegroundColor Green
        } elseif ($mlStatus.sample_count -gt 0) {
            Write-Host "   Building sample size ($($mlStatus.sample_count)/50 minimum)" -ForegroundColor Yellow
        } else {
            Write-Host "   No samples yet - need trading activity" -ForegroundColor Yellow
        }
    } else {
        Write-Host "⚠️  No sample data" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "❌ No ML data" -ForegroundColor Red
}
Write-Host

# Cross-Pair Portfolio Check
Write-Host "🔍 CROSS-PAIR PORTFOLIO CHECK" -ForegroundColor Yellow
Write-Host "=============================" -ForegroundColor Yellow
Write-Host "🔸 Portfolio discovery... " -NoNewline
try {
    $portfolioData = Invoke-RestMethod -Uri "$ApiUrl/portfolio/cross-pairs" -Method GET -TimeoutSec 10
    if ($portfolioData.enabled -eq $true) {
        Write-Host "✅ Enabled" -ForegroundColor Green
        Write-Host "   Portfolio Assets: $($portfolioData.total_assets)"
        Write-Host "   Available Pairs: $($portfolioData.total_pairs)"
        
        if ($portfolioData.total_assets -gt 1) {
            Write-Host "   Good portfolio diversity" -ForegroundColor Green
        } else {
            Write-Host "   Need more assets for cross-pair trading" -ForegroundColor Yellow
        }
    } else {
        Write-Host "⚠️  Disabled" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "❌ No portfolio data" -ForegroundColor Red
}
Write-Host

# Summary
Write-Host "📋 SUMMARY & RECOMMENDATIONS" -ForegroundColor Yellow
Write-Host "============================" -ForegroundColor Yellow

try {
    $health = Invoke-RestMethod -Uri "$ApiUrl/health" -Method GET -TimeoutSec 10
    if ($health.sentiment -eq $true) {
        Write-Host "✅ Sentiment system operational" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Check sentiment configuration and API keys" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "⚠️  Check sentiment configuration and API keys" -ForegroundColor Yellow
}

try {
    $mlStatus = Invoke-RestMethod -Uri "$ApiUrl/ml/status" -Method GET -TimeoutSec 10
    if ($null -ne $mlStatus.sample_count) {
        Write-Host "✅ ML monitoring operational" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Check ML learner integration" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "⚠️  Check ML learner integration" -ForegroundColor Yellow
}

try {
    $crossPair = Invoke-RestMethod -Uri "$ApiUrl/portfolio/cross-pairs" -Method GET -TimeoutSec 10
    if ($crossPair.enabled -eq $true) {
        Write-Host "✅ Cross-pair trading ready" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Check Binance API keys and portfolio" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "⚠️  Check Binance API keys and portfolio" -ForegroundColor Yellow
}

Write-Host
Write-Host "🚀 Quick Start Commands:" -ForegroundColor Cyan
Write-Host "  View ML dashboard:     python ml_monitor.py --continuous"
Write-Host "  Generate ML report:    python ml_monitor.py --report"
Write-Host "  Test cross-pairs:      python cross_pair/portfolio_cross_trading.py"
Write-Host
Write-Host "📖 Integration guides in:" -ForegroundColor Cyan
Write-Host "  ML Monitor:       ML_MONITOR_README.md"
Write-Host "  Cross-Pair:       cross_pair/README.md"
