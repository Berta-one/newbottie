# CRYPTO DASHBOARD STARTUP SCRIPT
# Save this as: start_crypto_dashboard.ps1

Get-Job -Name "dashboard-*" -ErrorAction SilentlyContinue | Stop-Job
Get-Job -Name "dashboard-*" -ErrorAction SilentlyContinue | Remove-Job

Set-Location "C:\tools\Bottie-main"

$job = Start-Job -Name "dashboard-main" -ScriptBlock {
    Set-Location "C:\tools\Bottie-main"
    & "C:\Users\luigi\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\LocalCache\local-packages\Python311\Scripts\streamlit.exe" run hybrid_bot_fixed.py --server.port 8501 --server.address 0.0.0.0
}

Write-Host "✅ Crypto Dashboard started as job: $($job.Id)"
Write-Host "🌐 Access at: http://localhost:8501"
