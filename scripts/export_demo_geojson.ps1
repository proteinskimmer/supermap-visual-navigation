param(
  [string]$Source = "demo_data/task_demo.json",
  [string]$OutputDir = "demo_data/gis_export"
)

$ErrorActionPreference = "Stop"

function New-FeatureCollection {
  param([array]$Features)

  [ordered]@{
    type = "FeatureCollection"
    name = ""
    crs = [ordered]@{
      type = "name"
      properties = [ordered]@{
        name = "urn:ogc:def:crs:OGC:1.3:CRS84"
      }
    }
    features = $Features
  }
}

function New-Feature {
  param(
    [hashtable]$Geometry,
    [hashtable]$Properties
  )

  [ordered]@{
    type = "Feature"
    geometry = $Geometry
    properties = $Properties
  }
}

function Convert-BboxToPolygon {
  param([array]$Bbox)

  @(
    @($Bbox[0][0], $Bbox[0][1]),
    @($Bbox[1][0], $Bbox[1][1]),
    @($Bbox[2][0], $Bbox[2][1]),
    @($Bbox[3][0], $Bbox[3][1]),
    @($Bbox[0][0], $Bbox[0][1])
  )
}

function Write-GeoJson {
  param(
    [string]$Path,
    [array]$Features
  )

  $collection = New-FeatureCollection -Features $Features
  $collection.name = [IO.Path]::GetFileNameWithoutExtension($Path)
  $json = $collection | ConvertTo-Json -Depth 20
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText((Resolve-Path -LiteralPath (Split-Path -Parent $Path)).Path + [IO.Path]::DirectorySeparatorChar + [IO.Path]::GetFileName($Path), $json, $utf8NoBom)
}

$resolvedSource = Resolve-Path -LiteralPath $Source
$raw = Get-Content -LiteralPath $resolvedSource -Raw -Encoding UTF8
$demo = $raw | ConvertFrom-Json

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$task = $demo.task
$taskAreaFeature = New-Feature `
  -Geometry @{ type = $task.area.type; coordinates = $task.area.coordinates } `
  -Properties @{
    id = $task.id
    name = $task.display_name
    source = "task_demo_json"
    min_height_m = $task.params.min_height_m
    max_height_m = $task.params.max_height_m
    safe_distance_m = $task.params.safe_distance_m
    max_distance_m = $task.params.max_distance_m
  }
Write-GeoJson -Path (Join-Path $OutputDir "task_area.geojson") -Features @($taskAreaFeature)

$riskFeatures = @()
foreach ($risk in $demo.risk_zones) {
  $coords = @()
  foreach ($point in $risk.polygon) {
    $coords += ,@($point[0], $point[1])
  }
  $riskFeatures += New-Feature `
    -Geometry @{ type = "Polygon"; coordinates = ,$coords } `
    -Properties @{
      id = $risk.id
      name = $risk.name
      risk_type = $risk.type
      level = $risk.level
      buffer_m = $risk.buffer_m
      active = [int][bool]$risk.active
      source = "task_demo_json"
    }
}
Write-GeoJson -Path (Join-Path $OutputDir "risk_zone.geojson") -Features $riskFeatures

$obstacleFeatures = @()
foreach ($obstacle in $demo.obstacles) {
  $position = $obstacle.position
  $obstacleFeatures += New-Feature `
    -Geometry @{ type = "Point"; coordinates = @($position[0], $position[1], $position[2]) } `
    -Properties @{
      id = $obstacle.id
      name = $obstacle.name
      obstacle_type = $obstacle.type
      altitude_m = $position[2]
      height_m = $obstacle.height_m
      buffer_m = $obstacle.buffer_m
      source = "task_demo_json"
    }
}
Write-GeoJson -Path (Join-Path $OutputDir "obstacle.geojson") -Features $obstacleFeatures

$tileFeatures = @()
foreach ($tile in $demo.vision_tile_index) {
  $center = $tile.center
  $grid = $tile.grid
  $pixelBbox = $tile.pixel_bbox
  $tileFeatures += New-Feature `
    -Geometry @{ type = "Polygon"; coordinates = ,(Convert-BboxToPolygon -Bbox $tile.bbox) } `
    -Properties @{
      tile_id = $tile.tile_id
      task_id = $tile.task_id
      name = $tile.name
      source = $tile.source
      feature_count = $tile.feature_count
      tile_image = $tile.tile_image
      source_image = $tile.source_image
      feature_count_method = $tile.feature_count_method
      grid_row = if ($grid) { $grid.row } else { $null }
      grid_col = if ($grid) { $grid.col } else { $null }
      grid_rows = if ($grid) { $grid.rows } else { $null }
      grid_cols = if ($grid) { $grid.cols } else { $null }
      pixel_bbox = if ($pixelBbox) { ($pixelBbox -join ",") } else { "" }
      center_lon = $center[0]
      center_lat = $center[1]
      center_alt_m = $center[2]
    }
}
Write-GeoJson -Path (Join-Path $OutputDir "vision_tile.geojson") -Features $tileFeatures

