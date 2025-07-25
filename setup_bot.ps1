# ================================
# Cloudflare Tunnel + Streamlit Auto-Setup
# ================================

$CloudflarePath = "C:\tools\cloudflared\cloudflared.exe"
$TunnelName = "bot-dashboard"
$Domain = "bot.sntax.com"
$UserProfile = $env:USERPROFILE
$ConfigDir = "$UserProfile\.cloudflared"

Write-Host "Checking Cloudflared installation..."
if (!(Test-Path $CloudflarePath)) {
    Write-Host "cloudflared.exe not found at $CloudflarePath"
    exit
}

Write-Host "Cloudflared found. Proceeding..."

# 1. Get tunnel credentials file
$tunnelJson = Get-ChildItem -Path $ConfigDir -Filter "*.json" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (!$tunnelJson) {
    Write-Host "No tunnel JSON found. Make sure you ran 'cloudflared tunnel create $TunnelName'"
    exit
}

$tunnelId = $tunnelJson.BaseName
Write-Host "Found tunnel ID: $tunnelId"

# 2. Create config.yml
$configContent = @"
tunnel: $TunnelName
credentials-file: $ConfigDir\$tunnelId.json
ingress:
  - hostname: $Domain
    service: http://localhost:8501
  - service: http_status:404
"@

$configFile = "$ConfigDir\config.yml"
$configContent | Out-File -Encoding utf8 $configFile
Write-Host "Created config.yml at $configFile"

# 3. Install Cloudflared as a Windows Service
Write-Host "Installing Cloudflare Tunnel as a Windows Service..."
Start-Process -FilePath $CloudflarePath -ArgumentList "service install" -Wait
Write-Host "Cloudflare Tunnel is now running as a service!"

# 4. Install PM2 if missing
if (-not (Get-Command pm2 -ErrorAction SilentlyContinue)) {
    Write-Host "Installing PM2 globally..."
    npm install -g pm2
}

# 5. Create start-bot.bat for Streamlit
$batFile = "C:\tools\Bottie-main\start-bot.bat"
$batContent = "@echo off
cd /d C:\tools\Bottie-main
streamlit run hybrid_bot_fixed.py --server.port 8501 --server.address 0.0.0.0"
Set-Content -Path $batFile -Value $batContent -Encoding ASCII
Write-Host "Created start-bot.bat"

# 6. Start Streamlit app with PM2
Write-Host "Starting Streamlit app with PM2..."
pm2 delete bot-dashboard --silent
pm2 start "cmd.exe" --name bot-dashboard -- "/c $batFile"
pm2 save
Write-Host "Streamlit app added to PM2 (auto-restart enabled)"

# 7. Enable PM2 startup on Windows
Write-Host "Setting up PM2 to auto-start on boot..."
pm2-startup install
Write-Host "Setup complete!"

Write-Host ""
Write-Host "Access your bot at: https://$Domain"
