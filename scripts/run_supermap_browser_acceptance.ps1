param(
  [string]$PythonExe = "E:\anaconda\envs\supermap_nav\python.exe",
  [string]$BackendUrl = "http://localhost:8000",
  [string]$FrontendUrl = "http://localhost:5173",
  [string]$IServerBaseUrl = "http://localhost:8090/iserver",
  [int]$BackendPort = 8000,
  [int]$FrontendPort = 5173
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$BackendDir = Join-Path $ProjectRoot "backend"
$FrontendDir = Join-Path $ProjectRoot "frontend"
$startedJobs = @()

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
  param([string]$Url, [int]$TimeoutSeconds = 30)
  $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
  while ((Get-Date) -lt $deadline) {
    if (Test-Url -Url $Url) {
      Write-Host "[OK] $Url"
      return
    }
    Start-Sleep -Seconds 1
  }
  throw "Timed out waiting for $Url"
}

try {
  if (-not (Test-Path -LiteralPath $PythonExe)) {
    throw "Python executable not found: $PythonExe"
  }

  if (-not (Test-Url -Url "$BackendUrl/api/health")) {
    Write-Host "[START] backend on port $BackendPort"
    $backendJob = Start-Job -Name "supermap_acceptance_backend" -ScriptBlock {
      param($Dir, $Python, $Port)
      Set-Location $Dir
      & $Python -m uvicorn app.main:app --host 127.0.0.1 --port $Port
    } -ArgumentList $BackendDir, $PythonExe, $BackendPort
    $startedJobs += $backendJob
  }

  if (-not (Test-Url -Url $FrontendUrl)) {
    Write-Host "[START] frontend on port $FrontendPort"
    $frontendJob = Start-Job -Name "supermap_acceptance_frontend" -ScriptBlock {
      param($Dir, $Port)
      Set-Location $Dir
      $env:VITE_SCENE_PROVIDER = "supermap"
      Remove-Item Env:VITE_SUPERMAP_SCENE_URL -ErrorAction SilentlyContinue
      npm run dev -- --host 0.0.0.0 --port $Port
    } -ArgumentList $FrontendDir, $FrontendPort
    $startedJobs += $frontendJob
  }

  Wait-Url -Url "$BackendUrl/api/health" -TimeoutSeconds 35
  Wait-Url -Url $FrontendUrl -TimeoutSeconds 35
  Wait-Url -Url "$IServerBaseUrl/services/map-low_altitude_demo/rest/maps.json" -TimeoutSeconds 20

  powershell -ExecutionPolicy Bypass -File (Join-Path $ProjectRoot "scripts\check_supermap_delivery_gate.ps1") `
    -IServerBaseUrl $IServerBaseUrl `
    -BackendBaseUrl "$BackendUrl/api"

  powershell -ExecutionPolicy Bypass -File (Join-Path $ProjectRoot "scripts\capture_delivery_screenshots.ps1") -FrontendUrl $FrontendUrl

  Write-Host ""
  Write-Host "[PASS] SuperMap browser acceptance finished."
}
finally {
  foreach ($job in $startedJobs) {
    Stop-Job -Job $job -ErrorAction SilentlyContinue
    Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
  }
}
