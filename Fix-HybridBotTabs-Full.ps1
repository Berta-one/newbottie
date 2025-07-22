# ============================================
# Fix-HybridBotTabs-Full.ps1
# ============================================

$Path = "hybrid_bot.py"
if (-not (Test-Path $Path)) {
    Write-Host "hybrid_bot.py not found. Run this from your project root." -ForegroundColor Red
    exit 1
}

# 1. Backup
$stamp = Get-Date -Format 'yyyyMMddHHmmss'
$BackupPath = "$Path.bak.$stamp"
Copy-Item $Path $BackupPath -Force
Write-Host "Backup created: $BackupPath" -ForegroundColor Green

# 2. Load file as single string
$txt = Get-Content $Path -Raw

# 3. Replace the st.tabs(...) label block with correct labels & icons
$newTabs = @'
tabs = st.tabs([
    "📈 Portfolio",       # 0 -> Portfolio Overview
    "✋ Manual Trading",   # 1 -> Manual Trading
    "🤖 Auto-Trader",      # 2 -> Auto-Trader Control
    "⚛ Multi-Strategy",   # 3 -> Multi-Strategy Market Scanner
    "⚙ Settings",         # 4 -> Trading Settings & Config
    "🔬 Backtesting",     # 5 -> BacktestingIntegration UI
    "📜 Logs"             # 6 -> Logs
])
'@

$txt = [regex]::Replace(
    $txt,
    'tabs\s*=\s*st\.tabs\s*\(\s*\[.*?\]\s*\)',
    $newTabs,
    [System.Text.RegularExpressions.RegexOptions]::Singleline
)

# 4. Remove *everything from the start of the "System Health Tab" comment onward*.
#    That section contains duplicate tabs[5], tabs[7], tabs[8] etc (causing IndexErrors).
$sysHealthPattern = '(?s)#\s*-+\s*\r?\n#\s*System Health Tab.*'  # matches comment header line and everything after
if ([regex]::IsMatch($txt, $sysHealthPattern)) {
    $txt = [regex]::Replace($txt, $sysHealthPattern, "`n# --- Removed legacy System Health / duplicate Backtesting / Analytics blocks ---`n")
}

# 5. Append clean Backtesting & Logs tabs (index 5 & 6)
$tail = @'
# =========================================================
# Backtesting Tab (clean)
# =========================================================
with tabs[5]:
    st.header("🔬 Backtesting")
    if "BACKTESTING_AVAILABLE" in globals() and BACKTESTING_AVAILABLE:
        try:
            if "backtesting_obj" not in st.session_state:
                from backtesting_integration import BacktestingIntegration
                st.session_state["backtesting_obj"] = BacktestingIntegration()
            st.session_state["backtesting_obj"].render_backtesting_tab()
        except Exception as e:
            st.error(f"Backtesting error: {e}")
    else:
        st.error("Backtesting unavailable - install dependencies.")
        st.code("pip install ccxt scipy", language="bash")

# =========================================================
# Logs Tab
# =========================================================
with tabs[6]:
    st.header("📜 System Logs")
    logs = st.session_state.get("logs", [])
    if logs:
        # show newest first
        for line in reversed(logs[-500:]):
            st.text(line)
    else:
        st.info("No logs yet.")
'@

$txt = $txt + "`n" + $tail + "`n"

# 6. Write file back
Set-Content -Path $Path -Value $txt -Encoding UTF8
Write-Host "✅ hybrid_bot.py fully repaired (tabs aligned, bad blocks removed, clean Backtesting & Logs added)." -ForegroundColor Green
