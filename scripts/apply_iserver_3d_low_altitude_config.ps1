param(
  [string]$InstallRoot = "E:\supermap_software\supermap-iserver-2025u1a-windows-x64-all",
  [string]$ProjectRoot = "E:\supermap_project",
  [string]$StagedXml = "docs\supermap_integration\generated\iserver-services.with-3D-low_altitude_demo.staged.xml",
  [string]$BackupDir = "docs\supermap_integration\generated\iserver_config_backups",
  [string]$IServerBaseUrl = "http://localhost:8090/iserver",
  [switch]$Apply,
  [switch]$Restart,
  [switch]$RollbackLatest
)

$ErrorActionPreference = "Stop"

function Assert-ValidLowAltitude3DConfig {
  param([string]$Path)

  [xml]$xml = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
  $components = @($xml.application.components.component | Where-Object { $_.name -eq "3D-low_altitude_demo" })
  $providers = @($xml.application.providers.provider | Where-Object { $_.name -eq "3D-low_altitude_demo" })
  if ($components.Count -ne 1) {
    throw "Expected exactly one 3D-low_altitude_demo component in $Path, got $($components.Count)"
  }
  if ($providers.Count -ne 1) {
    throw "Expected exactly one 3D-low_altitude_demo provider in $Path, got $($providers.Count)"
  }
  if ($components[0].class -ne "com.supermap.services.components.impl.RealspaceImpl") {
    throw "Unexpected component class: $($components[0].class)"
  }
  if ($providers[0].class -ne "com.supermap.services.providers.UGCRealspaceProvider") {
    throw "Unexpected provider class: $($providers[0].class)"
  }
  if ($providers[0].config.workspacePath -notlike "*low_altitude_demo.smwu") {
    throw "Unexpected provider workspacePath: $($providers[0].config.workspacePath)"
  }
  if (-not $providers[0].config.output) {
    throw "UGCRealspaceProviderSetting.output is required for 3D-low_altitude_demo"
  }
}

function Restart-IServer {
  param([string]$Root)

  $bin = Join-Path $Root "bin"
  $shutdown = Join-Path $bin "shutdown.bat"
  $startup = Join-Path $bin "startup.bat"
  if (-not (Test-Path -LiteralPath $shutdown)) {
    throw "shutdown.bat not found: $shutdown"
  }
  if (-not (Test-Path -LiteralPath $startup)) {
    throw "startup.bat not found: $startup"
  }

  Push-Location $bin
  try {
    Write-Host "[RUN] shutdown.bat"
    & $shutdown | Out-Host
    Start-Sleep -Seconds 8
    Write-Host "[RUN] startup.bat"
    & $startup | Out-Host
    Start-Sleep -Seconds 20
  }
  finally {
    Pop-Location
  }
}

function Test-IServer3DGate {
  param([string]$BaseUrl)

  $url = "$BaseUrl/services/3D-low_altitude_demo/rest/realspace/scenes.json"
  try {
    $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 20
    Write-Host "[CHECK] $url => HTTP $($response.StatusCode)"
    Write-Host $response.Content
  }
  catch {
    Write-Host "[CHECK] $url => $($_.Exception.Message)"
  }
}

$sourceXml = Join-Path $InstallRoot "webapps\iserver\WEB-INF\iserver-services.xml"
$stagedPath = if ([System.IO.Path]::IsPathRooted($StagedXml)) { $StagedXml } else { Join-Path $ProjectRoot $StagedXml }
$backupRoot = if ([System.IO.Path]::IsPathRooted($BackupDir)) { $BackupDir } else { Join-Path $ProjectRoot $BackupDir }

if (-not (Test-Path -LiteralPath $sourceXml)) {
  throw "iServer services XML not found: $sourceXml"
}
New-Item -ItemType Directory -Force -Path $backupRoot | Out-Null

if ($RollbackLatest) {
  $latest = Get-ChildItem -Path $backupRoot -Filter "iserver-services.*.xml" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if (-not $latest) {
    throw "No backup found in $backupRoot"
  }
  Write-Host "[INFO] latest backup => $($latest.FullName)"
  [xml]$null = Get-Content -LiteralPath $latest.FullName -Raw -Encoding UTF8
  if (-not $Apply) {
    Write-Host "[DRY-RUN] Would restore latest backup to $sourceXml. Re-run with -Apply to restore."
    exit 0
  }
  Copy-Item -LiteralPath $latest.FullName -Destination $sourceXml -Force
  Write-Host "[OK] restored backup => $sourceXml"
  if ($Restart) {
    Restart-IServer -Root $InstallRoot
    Test-IServer3DGate -BaseUrl $IServerBaseUrl
  }
  exit 0
}

if (-not (Test-Path -LiteralPath $stagedPath)) {
  throw "Staged XML not found: $stagedPath"
}

[xml]$null = Get-Content -LiteralPath $sourceXml -Raw -Encoding UTF8
Assert-ValidLowAltitude3DConfig -Path $stagedPath

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupPath = Join-Path $backupRoot "iserver-services.$stamp.xml"

Write-Host "[OK] source XML valid => $sourceXml"
Write-Host "[OK] staged XML valid => $stagedPath"
Write-Host "[INFO] backup target => $backupPath"

if (-not $Apply) {
  Write-Host "[DRY-RUN] Would backup source XML, apply staged XML, and optionally restart iServer."
  Write-Host "[DRY-RUN] Re-run with -Apply to modify iServer config. Add -Restart to restart and probe the 3D gate."
  exit 0
}

Copy-Item -LiteralPath $sourceXml -Destination $backupPath -Force
Copy-Item -LiteralPath $stagedPath -Destination $sourceXml -Force
Write-Host "[OK] backup saved => $backupPath"
Write-Host "[OK] staged XML applied => $sourceXml"

if ($Restart) {
  Restart-IServer -Root $InstallRoot
  Test-IServer3DGate -BaseUrl $IServerBaseUrl
}
else {
  Write-Host "[NEXT] Restart iServer, then run scripts\check_low_altitude_3d_gate.ps1"
}
