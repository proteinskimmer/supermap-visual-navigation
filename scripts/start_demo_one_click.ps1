param(
  [string]$ProjectRoot = "E:\supermap_project",
  [string]$IServerRoot = "E:\supermap_software\supermap-iserver-2025u1a-windows-x64-all",
  [int]$BackendPort = 8000,
  [int]$FrontendPort = 5173,
  [switch]$NoBrowser,
  [switch]$VerifyEvidence
)

$ErrorActionPreference = "Stop"

$stateDir = Join-Path $ProjectRoot ".tmp\demo_runtime"
$backendPidFile = Join-Path $stateDir "backend.pid"
$frontendPidFile = Join-Path $stateDir "frontend.pid"
$iserverPidFile = Join-Path $stateDir "iserver_launcher.pid"
$backendOutLog = Join-Path $stateDir "backend.out.log"
$backendErrLog = Join-Path $stateDir "backend.err.log"
$frontendOutLog = Join-Path $stateDir "frontend.out.log"
$frontendErrLog = Join-Path $stateDir "frontend.err.log"

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

function Test-BackendNavigationRoute {
  param([int]$Port)
  try {
    Invoke-WebRequest `
      -Uri "http://localhost:$Port/api/navigation/start" `
      -UseBasicParsing `
      -Method Post `
      -ContentType "application/json" `
      -Body "{}" `
      -TimeoutSec 3 | Out-Null
    return $true
  }
  catch {
    if ($_.Exception.Response) {
      $statusCode = [int]$_.Exception.Response.StatusCode
      return $statusCode -eq 422
    }
    return $false
  }
}

