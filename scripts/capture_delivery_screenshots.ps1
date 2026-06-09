param(
  [string]$Chrome = "C:\Program Files\Google\Chrome\Application\chrome.exe",
  [string]$OutputDir = "docs\delivery\screenshots",
  [string]$FrontendUrl = "http://localhost:5173/",
  [int]$Width = 1440,
  [int]$Height = 1000,
  [int]$VirtualTimeBudgetMs = 12000
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectRoot

if (-not (Test-Path -LiteralPath $Chrome)) {
  $fallback = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
  if (Test-Path -LiteralPath $fallback) {
    $Chrome = $fallback
  }
  else {
    throw "No Chrome/Edge executable found."
  }
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$resolvedOutput = Resolve-Path -LiteralPath $OutputDir

$targets = @(
  @{
    Name = "frontend_supermap_workspace.png"
    Url = $FrontendUrl
  },
  @{
    Name = "iserver_services_list.png"
    Url = "http://localhost:8090/iserver/services"
  },
  @{
    Name = "iserver_map_low_altitude_demo_map.png"
    Url = "http://localhost:8090/iserver/services/map-low_altitude_demo/rest/maps/low_altitude_demo_map"
  },
  @{
    Name = "iserver_map_low_altitude_demo_map_json.png"
    Url = "http://localhost:8090/iserver/services/map-low_altitude_demo/rest/maps/low_altitude_demo_map.json"
  },
  @{
    Name = "iserver_data_low_altitude_demo_datasets.png"
    Url = "http://localhost:8090/iserver/services/data-low_altitude_demo/rest/data/datasources/low_altitude_demo/datasets.json"
  },
  @{
    Name = "iserver_3d_cbd_scenes.png"
    Url = "http://localhost:8090/iserver/services/3D-CBD/rest/realspace/scenes.json"
  },
  @{
    Name = "iserver_3d_low_altitude_demo_scenes.png"
    Url = "http://localhost:8090/iserver/services/3D-low_altitude_demo/rest/realspace/scenes.json"
  },
  @{
    Name = "iserver_publish_services_admin_attempt.png"
    Url = "http://localhost:8090/iserver/admin-ui/services/serviceManagement/publishServices"
  }
)

foreach ($target in $targets) {
  $outputPath = Join-Path $resolvedOutput $target.Name
  $backupPath = "$outputPath.bak"
  Remove-Item -LiteralPath $backupPath -ErrorAction SilentlyContinue
  if (Test-Path -LiteralPath $outputPath) {
    Move-Item -LiteralPath $outputPath -Destination $backupPath -Force
  }
  Remove-Item -LiteralPath $outputPath -ErrorAction SilentlyContinue
  $args = @(
    "--headless",
    "--no-sandbox",
    "--disable-gpu",
    "--disable-gpu-compositing",
    "--disable-software-rasterizer",
    "--disable-dev-shm-usage",
    "--disable-features=VizDisplayCompositor",
    "--hide-scrollbars",
    "--window-size=$Width,$Height",
    "--virtual-time-budget=$VirtualTimeBudgetMs",
    "--screenshot=$outputPath",
    $target.Url
  )
  Write-Host "[CAPTURE] $($target.Url)"
  & $Chrome @args | Out-Host
  if (-not (Test-Path -LiteralPath $outputPath)) {
    if (Test-Path -LiteralPath $backupPath) {
      Move-Item -LiteralPath $backupPath -Destination $outputPath -Force
    }
    throw "Screenshot not created: $outputPath"
  }
  Remove-Item -LiteralPath $backupPath -ErrorAction SilentlyContinue
  $item = Get-Item -LiteralPath $outputPath
  Write-Host "[OK] $($item.Name) => $($item.Length) bytes"
}

Write-Host ""
Write-Host "[PASS] Screenshots saved to $resolvedOutput"
