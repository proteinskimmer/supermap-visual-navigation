param(
  [string]$ProjectRoot = "E:\supermap_project",
  [string]$IServerBaseUrl = "http://localhost:8090/iserver",
  [string]$BackendBaseUrl = "http://localhost:8000/api",
  [string]$PythonExe = "E:\anaconda\envs\supermap_nav\python.exe",
  [switch]$SkipRuntime,
  [switch]$NoStartBackend,
  [switch]$Strict
)

$ErrorActionPreference = "Stop"

$screenshots = Join-Path $ProjectRoot "docs\delivery\screenshots"
$pending = New-Object System.Collections.ArrayList
$startedJobs = @()

function Add-Pending {
  param([string]$Message)
  [void]$pending.Add($Message)
  Write-Host "[PENDING] $Message"
}

function Assert-File {
  param(
    [string]$Path,
    [string]$Label,
    [int]$MinBytes = 20000,
    [switch]$PendingOnly
  )

  if (-not (Test-Path -LiteralPath $Path)) {
    if ($PendingOnly) {
      Add-Pending "$Label missing: $Path"
      return
    }
    throw "$Label missing: $Path"
  }

  $item = Get-Item -LiteralPath $Path
  if ($item.Length -lt $MinBytes) {
    if ($PendingOnly) {
      Add-Pending "$Label too small: $($item.Length) bytes, $Path"
      return
    }
    throw "$Label too small: $($item.Length) bytes, $Path"
  }

  Write-Host "[OK] $Label => $($item.Name), $($item.Length) bytes"
}

function Get-Json {
  param([string]$Url, [string]$Label)
  $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 10
  if ($response.StatusCode -ne 200) {
    throw "$Label returned HTTP $($response.StatusCode)"
  }
  Write-Host "[OK] $Label => HTTP 200"
  return $response.Content | ConvertFrom-Json
}

function Test-Url {
  param([string]$Url)
  try {
    $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3
    return $response.StatusCode -ge 200 -and $response.StatusCode -lt 500
  }
  catch {
    return $false
  }
}

function Wait-Url {
  param([string]$Url, [int]$TimeoutSeconds = 35)
  $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
  while ((Get-Date) -lt $deadline) {
    if (Test-Url -Url $Url) {
      Write-Host "[OK] $Url"
      return $true
    }
    Start-Sleep -Seconds 1
  }
  return $false
}

