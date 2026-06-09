param(
  [string]$ProjectRoot = "E:\supermap_project",
  [int[]]$Ports = @(5173, 8000),
  [switch]$StopIServer
)

$ErrorActionPreference = "Stop"

$stateDir = Join-Path $ProjectRoot ".tmp\demo_runtime"
$pidFiles = @(
  (Join-Path $stateDir "frontend.pid"),
  (Join-Path $stateDir "backend.pid")
)

if ($StopIServer) {
  $pidFiles += (Join-Path $stateDir "iserver_launcher.pid")
}

Write-Host "== Stop demo processes =="

foreach ($file in $pidFiles) {
  if (-not (Test-Path -LiteralPath $file)) {
    continue
  }
  $pidValue = Get-Content -LiteralPath $file -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($pidValue -and ($pidValue -as [int])) {
    $process = Get-Process -Id ([int]$pidValue) -ErrorAction SilentlyContinue
    if ($process) {
      Write-Host "[STOP] $($process.ProcessName) pid=$pidValue"
      Stop-Process -Id ([int]$pidValue) -Force -ErrorAction SilentlyContinue
    }
  }
  Remove-Item -LiteralPath $file -Force -ErrorAction SilentlyContinue
}

foreach ($port in $Ports) {
  $listenerPids = @()
  $connections = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
  foreach ($connection in $connections) {
    $listenerPids += $connection.OwningProcess
  }

  $netstatLines = netstat -ano | Select-String -Pattern "^\s*TCP\s+\S+:$port\s+\S+\s+LISTENING\s+(\d+)\s*$"
  foreach ($line in $netstatLines) {
    $match = [regex]::Match($line.Line, "LISTENING\s+(\d+)\s*$")
    if ($match.Success) {
      $listenerPids += [int]$match.Groups[1].Value
    }
  }

  foreach ($pidValue in ($listenerPids | Sort-Object -Unique)) {
    $process = Get-Process -Id $pidValue -ErrorAction SilentlyContinue
    if ($process) {
      Write-Host "[STOP] port $port => $($process.ProcessName) pid=$pidValue"
      Stop-Process -Id $pidValue -Force -ErrorAction SilentlyContinue
    }
  }
}

Write-Host "[PASS] Demo stop command finished."