function Wait-Url {
  param([string]$Url, [int]$TimeoutSeconds = 60)
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

function Get-LogTail {
  param([string[]]$Paths)
  $chunks = @()
  foreach ($path in $Paths) {
    if (Test-Path -LiteralPath $path) {
      $tail = Get-Content -LiteralPath $path -Tail 40 -ErrorAction SilentlyContinue
      if ($tail) {
        $chunks += "----- $path -----"
        $chunks += $tail
      }
    }
  }
  return ($chunks -join [Environment]::NewLine)
}

function Test-PidFileAlive {
  param([string]$PidFile)
  if (-not (Test-Path -LiteralPath $PidFile)) {
    return $false
  }
  $pidValue = Get-Content -LiteralPath $PidFile -ErrorAction SilentlyContinue | Select-Object -First 1
  if (-not ($pidValue -and ($pidValue -as [int]))) {
    return $false
  }
  return [bool](Get-Process -Id ([int]$pidValue) -ErrorAction SilentlyContinue)
}

function Confirm-NewServiceStable {
  param(
    [string]$Name,
    [string]$Url,
    [string]$PidFile,
    [string[]]$LogPaths
  )

  Start-Sleep -Seconds 3
  $stable = $false
  $deadline = (Get-Date).AddSeconds(15)
  while ((Get-Date) -lt $deadline) {
    if (Test-Url -Url $Url) {
      $stable = $true
      break
    }
    Start-Sleep -Seconds 1
  }
  if (-not $stable) {
    $logTail = Get-LogTail -Paths $LogPaths
    throw "$Name started but became unreachable: $Url`n$logTail"
  }
  if (-not (Test-PidFileAlive -PidFile $PidFile)) {
    $logTail = Get-LogTail -Paths $LogPaths
    throw "$Name startup process exited unexpectedly.`n$logTail"
  }
  Write-Host "[OK] $Name stayed healthy after startup"
}

function Start-HiddenPowerShell {
  param(
    [string]$Command,
    [string]$WorkingDirectory,
    [string]$PidFile,
    [string]$StdoutLog,
    [string]$StderrLog
  )

  Remove-Item -LiteralPath $StdoutLog, $StderrLog -Force -ErrorAction SilentlyContinue
  $runnerFile = [System.IO.Path]::ChangeExtension($PidFile, ".runner.ps1")
  $workingLiteral = $WorkingDirectory.Replace("'", "''")
  $stdoutLiteral = $StdoutLog.Replace("'", "''")
  $runner = @"
`$ErrorActionPreference = "Stop"
Set-Location '$workingLiteral'
Start-Transcript -LiteralPath '$stdoutLiteral' -Force | Out-Null
try {
  $Command
}
finally {
  Stop-Transcript | Out-Null
}
"@
  Set-Content -LiteralPath $runnerFile -Value $runner -Encoding UTF8

  $process = Start-Process `
    -FilePath "powershell.exe" `
    -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $runnerFile) `
    -WorkingDirectory $WorkingDirectory `
    -WindowStyle Hidden `
    -PassThru

  Set-Content -LiteralPath $PidFile -Value $process.Id -Encoding ASCII
  return $process
}

if (-not (Test-Path -LiteralPath $ProjectRoot)) {
  throw "Project root not found: $ProjectRoot"
}

New-Item -ItemType Directory -Force -Path $stateDir | Out-Null
Set-Location $ProjectRoot

Write-Host "== Low Altitude SuperMap Demo =="
Write-Host "[INFO] Project root: $ProjectRoot"

if ($VerifyEvidence) {
  Write-Host ""
  Write-Host "== Verify evidence gate =="
  powershell -ExecutionPolicy Bypass -File (Join-Path $ProjectRoot "scripts\check_supermap_goal_evidence.ps1") -Strict
}

Write-Host ""
Write-Host "== iServer =="
$iserverUrl = "http://localhost:8090/iserver"
if (Test-Url -Url $iserverUrl) {
  Write-Host "[OK] iServer already running: $iserverUrl"
}
else {
  $startup = Join-Path $IServerRoot "bin\startup.bat"
  if (-not (Test-Path -LiteralPath $startup)) {
    throw "iServer is not reachable and startup.bat was not found: $startup"
  }
  Write-Host "[START] iServer"
  $proc = Start-Process -FilePath $startup -WorkingDirectory (Split-Path $startup -Parent) -WindowStyle Hidden -PassThru
  Set-Content -LiteralPath $iserverPidFile -Value $proc.Id -Encoding ASCII
  Wait-Url -Url $iserverUrl -TimeoutSeconds 120
}

Write-Host ""
Write-Host "== Backend =="
$backendUrl = "http://localhost:$BackendPort/api/health"
if (Test-Url -Url $backendUrl) {
  Write-Host "[OK] backend already running: $backendUrl"
  if (-not (Test-BackendNavigationRoute -Port $BackendPort)) {
    throw "Backend is running but /api/navigation/start is missing. Run STOP_DEMO.bat, then START_DEMO.bat to load the R2 backend."
  }
}
else {
  Write-Host "[START] backend on port $BackendPort"
  $backendCommand = "& '$ProjectRoot\scripts\start_backend.ps1' -Port $BackendPort"
  Start-HiddenPowerShell `
    -Command $backendCommand `
    -WorkingDirectory $ProjectRoot `
    -PidFile $backendPidFile `
    -StdoutLog $backendOutLog `
    -StderrLog $backendErrLog | Out-Null
  Wait-Url -Url $backendUrl -TimeoutSeconds 45
  Confirm-NewServiceStable -Name "backend" -Url $backendUrl -PidFile $backendPidFile -LogPaths @($backendOutLog, $backendErrLog)
  if (-not (Test-BackendNavigationRoute -Port $BackendPort)) {
    $logTail = Get-LogTail -Paths @($backendOutLog, $backendErrLog)
    throw "Backend started, but /api/navigation/start is missing.`n$logTail"
  }
}

Write-Host ""
Write-Host "== Frontend =="
$frontendUrl = "http://localhost:$FrontendPort"
if (Test-Url -Url $frontendUrl) {
  Write-Host "[OK] frontend already running: $frontendUrl"
}
else {
  Write-Host "[START] frontend on port $FrontendPort"
  $frontendCommand = "& '$ProjectRoot\scripts\start_frontend_supermap_project.ps1' -Port $FrontendPort"
  Start-HiddenPowerShell `
    -Command $frontendCommand `
    -WorkingDirectory $ProjectRoot `
    -PidFile $frontendPidFile `
    -StdoutLog $frontendOutLog `
    -StderrLog $frontendErrLog | Out-Null
  Wait-Url -Url $frontendUrl -TimeoutSeconds 60
  Confirm-NewServiceStable -Name "frontend" -Url $frontendUrl -PidFile $frontendPidFile -LogPaths @($frontendOutLog, $frontendErrLog)
}

if (-not $NoBrowser) {
  Write-Host ""
  Write-Host "[OPEN] $frontendUrl"
  Start-Process $frontendUrl
}

Write-Host ""
Write-Host "[PASS] Demo is ready."
Write-Host "URL: $frontendUrl"
Write-Host "Stop: powershell -ExecutionPolicy Bypass -File $ProjectRoot\scripts\stop_demo_one_click.ps1"
