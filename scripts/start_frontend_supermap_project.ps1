param(
  [int]$Port = 5173,
  [string]$SceneUrl = ""
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")

$env:VITE_SCENE_PROVIDER = "supermap"
if ($SceneUrl) {
  $env:VITE_SUPERMAP_SCENE_URL = $SceneUrl
}
else {
  Remove-Item Env:\VITE_SUPERMAP_SCENE_URL -ErrorAction SilentlyContinue
}

Set-Location $ProjectRoot
powershell -ExecutionPolicy Bypass -File scripts\start_frontend.ps1 -Port $Port
