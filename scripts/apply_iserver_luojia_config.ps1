param(
  [string]$InstallRoot = "E:\supermap_software\supermap-iserver-2025u1a-windows-x64-all",
  [string]$ProjectRoot = "E:\supermap_project",
  [string]$StagedXml = "docs\supermap_integration\generated\iserver-services.with-luojia_mountain_demo.staged.xml",
  [string]$BackupDir = "docs\supermap_integration\generated\iserver_config_backups",
  [string]$IServerBaseUrl = "http://localhost:8090/iserver",
  [switch]$Apply,
  [switch]$Restart
)

$ErrorActionPreference = "Stop"

function Assert-ValidLuojiaConfig {
  param([string]$Path)

  [xml]$xml = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
  $expected = @(
    @{ name = "map-luojia_mountain_demo"; componentClass = "com.supermap.services.components.impl.MapImpl"; providerClass = "com.supermap.services.providers.UGCMapProvider" },
    @{ name = "data-luojia_mountain_demo"; componentClass = "com.supermap.services.components.impl.DataImpl"; providerClass = "com.supermap.services.providers.UGCDataProvider" },
    @{ name = "3D-luojia_mountain_demo"; componentClass = "com.supermap.services.components.impl.RealspaceImpl"; providerClass = "com.supermap.services.providers.UGCRealspaceProvider" }
  )

  foreach ($item in $expected) {
    $components = @($xml.application.components.component | Where-Object { $_.name -eq $item.name })
    $providers = @($xml.application.providers.provider | Where-Object { $_.name -eq $item.name })
    if ($components.Count -ne 1) { throw "Expected exactly one component for $($item.name), got $($components.Count)" }
    if ($providers.Count -ne 1) { throw "Expected exactly one provider for $($item.name), got $($providers.Count)" }
    if ($components[0].class -ne $item.componentClass) { throw "Unexpected component class for $($item.name): $($components[0].class)" }
    if ($providers[0].class -ne $item.providerClass) { throw "Unexpected provider class for $($item.name): $($providers[0].class)" }
    if ($providers[0].config.workspacePath -notlike "*luojia_workspace/luojia_mountain_demo.smwu") {
      throw "Unexpected workspacePath for $($item.name): $($providers[0].config.workspacePath)"
    }
  }
}

function Restart-IServer {
  param([string]$Root)

  $bin = Join-Path $Root "bin"
  $shutdown = Join-Path $bin "shutdown.bat"
  $startup = Join-Path $bin "startup.bat"
  if (-not (Test-Path -LiteralPath $shutdown)) { throw "shutdown.bat not found: $shutdown" }
  if (-not (Test-Path -LiteralPath $startup)) { throw "startup.bat not found: $startup" }

  Push-Location $bin
  try {
    Write-Host "[RUN] shutdown.bat"
    & $shutdown | Out-Host
    Start-Sleep -Seconds 8
    Write-Host "[RUN] startup.bat"
    & $startup | Out-Host
    Start-Sleep -Seconds 25
  }
  finally {
    Pop-Location
  }
}

$sourceXml = Join-Path $InstallRoot "webapps\iserver\WEB-INF\iserver-services.xml"
$stagedPath = if ([System.IO.Path]::IsPathRooted($StagedXml)) { $StagedXml } else { Join-Path $ProjectRoot $StagedXml }
$backupRoot = if ([System.IO.Path]::IsPathRooted($BackupDir)) { $BackupDir } else { Join-Path $ProjectRoot $BackupDir }

if (-not (Test-Path -LiteralPath $sourceXml)) { throw "iServer services XML not found: $sourceXml" }
if (-not (Test-Path -LiteralPath $stagedPath)) { throw "Staged XML not found: $stagedPath" }
New-Item -ItemType Directory -Force -Path $backupRoot | Out-Null

[xml]$null = Get-Content -LiteralPath $sourceXml -Raw -Encoding UTF8
Assert-ValidLuojiaConfig -Path $stagedPath

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupPath = Join-Path $backupRoot "iserver-services.$stamp.xml"

Write-Host "[OK] source XML valid => $sourceXml"
Write-Host "[OK] staged Luojia XML valid => $stagedPath"
Write-Host "[INFO] backup target => $backupPath"

if (-not $Apply) {
  Write-Host "[DRY-RUN] Would backup source XML and apply staged Luojia XML."
  Write-Host "[DRY-RUN] Re-run with -Apply to modify iServer config. Add -Restart to restart iServer."
  exit 0
}

Copy-Item -LiteralPath $sourceXml -Destination $backupPath -Force
Copy-Item -LiteralPath $stagedPath -Destination $sourceXml -Force
Write-Host "[OK] backup saved => $backupPath"
Write-Host "[OK] staged XML applied => $sourceXml"

if ($Restart) {
  Restart-IServer -Root $InstallRoot
}
else {
  Write-Host "[NEXT] Restart iServer, then run scripts\check_luojia_supermap_gate.ps1"
}
