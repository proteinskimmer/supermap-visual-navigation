param(
  [string]$IServerPublishUrl = "http://localhost:8090/iserver/admin-ui/services/serviceManagement/publishServices",
  [string]$IDesktopExe = "E:\supermap_software\SuperMap iDesktopX 2025\SuperMap iDesktopX.exe",
  [string]$Workspace = "E:\supermap_project\supermap_file_root\demo_workspace\low_altitude_demo.smwu",
  [string]$Browser = ""
)

$ErrorActionPreference = "Stop"

if (-not $Browser) {
  $edge = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
  $chrome = "C:\Program Files\Google\Chrome\Application\chrome.exe"
  if (Test-Path -LiteralPath $edge) {
    $Browser = $edge
  }
  elseif (Test-Path -LiteralPath $chrome) {
    $Browser = $chrome
  }
  else {
    throw "No Edge/Chrome executable found."
  }
}

if (-not (Test-Path -LiteralPath $IDesktopExe)) {
  throw "iDesktopX executable not found: $IDesktopExe"
}

if (-not (Test-Path -LiteralPath $Workspace)) {
  throw "low_altitude_demo workspace not found: $Workspace"
}

Write-Host "[OPEN] iServer publish/admin page"
Start-Process -FilePath $Browser -ArgumentList @($IServerPublishUrl) -WindowStyle Normal

Write-Host "[OPEN] iDesktopX project workspace"
Start-Process -FilePath $IDesktopExe -ArgumentList @($Workspace) -WorkingDirectory (Split-Path $IDesktopExe -Parent) -WindowStyle Normal

Write-Host ""
Write-Host "[NEXT] After the windows are visible, capture evidence with:"
Write-Host "powershell -ExecutionPolicy Bypass -File E:\supermap_project\scripts\capture_interactive_gui_evidence.ps1 -Name iserver_publish_success_admin.png"
Write-Host "powershell -ExecutionPolicy Bypass -File E:\supermap_project\scripts\capture_interactive_gui_evidence.ps1 -Name idesktopx_low_altitude_demo_map_layers.png"