$start = $task.start
$target = $task.target
$startTargetFeatures = @(
  (New-Feature `
    -Geometry @{ type = "Point"; coordinates = @($start[0], $start[1], $start[2]) } `
    -Properties @{ id = "start"; name = "Start"; role = "start"; altitude_m = $start[2]; task_id = $task.id }),
  (New-Feature `
    -Geometry @{ type = "Point"; coordinates = @($target[0], $target[1], $target[2]) } `
    -Properties @{ id = "target"; name = "Target"; role = "target"; altitude_m = $target[2]; task_id = $task.id })
)
Write-GeoJson -Path (Join-Path $OutputDir "start_target.geojson") -Features $startTargetFeatures

$routes = @(
  @{
    id = "route_shortest_preview"
    name = "Shortest preview"
    mode = "shortest"
    coordinates = @(
      @($start[0], $start[1], $start[2]),
      @(116.1580, 39.1570, 150.0),
      @($target[0], $target[1], $target[2])
    )
  },
  @{
    id = "route_safest_preview"
    name = "Safest preview"
    mode = "safest"
    coordinates = @(
      @($start[0], $start[1], $start[2]),
      @(116.1260, 39.1300, 145.0),
      @(116.1450, 39.1850, 170.0),
      @(116.1880, 39.2070, 155.0),
      @($target[0], $target[1], $target[2])
    )
  },
  @{
    id = "route_balanced_preview"
    name = "Balanced preview"
    mode = "balanced"
    coordinates = @(
      @($start[0], $start[1], $start[2]),
      @(116.1370, 39.1380, 140.0),
      @(116.1640, 39.1800, 165.0),
      @(116.2050, 39.1940, 150.0),
      @($target[0], $target[1], $target[2])
    )
  }
)
$routeFeatures = @()
foreach ($route in $routes) {
  $routeFeatures += New-Feature `
    -Geometry @{ type = "LineString"; coordinates = $route.coordinates } `
    -Properties @{
      id = $route.id
      name = $route.name
      mode = $route.mode
      task_id = $task.id
      preview = 1
      source = "manual_demo_preview"
    }
}
Write-GeoJson -Path (Join-Path $OutputDir "routes_preview.geojson") -Features $routeFeatures

$visionCenterFeatures = @()
foreach ($image in $demo.vision_images) {
  $center = $image.expected_center
  $visionCenterFeatures += New-Feature `
    -Geometry @{ type = "Point"; coordinates = @($center[0], $center[1], $center[2]) } `
    -Properties @{
      id = $image.id
      task_id = $image.task_id
      name = $image.name
      query_image = $image.query_image
      capture_time_s = $image.capture_time_s
      fov_deg = $image.camera.fov_deg
      pitch_deg = $image.camera.pitch_deg
      altitude_m = $center[2]
      source = "vision_expected_center"
    }
}
Write-GeoJson -Path (Join-Path $OutputDir "vision_image_center.geojson") -Features $visionCenterFeatures

$uav = $demo.vision_images[0].expected_center
$uavFeature = New-Feature `
  -Geometry @{ type = "Point"; coordinates = @($uav[0], $uav[1], $uav[2]) } `
  -Properties @{
    id = "uav_current_mock"
    name = "Current UAV mock position"
    task_id = $task.id
    capture_time_s = $demo.vision_images[0].capture_time_s
    altitude_m = $uav[2]
    source = "demo_current_uav"
  }
Write-GeoJson -Path (Join-Path $OutputDir "uav_position.geojson") -Features @($uavFeature)

$readme = @'
# Demo GIS Export Package

Generated from `demo_data/task_demo.json` for iDesktopX import.

Coordinate reference:
- CRS: WGS84 longitude/latitude, GeoJSON CRS84 axis order.
- Geometry coordinates use `[longitude, latitude]`.
- Point and route preview coordinates may include altitude as the third value in meters.

Recommended iDesktopX import order:
1. `task_area.geojson`
2. `risk_zone.geojson`
3. `obstacle.geojson`
4. `vision_tile.geojson`
5. `start_target.geojson`
6. `routes_preview.geojson`
7. `vision_image_center.geojson`
8. `uav_position.geojson`

Layer styling suggestion:
- `task_area`: transparent fill, cyan or blue border.
- `risk_zone`: red/orange fill by `level`, 40%-55% transparency.
- `obstacle`: tower/building point symbols, label by `name`, show `height_m`.
- `vision_tile`: yellow outline with light transparent fill, label by `tile_id`.
- `routes_preview`: style by `mode`; shortest gray, safest green, balanced blue.
- `start_target`: start green marker, target red marker.
- `uav_position`: bright moving/aircraft marker if available.

Publishing note:
- These files are mock/demo vector layers, not a real iServer scene.
- After iDesktopX scene production, publish with iServer and fill the resulting scene URL into the frontend `scene.open(sceneUrl)` configuration.
'@
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText((Join-Path $OutputDir "README.md"), $readme, $utf8NoBom)

Write-Host "Exported demo GeoJSON package to $OutputDir"
Get-ChildItem -LiteralPath $OutputDir -Filter "*.geojson" | Select-Object Name, Length
