param (
    [string]$Path = ".",
    [string]$Extension = "*",
    [switch]$DryRun
)

$replacements = @{
    "❌" = "?"
    "✅" = "??"
    "✔" = "?"
    "£"  = "�"
    "€" = "�"
    "•" = "�"
    "—" = "�"
    "–" = "�"
    "”" = "�"
    "“" = "�"
    "‘" = "�"
    "’" = "�"
    "…" = "�"
    "🎯" = "??"
    "💷" = "??"
    "💸" = "??"
    "💰" = "??"
    "💹" = "??"
    "📆" = "??"
    "📝" = "??"
    "📍" = "??"
    "📏" = "??"
    "📐" = "??"
    "📁" = "??"
    "�?" = "??"
    "�?" = "??"
}

Write-Host "Scanning for *$Extension files in $Path..." -ForegroundColor Cyan

Get-ChildItem -Path $Path -Recurse -Include "*$Extension" -File | ForEach-Object {
    $filePath = $_.FullName
    $content = Get-Content $filePath -Raw
    $original = $content
    foreach ($bad in $replacements.Keys) {
        $content = $content -replace [regex]::Escape($bad), $replacements[$bad]
    }
    if ($content -ne $original) {
        if ($DryRun) {
            Write-Host "[DRY-RUN] Changes would be applied to: $filePath" -ForegroundColor Yellow
        } else {
            Set-Content $filePath -Value $content -Encoding UTF8
            Write-Host "[UPDATED] Fixed garbled symbols in: $filePath" -ForegroundColor Green
        }
    }
}

Write-Host "Operation complete." -ForegroundColor Cyan
