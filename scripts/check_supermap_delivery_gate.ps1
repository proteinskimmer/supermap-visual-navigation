param(
  [string]$IServerBaseUrl = "http://localhost:8090/iserver",
  [string]$BackendBaseUrl = "http://localhost:8000/api",
  [string]$MapName = "low_altitude_demo_map"
)

$ErrorActionPreference = "Stop"

function Get-Json {
  param([string]$Url, [string]$Label)
  $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 10
  if ($response.StatusCode -ne 200) {
    throw "$Label returned HTTP $($response.StatusCode)"
  }
  Write-Host "[OK] $Label => HTTP 200"
  return $response.Content | ConvertFrom-Json
}

function Assert-Equal {
  param($Actual, $Expected, [string]$Label)
  if ($Actual -ne $Expected) {
    throw "$Label expected $Expected, got $Actual"
  }
  Write-Host "[OK] $Label => $Actual"
}

function Assert-ContainsAll {
  param([array]$Actual, [array]$Expected, [string]$Label)
  foreach ($item in $Expected) {
    if ($Actual -notcontains $item) {
      throw "$Label missing: $item"
    }
  }
  Write-Host "[OK] $Label => $($Expected.Count) expected item(s)"
}

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

Write-Host "== Backend SuperMap config =="
$servicesPayload = Get-Json -Url "$BackendBaseUrl/supermap/services" -Label "backend /api/supermap/services"
if (-not $servicesPayload.success) {
  throw "backend /api/supermap/services success=false"
}
$serviceMap = @{}
foreach ($svc in $servicesPayload.data) {
  $serviceMap[$svc.id] = $svc
}
Assert-Equal -Actual $serviceMap.scene.status -Expected "verified" -Label "scene service status"
Assert-Equal -Actual $serviceMap.map.status -Expected "verified" -Label "map service status"
Assert-Equal -Actual $serviceMap.data.status -Expected "verified" -Label "data service status"

Write-Host ""
Write-Host "== iServer map service =="
$maps = Get-Json -Url "$IServerBaseUrl/services/map-low_altitude_demo/rest/maps.json" -Label "map-low_altitude_demo maps.json"
$mapNames = @($maps | ForEach-Object { $_.name })
Assert-ContainsAll -Actual $mapNames -Expected @($MapName) -Label "published map names"

$mapMeta = Get-Json -Url "$IServerBaseUrl/services/map-low_altitude_demo/rest/maps/$MapName.json" -Label "$MapName metadata"
Assert-Equal -Actual $mapMeta.prjCoordSys.epsgCode -Expected 4326 -Label "$MapName EPSG"
if ($mapMeta.bounds.left -eq 0 -and $mapMeta.bounds.right -eq 0) {
  throw "$MapName bounds are empty"
}
Write-Host "[OK] $MapName bounds => left=$($mapMeta.bounds.left), bottom=$($mapMeta.bounds.bottom), right=$($mapMeta.bounds.right), top=$($mapMeta.bounds.top)"

$layers = Get-Json -Url "$IServerBaseUrl/services/map-low_altitude_demo/rest/maps/$MapName/layers.json" -Label "$MapName layers"
$subLayers = @($layers[0].subLayers.layers | ForEach-Object { $_.datasetInfo.name })
Assert-ContainsAll -Actual $subLayers -Expected $expectedDatasets -Label "$MapName business layers"

Write-Host ""
Write-Host "== iServer data service =="
$datasets = Get-Json -Url "$IServerBaseUrl/services/data-low_altitude_demo/rest/data/datasources/low_altitude_demo/datasets.json" -Label "data-low_altitude_demo datasets"
Assert-Equal -Actual $datasets.datasetCount -Expected 8 -Label "data service dataset count"
Assert-ContainsAll -Actual $datasets.datasetNames -Expected $expectedDatasets -Label "data service dataset names"

Write-Host ""
Write-Host "== iServer configured scene service =="
$sceneService = $serviceMap.scene
$sceneBaseUrl = $sceneService.url.TrimEnd("/")
$sceneListUrl = "$sceneBaseUrl/scenes.json"
$sceneExpectedName = if ($sceneService.name -eq "3D-low_altitude_demo") { "low_altitude_demo" } elseif ($sceneService.name -eq "3D-CBD") { "CBD" } else { $sceneService.name }
$scenes = Get-Json -Url $sceneListUrl -Label "$($sceneService.name) scenes.json"
if (($scenes | ConvertTo-Json -Depth 5) -notmatch [regex]::Escape($sceneExpectedName)) {
  throw "$($sceneService.name) scenes.json does not contain $sceneExpectedName"
}
Write-Host "[OK] $($sceneService.name) scene list contains $sceneExpectedName"

Write-Host ""
Write-Host "[PASS] SuperMap delivery gate verified."