try {
Set-Location $ProjectRoot

Write-Host "== Screenshot evidence =="
Assert-File -Path (Join-Path $screenshots "frontend_supermap_workspace.png") -Label "frontend SuperMap workspace"
Assert-File -Path (Join-Path $screenshots "iserver_map_low_altitude_demo_map.png") -Label "map service page"
Assert-File -Path (Join-Path $screenshots "iserver_data_low_altitude_demo_datasets.png") -Label "data datasets page" -MinBytes 8000
Assert-File -Path (Join-Path $screenshots "iserver_3d_low_altitude_demo_scenes.png") -Label "3D-low_altitude_demo scenes page" -MinBytes 8000
Assert-File -Path (Join-Path $screenshots "low_altitude_demo_map_iobjectspy_preview.png") -Label "iObjectSpy map preview"
Assert-File -Path (Join-Path $screenshots "compat_cbd\frontend_supermap_workspace.png") -Label "3D-CBD compatibility frontend"

Assert-File -Path (Join-Path $screenshots "iserver_publish_success_admin.png") -Label "iServer logged-in publish success GUI screenshot" -PendingOnly
Assert-File -Path (Join-Path $screenshots "idesktopx_low_altitude_demo_map_layers.png") -Label "iDesktopX low_altitude_demo_map GUI screenshot" -PendingOnly

if (-not $SkipRuntime) {
  Write-Host ""
  Write-Host "== Runtime REST evidence =="

  $maps = Get-Json -Url "$IServerBaseUrl/services/map-low_altitude_demo/rest/maps.json" -Label "map-low_altitude_demo maps"
  $mapNames = @($maps | ForEach-Object { $_.name })
  if ($mapNames -notcontains "low_altitude_demo_map") {
    throw "map-low_altitude_demo missing low_altitude_demo_map"
  }
  Write-Host "[OK] low_altitude_demo_map listed"

  $mapMeta = Get-Json -Url "$IServerBaseUrl/services/map-low_altitude_demo/rest/maps/low_altitude_demo_map.json" -Label "low_altitude_demo_map metadata"
  if ($mapMeta.prjCoordSys.epsgCode -ne 4326) {
    throw "low_altitude_demo_map EPSG expected 4326, got $($mapMeta.prjCoordSys.epsgCode)"
  }
  Write-Host "[OK] low_altitude_demo_map EPSG => 4326"

  $datasets = Get-Json -Url "$IServerBaseUrl/services/data-low_altitude_demo/rest/data/datasources/low_altitude_demo/datasets.json" -Label "data-low_altitude_demo datasets"
  if ($datasets.datasetCount -ne 8) {
    throw "data-low_altitude_demo datasetCount expected 8, got $($datasets.datasetCount)"
  }
  Write-Host "[OK] data-low_altitude_demo datasetCount => 8"

  $scene = Get-Json -Url "$IServerBaseUrl/services/3D-low_altitude_demo/rest/realspace/scenes.json" -Label "3D-low_altitude_demo scenes"
  if (($scene | ConvertTo-Json -Depth 5) -notmatch "low_altitude_demo") {
    throw "3D-low_altitude_demo scenes payload missing low_altitude_demo"
  }
  Write-Host "[OK] 3D-low_altitude_demo contains low_altitude_demo"

  try {
    $backendRoot = $BackendBaseUrl.TrimEnd("/") -replace "/api$", ""
    $backendHealth = "$backendRoot/api/health"
    if (-not $NoStartBackend -and -not (Test-Url -Url $backendHealth)) {
      if (-not (Test-Path -LiteralPath $PythonExe)) {
        throw "Backend is not running and Python executable not found: $PythonExe"
      }
      $backendPort = ([uri]$backendRoot).Port
      if ($backendPort -le 0) {
        $backendPort = 8000
      }
      $backendDir = Join-Path $ProjectRoot "backend"
      Write-Host "[START] backend on port $backendPort"
      $backendJob = Start-Job -Name "supermap_goal_evidence_backend" -ScriptBlock {
        param($Dir, $Python, $Port)
        Set-Location $Dir
        & $Python -m uvicorn app.main:app --host 127.0.0.1 --port $Port
      } -ArgumentList $backendDir, $PythonExe, $backendPort
      $startedJobs += $backendJob
      if (-not (Wait-Url -Url $backendHealth -TimeoutSeconds 35)) {
        throw "Timed out waiting for backend health: $backendHealth"
      }
    }

    $services = Get-Json -Url "$BackendBaseUrl/supermap/services" -Label "backend /api/supermap/services"
    $serviceMap = @{}
    foreach ($svc in $services.data) {
      $serviceMap[$svc.id] = $svc
    }
    foreach ($id in @("scene", "map", "data")) {
      if ($serviceMap[$id].status -ne "verified") {
        throw "$id service status expected verified, got $($serviceMap[$id].status)"
      }
      Write-Host "[OK] backend service $id => verified"
    }
  }
  catch {
    Add-Pending "backend runtime check unavailable: $($_.Exception.Message)"
  }
}

Write-Host ""
if ($pending.Count -eq 0) {
  Write-Host "[PASS] SuperMap goal evidence is complete."
}
else {
  Write-Host "[PENDING] SuperMap goal evidence has $($pending.Count) pending item(s)."
  foreach ($item in $pending) {
    Write-Host " - $item"
  }
  if ($Strict) {
    exit 2
  }
}
}
finally {
  foreach ($job in $startedJobs) {
    Stop-Job -Job $job -ErrorAction SilentlyContinue
    Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
  }
}
