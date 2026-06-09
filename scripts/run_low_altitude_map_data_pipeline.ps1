param(
  [string]$ProjectRoot = "E:\supermap_project",
  [string]$InstallRoot = "E:\supermap_software\SuperMap iDesktopX 2025",
  [string]$IServerBaseUrl = "http://localhost:8090/iserver",
  [string]$BackendBaseUrl = "http://localhost:8000/api",
  [string]$AutoWorkspace = "supermap_file_root\demo_workspace_auto\low_altitude_demo.smwu",
  [string]$AutoDatasource = "supermap_file_root\demo_workspace_auto\low_altitude_demo.udbx",
  [switch]$OverwriteAutoWorkspace,
  [switch]$SkipWorkspaceBuild
)

$ErrorActionPreference = "Stop"

function Invoke-Step {
  param(
    [string]$Name,
    [scriptblock]$Body
  )

  Write-Host ""
  Write-Host "== $Name =="
  & $Body
  Write-Host "[OK] $Name"
}

if (-not (Test-Path -LiteralPath $ProjectRoot)) {
  throw "Project root not found: $ProjectRoot"
}

Set-Location $ProjectRoot

$summaryDir = Join-Path $ProjectRoot "docs\delivery"
New-Item -ItemType Directory -Force -Path $summaryDir | Out-Null
$summaryPath = Join-Path $summaryDir "low_altitude_map_data_pipeline_summary.json"

$startedAt = Get-Date
$steps = New-Object System.Collections.ArrayList
$script:startedJobs = @()

function Invoke-CheckedPowerShell {
  param([string[]]$Arguments)

  powershell @Arguments
  if ($LASTEXITCODE -ne 0) {
    throw "PowerShell child process failed with exit code ${LASTEXITCODE}: powershell $($Arguments -join ' ')"
  }
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
  Invoke-Step -Name "Export demo GeoJSON" -Body {
    Invoke-CheckedPowerShell -Arguments @("-ExecutionPolicy", "Bypass", "-File", (Join-Path $ProjectRoot "scripts\export_demo_geojson.ps1"))
    [void]$steps.Add("export_demo_geojson")
  }

  if (-not $SkipWorkspaceBuild) {
    Invoke-Step -Name "Build SuperMap workspace with iObjectSpy" -Body {
      $buildArgs = @(
        "-ExecutionPolicy", "Bypass",
        "-File", (Join-Path $ProjectRoot "scripts\build_low_altitude_workspace.ps1"),
        "-InstallRoot", $InstallRoot,
        "-ProjectRoot", $ProjectRoot,
        "-Workspace", $AutoWorkspace,
        "-Datasource", $AutoDatasource
      )
      if ($OverwriteAutoWorkspace) {
        $buildArgs += "-Overwrite"
      }
      Invoke-CheckedPowerShell -Arguments $buildArgs
      [void]$steps.Add("build_workspace_auto")
    }
  }
  else {
    Write-Host ""
    Write-Host "== Build SuperMap workspace with iObjectSpy =="
    Write-Host "[SKIP] SkipWorkspaceBuild specified"
    [void]$steps.Add("skip_workspace_build")
  }

  Invoke-Step -Name "Generate iServer service config draft" -Body {
    Invoke-CheckedPowerShell -Arguments @("-ExecutionPolicy", "Bypass", "-File", (Join-Path $ProjectRoot "scripts\export_iserver_low_altitude_service_config.ps1"), "-IncludeUnverified3D")
    [void]$steps.Add("export_iserver_config_draft")
  }

  Invoke-Step -Name "Render project map preview with iObjectSpy" -Body {
    Invoke-CheckedPowerShell -Arguments @("-ExecutionPolicy", "Bypass", "-File", (Join-Path $ProjectRoot "scripts\render_low_altitude_map_preview.ps1"), "-InstallRoot", $InstallRoot, "-ProjectRoot", $ProjectRoot)
    [void]$steps.Add("render_project_map_preview")
  }

  Invoke-Step -Name "Check low_altitude_demo publish readiness" -Body {
    Invoke-CheckedPowerShell -Arguments @("-ExecutionPolicy", "Bypass", "-File", (Join-Path $ProjectRoot "scripts\check_low_altitude_demo_publish_ready.ps1"), "-IServerBaseUrl", $IServerBaseUrl)
    [void]$steps.Add("check_publish_ready")
  }

  Invoke-Step -Name "Ensure backend service for REST gate" -Body {
    $backendHealth = $BackendBaseUrl.TrimEnd("/") -replace "/api$", ""
    $backendHealth = "$backendHealth/api/health"
    if (-not (Test-Url -Url $backendHealth)) {
      $pythonExe = "E:\anaconda\envs\supermap_nav\python.exe"
      if (-not (Test-Path -LiteralPath $pythonExe)) {
        throw "Backend is not running and Python executable was not found: $pythonExe"
      }
      $backendDir = Join-Path $ProjectRoot "backend"
      $backendPort = ([uri]($BackendBaseUrl.TrimEnd("/") -replace "/api$", "")).Port
      if ($backendPort -le 0) {
        $backendPort = 8000
      }
      Write-Host "[START] backend on port $backendPort"
      $backendJob = Start-Job -Name "low_altitude_pipeline_backend" -ScriptBlock {
        param($Dir, $Python, $Port)
        Set-Location $Dir
        & $Python -m uvicorn app.main:app --host 127.0.0.1 --port $Port
      } -ArgumentList $backendDir, $pythonExe, $backendPort
      $script:startedJobs += $backendJob
      Wait-Url -Url $backendHealth -TimeoutSeconds 35
    }
    else {
      Write-Host "[OK] backend already running"
    }
    [void]$steps.Add("ensure_backend_for_rest_gate")
  }

  Invoke-Step -Name "Verify SuperMap delivery REST gate" -Body {
    Invoke-CheckedPowerShell -Arguments @("-ExecutionPolicy", "Bypass", "-File", (Join-Path $ProjectRoot "scripts\check_supermap_delivery_gate.ps1"), "-IServerBaseUrl", $IServerBaseUrl, "-BackendBaseUrl", $BackendBaseUrl)
    [void]$steps.Add("check_delivery_gate")
  }
}
finally {
  foreach ($job in $script:startedJobs) {
    Stop-Job -Job $job -ErrorAction SilentlyContinue
    Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
  }
}

$summary = [ordered]@{
  started_at = $startedAt.ToString("s")
  finished_at = (Get-Date).ToString("s")
  project_root = $ProjectRoot
  auto_workspace = Join-Path $ProjectRoot $AutoWorkspace
  auto_datasource = Join-Path $ProjectRoot $AutoDatasource
  steps = $steps
  strict_status = "GeoJSON export, auto workspace build, iServer config draft, iObjectSpy map preview, backend config gate, and iServer REST gate completed. Existing iServer map/data publication is verified; creating or replacing publication entries still depends on iServer Admin/API/XML deployment."
}

$summary | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $summaryPath -Encoding UTF8

Write-Host ""
Write-Host "[PASS] low_altitude_demo map/data pipeline finished"
Write-Host "[OK] summary => $summaryPath"
