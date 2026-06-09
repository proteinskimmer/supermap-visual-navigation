param(
  [string]$GeoJsonDir = "demo_data\gis_export",
  [string]$WorkspacePath = "supermap_file_root\demo_workspace\low_altitude_demo.smwu",
  [string]$TargetConfig = "config\supermap_services.low_altitude_demo.example.json",
  [string]$LocalConfig = "config\supermap_services.local.json",
  [string]$IServerBaseUrl = "http://localhost:8090/iserver"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectRoot

function Test-RequiredPath {
  param(
    [string]$Path,
    [string]$Label,
    [switch]$Optional
  )

  if (Test-Path -LiteralPath $Path) {
    Write-Host "[OK] $Label => $Path"
    return $true
  }

  if ($Optional) {
    Write-Host "[TODO] $Label => $Path"
    return $false
  }

  throw "$Label missing: $Path"
}

function Get-JsonUrl {
  param(
    [string]$Url,
    [string]$Label
  )

  try {
    $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 8
    Write-Host "[OK] $Label => HTTP $($response.StatusCode)"
    return $response.Content | ConvertFrom-Json
  }
  catch {
    Write-Host "[TODO] $Label => $Url"
    Write-Host "       $($_.Exception.Message)"
    return $null
  }
}

$requiredGeoJson = @(
  "task_area.geojson",
  "risk_zone.geojson",
  "obstacle.geojson",
  "vision_tile.geojson",
  "start_target.geojson",
  "routes_preview.geojson",
  "vision_image_center.geojson",
  "uav_position.geojson"
)

Write-Host "== Project demo GeoJSON package =="
Test-RequiredPath -Path $GeoJsonDir -Label "GeoJSON directory" | Out-Null
foreach ($name in $requiredGeoJson) {
  $path = Join-Path $GeoJsonDir $name
  Test-RequiredPath -Path $path -Label $name | Out-Null
  $geojson = Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json
  if ($geojson.type -ne "FeatureCollection" -or -not $geojson.features -or $geojson.features.Count -lt 1) {
    throw "$name is not a non-empty GeoJSON FeatureCollection"
  }
  Write-Host ("[OK] {0}: {1} features" -f $name, $geojson.features.Count)
}

Write-Host ""
Write-Host "== Workspace target =="
$workspaceDir = Split-Path $WorkspacePath -Parent
Test-RequiredPath -Path $workspaceDir -Label "Workspace directory" | Out-Null
$workspaceExists = Test-RequiredPath -Path $WorkspacePath -Label "low_altitude_demo.smwu" -Optional

Write-Host ""
Write-Host "== Target service config template =="
Test-RequiredPath -Path $TargetConfig -Label "low_altitude_demo config template" | Out-Null
$config = Get-Content -LiteralPath $TargetConfig -Raw -Encoding UTF8 | ConvertFrom-Json
if ($config.services.scene.name -eq "3D-CBD" -or $config.services.scene.url -like "*3D-CBD*") {
  throw "Target config still points to 3D-CBD. It must point to low_altitude_demo services."
}
Write-Host "[OK] target scene service name: $($config.services.scene.name)"
Write-Host "[OK] target map service name: $($config.services.map.name)"
Write-Host "[OK] target data service name: $($config.services.data.name)"

Write-Host ""
$localConfigExists = Test-RequiredPath -Path $LocalConfig -Label "local service config" -Optional
if ($localConfigExists) {
  $localConfigJson = Get-Content -LiteralPath $LocalConfig -Raw -Encoding UTF8 | ConvertFrom-Json
  Write-Host "[OK] local map service status: $($localConfigJson.services.map.status)"
  Write-Host "[OK] local data service status: $($localConfigJson.services.data.status)"
}

Write-Host ""
Write-Host "== Published service checks =="
$mapList = Get-JsonUrl -Url "$IServerBaseUrl/services/map-low_altitude_demo/rest/maps.json" -Label "map-low_altitude_demo maps.json"
if ($null -ne $mapList) {
  if ($mapList.Count -gt 0) {
    Write-Host "[OK] map service has $($mapList.Count) map resource(s)"
  }
  else {
    Write-Host "[WARN] map service is published, but maps.json is empty. Save a map object in iDesktopX if map rendering is required."
  }
}

$datasetList = Get-JsonUrl -Url "$IServerBaseUrl/services/data-low_altitude_demo/rest/data/datasources/low_altitude_demo/datasets.json" -Label "data-low_altitude_demo datasets.json"
if ($null -ne $datasetList) {
  $expectedDatasets = @(
    "task_area_R",
    "risk_zone_R",
    "obstacle_ZP",
    "vision_tile_R",
    "start_target_ZP",
    "routes_preview_ZL",
    "vision_image_center_ZP",
    "uav_position_ZP"
  )
  foreach ($datasetName in $expectedDatasets) {
    if ($datasetList.datasetNames -contains $datasetName) {
      Write-Host "[OK] dataset published: $datasetName"
    }
    else {
      Write-Host "[TODO] dataset missing from data service: $datasetName"
    }
  }
}

Write-Host ""
if ($workspaceExists) {
  Write-Host "[PASS] Project workspace file exists. If data service checks are OK, the project-owned GIS data service gate is verified."
}
else {
  Write-Host "[NEXT] Open iDesktopX, import demo_data\gis_export, style layers, and save low_altitude_demo.smwu to the workspace target above."
}
