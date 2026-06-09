param(
  [int]$Port = 5173,
  [string]$SceneUrl = "http://localhost:8090/iserver/services/3D-CBD/rest/realspace"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")

$env:VITE_SCENE_PROVIDER = "supermap"
$env:VITE_SUPERMAP_SCENE_URL = $SceneUrl

Set-Location $ProjectRoot
powershell -ExecutionPolicy Bypass -File scripts\start_frontend.ps1 -Port $Port
