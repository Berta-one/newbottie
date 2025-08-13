# Render Environment Variable Deployment Helper
# PowerShell script to assist with copying environment variables to Render

param(
    [Parameter(HelpMessage="Which solution to use: batch, json, or both")]
    [ValidateSet("batch", "json", "both")]
    [string]$Solution = "both",
    
    [Parameter(HelpMessage="Open files automatically for copying")]
    [switch]$OpenFiles
)

Write-Host "🚀 Render Environment Variable Deployment Helper" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green

function Show-BatchSolution {
    Write-Host "`n📦 BATCH SOLUTION (Recommended for large deployments)" -ForegroundColor Cyan
    Write-Host "Files created:"
    if (Test-Path "render_batch_1.env") { Write-Host "  ✅ render_batch_1.env" -ForegroundColor Green }
    if (Test-Path "render_batch_2.env") { Write-Host "  ✅ render_batch_2.env" -ForegroundColor Green }
    if (Test-Path "render_batch_3.env") { Write-Host "  ✅ render_batch_3.env" -ForegroundColor Green }
    if (Test-Path "render_batch_deployment.md") { Write-Host "  ✅ render_batch_deployment.md" -ForegroundColor Green }
    
    Write-Host "`nDeployment Steps:" -ForegroundColor Yellow
    Write-Host "1. Go to https://dashboard.render.com" -ForegroundColor White
    Write-Host "2. Select your Bottie service → Environment tab" -ForegroundColor White
    Write-Host "3. Copy variables from render_batch_1.env and paste (skip # comments)" -ForegroundColor White
    Write-Host "4. Repeat for render_batch_2.env and render_batch_3.env" -ForegroundColor White
    Write-Host "5. Save changes after each batch" -ForegroundColor White
    
    if ($OpenFiles) {
        Write-Host "`n📂 Opening batch files..." -ForegroundColor Yellow
        if (Test-Path "render_batch_1.env") { notepad "render_batch_1.env" }
        if (Test-Path "render_batch_2.env") { notepad "render_batch_2.env" }  
        if (Test-Path "render_batch_3.env") { notepad "render_batch_3.env" }
    }
}

function Show-JsonSolution {
    Write-Host "`n🔧 JSON SOLUTION (Recommended for simplicity)" -ForegroundColor Cyan
    Write-Host "Files created:"
    if (Test-Path "sentiment_json_config.env") { Write-Host "  ✅ sentiment_json_config.env" -ForegroundColor Green }
    if (Test-Path "sentiment_config.json") { Write-Host "  ✅ sentiment_config.json" -ForegroundColor Green }
    if (Test-Path "sentiment_json_usage.md") { Write-Host "  ✅ sentiment_json_usage.md" -ForegroundColor Green }
    
    Write-Host "`nDeployment Steps:" -ForegroundColor Yellow
    Write-Host "1. Go to https://dashboard.render.com" -ForegroundColor White
    Write-Host "2. Select your Bottie service → Environment tab" -ForegroundColor White
    Write-Host "3. Copy the SENTIMENT_CONFIG variable from sentiment_json_config.env" -ForegroundColor White
    Write-Host "4. Paste into Render Environment Variables" -ForegroundColor White
    Write-Host "5. Save changes" -ForegroundColor White
    Write-Host "6. Update your code to use JSON config (see sentiment_json_usage.md)" -ForegroundColor White
    
    if ($OpenFiles) {
        Write-Host "`n📂 Opening JSON files..." -ForegroundColor Yellow
        if (Test-Path "sentiment_json_config.env") { notepad "sentiment_json_config.env" }
        if (Test-Path "sentiment_json_usage.md") { notepad "sentiment_json_usage.md" }
    }
}

function Show-QuickCopy {
    Write-Host "`n⚡ QUICK COPY HELPERS" -ForegroundColor Magenta
    Write-Host "For Batch Solution:" -ForegroundColor Yellow
    Write-Host "  Get-Content render_batch_1.env | Where-Object { -not `$_.StartsWith('#') } | Set-Clipboard" -ForegroundColor Gray
    Write-Host "For JSON Solution:" -ForegroundColor Yellow  
    Write-Host "  Get-Content sentiment_json_config.env | Where-Object { -not `$_.StartsWith('#') } | Set-Clipboard" -ForegroundColor Gray
}

function Show-Verification {
    Write-Host "`n✅ VERIFICATION STEPS" -ForegroundColor Magenta
    Write-Host "After deployment, verify your setup:" -ForegroundColor Yellow
    Write-Host "1. Check Render Environment tab shows your variables" -ForegroundColor White
    Write-Host "2. Restart your Render service" -ForegroundColor White
    Write-Host "3. Test sentiment endpoints: https://bottie-1.onrender.com/sentiment/analyze" -ForegroundColor White
    Write-Host "4. Check application logs for any environment variable errors" -ForegroundColor White
}

# Main execution
switch ($Solution) {
    "batch" { Show-BatchSolution }
    "json" { Show-JsonSolution }
    "both" { 
        Show-BatchSolution
        Show-JsonSolution
    }
}

Show-QuickCopy
Show-Verification

Write-Host "`n🎉 Deployment helper complete!" -ForegroundColor Green
Write-Host "💡 Tip: Use -OpenFiles to automatically open relevant files" -ForegroundColor Yellow
Write-Host "💡 Tip: JSON solution is easier to manage long-term" -ForegroundColor Yellow
