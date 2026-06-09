param(
  [string]$FrontendUrl = "http://localhost:5173",
  [string]$ChromeExe = "C:\Program Files\Google\Chrome\Application\chrome.exe",
  [int]$VirtualTimeBudgetMs = 10000
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$profileDir = Join-Path $ProjectRoot ".tmp\chrome-luojia-dom-gate"
$domEvidencePath = Join-Path $ProjectRoot "docs\delivery\screenshots\frontend_luojia_scene_dom_evidence.html"

function Require-Contains {
  param([string]$Text, [string]$Pattern, [string]$Label)
  if (-not $Text.Contains($Pattern)) {
    throw "[FAIL] Missing ${Label}: $Pattern"
  }
  Write-Host "[OK] $Label"
}

if (-not (Test-Path -LiteralPath $ChromeExe)) {
  throw "Chrome executable not found: $ChromeExe"
}

New-Item -ItemType Directory -Force -Path $profileDir | Out-Null

Write-Host "== Luojia frontend DOM gate =="
Write-Host "[INFO] url: $FrontendUrl"

$chromeCommand = "`"$ChromeExe`" --headless=new --disable-gpu --no-sandbox --window-size=1600,1000 --virtual-time-budget=$VirtualTimeBudgetMs --user-data-dir=`"$profileDir`" --dump-dom `"$FrontendUrl`" > `"$domEvidencePath`" 2>nul"
cmd.exe /c $chromeCommand | Out-Null

$text = Get-Content -LiteralPath $domEvidencePath -Raw -Encoding UTF8
Set-Content -LiteralPath $domEvidencePath -Value $text -Encoding UTF8
Write-Host "[INFO] DOM evidence: $domEvidencePath"

Require-Contains -Text $text -Pattern "luojia-base-mount" -Label "Luojia scene mount class"
Require-Contains -Text $text -Pattern 'data-luojia-mode="true"' -Label "Luojia scene mode"
Require-Contains -Text $text -Pattern 'data-luojia-fallback-installed="true"' -Label "Luojia fallback installed"
Require-Contains -Text $text -Pattern 'data-luojia-terrain-installed="true"' -Label "DEM terrain mesh installed"
Require-Contains -Text $text -Pattern "/demo/luojia_ortho_preview.jpg" -Label "WebGL ortho fallback path"
Require-Contains -Text $text -Pattern 'data-scene-status="ready"' -Label "SuperMap viewer ready status"

$canvasMatches = [regex]::Matches($text, '<canvas[^>]*width="(?<width>\d+)"[^>]*height="(?<height>\d+)"')
if ($canvasMatches.Count -lt 1) {
  throw "[FAIL] SuperMap canvas not found"
}

$largestCanvas = $canvasMatches |
  ForEach-Object {
    [pscustomobject]@{
      Width = [int]$_.Groups["width"].Value
      Height = [int]$_.Groups["height"].Value
    }
  } |
  Sort-Object -Property @{ Expression = { $_.Width * $_.Height }; Descending = $true } |
  Select-Object -First 1

if ($largestCanvas.Width -le 0 -or $largestCanvas.Height -le 0) {
  throw "[FAIL] SuperMap canvas has invalid size: $($largestCanvas.Width)x$($largestCanvas.Height)"
}

Write-Host "[OK] SuperMap canvas size: $($largestCanvas.Width)x$($largestCanvas.Height)"
Write-Host "[PASS] Luojia frontend DOM gate verified."
