param(
  [string]$FrontendUrl = "http://localhost:5173",
  [string]$ChromeExe = "C:\Program Files\Google\Chrome\Application\chrome.exe",
  [string]$ScreenshotPath = "E:\supermap_project\docs\delivery\screenshots\frontend_luojia_scene_headless.png",
  [int]$VirtualTimeBudgetMs = 12000,
  [int]$Width = 1600,
  [int]$Height = 1000
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$profileDir = Join-Path $ProjectRoot ".tmp\chrome-luojia-visual-gate"

if (-not (Test-Path -LiteralPath $ChromeExe)) {
  throw "Chrome executable not found: $ChromeExe"
}

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $ScreenshotPath) | Out-Null
New-Item -ItemType Directory -Force -Path $profileDir | Out-Null
Remove-Item -LiteralPath $ScreenshotPath -Force -ErrorAction SilentlyContinue

Write-Host "== Luojia frontend visual gate =="
Write-Host "[INFO] url: $FrontendUrl"
Write-Host "[INFO] screenshot: $ScreenshotPath"

$chromeCommand = "`"$ChromeExe`" --headless=new --disable-gpu --no-sandbox --run-all-compositor-stages-before-draw --virtual-time-budget=$VirtualTimeBudgetMs --window-size=$Width,$Height --user-data-dir=`"$profileDir`" --screenshot=`"$ScreenshotPath`" `"$FrontendUrl`""
cmd.exe /c $chromeCommand

if (-not (Test-Path -LiteralPath $ScreenshotPath)) {
  throw "[FAIL] Screenshot was not created"
}

$file = Get-Item -LiteralPath $ScreenshotPath
if ($file.Length -lt 50000) {
  throw "[FAIL] Screenshot is too small: $($file.Length) bytes"
}
Write-Host "[OK] screenshot saved: $($file.Length) bytes"

Add-Type -AssemblyName System.Drawing
$bitmap = [System.Drawing.Bitmap]::FromFile($ScreenshotPath)
try {
  $regions = @{
    full = @(0, 0, $bitmap.Width, $bitmap.Height)
    scene = @([int]($bitmap.Width * 0.25), [int]($bitmap.Height * 0.12), [int]($bitmap.Width * 0.5), [int]($bitmap.Height * 0.68))
  }

  foreach ($name in $regions.Keys) {
    $r = $regions[$name]
    $sumR = 0
    $sumG = 0
    $sumB = 0
    $count = 0
    $nonDark = 0
    $step = 8
    for ($y = $r[1]; $y -lt ($r[1] + $r[3]); $y += $step) {
      for ($x = $r[0]; $x -lt ($r[0] + $r[2]); $x += $step) {
        $color = $bitmap.GetPixel($x, $y)
        $sumR += $color.R
        $sumG += $color.G
        $sumB += $color.B
        $count += 1
        if (($color.R + $color.G + $color.B) -gt 75) {
          $nonDark += 1
        }
      }
    }

    $meanR = [math]::Round($sumR / $count, 2)
    $meanG = [math]::Round($sumG / $count, 2)
    $meanB = [math]::Round($sumB / $count, 2)
    $nonDarkPct = [math]::Round(100 * $nonDark / $count, 2)
    Write-Host "[OK] $name mean=($meanR,$meanG,$meanB) nonDarkPct=$nonDarkPct"

    if ($nonDarkPct -lt 15) {
      throw "[FAIL] $name region appears too dark"
    }
  }
}
finally {
  $bitmap.Dispose()
}

Write-Host "[PASS] Luojia frontend visual gate verified."
