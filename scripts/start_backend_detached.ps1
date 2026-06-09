param(
  [string]$CondaEnvPython = "E:\anaconda\envs\supermap_nav\python.exe",
  [int]$Port = 8000
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$BackendDir = Join-Path $ProjectRoot "backend"

if (-not (Test-Path -LiteralPath $CondaEnvPython)) {
  throw "Python executable not found: $CondaEnvPython"
}

$command = "& '$CondaEnvPython' -m uvicorn app.main:app --host 127.0.0.1 --port $Port"
Start-Process `
  -FilePath "powershell.exe" `
  -ArgumentList @("-NoProfile", "-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $command) `
  -WorkingDirectory $BackendDir `
  -WindowStyle Hidden

Start-Sleep -Seconds 4
$healthUrl = "http://localhost:$Port/api/health"
$response = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 10
if ($response.StatusCode -ne 200) {
  throw "Backend health check failed: HTTP $($response.StatusCode)"
}

Write-Host "[OK] backend detached server started: $healthUrl"
