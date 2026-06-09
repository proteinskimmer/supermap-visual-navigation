param(
    [string]$SdkRoot = "E:\supermap_software\supermap-iclient3d-for-webgl_webgpu-2025u1"
)

$ErrorActionPreference = "Stop"

function Test-RequiredPath {
    param(
        [string]$Path,
        [string]$Label
    )

    if (Test-Path -LiteralPath $Path) {
        Write-Host "[OK] $Label => $Path"
        return $true
    }

    Write-Host "[FAIL] $Label => $Path"
    return $false
}

$allOk = $true

$requiredPaths = @(
    @{ Label = "SDK root"; Path = $SdkRoot },
    @{ Label = "Core JS"; Path = Join-Path $SdkRoot "Build\SuperMap3D\SuperMap3D.js" },
    @{ Label = "Widgets CSS"; Path = Join-Path $SdkRoot "Build\SuperMap3D\Widgets\widgets.css" },
    @{ Label = "Workers"; Path = Join-Path $SdkRoot "Build\SuperMap3D\Workers" },
    @{ Label = "Assets"; Path = Join-Path $SdkRoot "Build\SuperMap3D\Assets" },
    @{ Label = "ThirdParty"; Path = Join-Path $SdkRoot "Build\SuperMap3D\ThirdParty" },
    @{ Label = "API docs"; Path = Join-Path $SdkRoot "docs\Documentation" },
    @{ Label = "WebGL examples"; Path = Join-Path $SdkRoot "examples\webgl" },
    @{ Label = "Vue component examples"; Path = Join-Path $SdkRoot "examples\component" },
    @{ Label = "Topic docs"; Path = Join-Path $SdkRoot "examples\TopicDOC" },
    @{ Label = "Local web docs"; Path = Join-Path $SdkRoot "web" }
)

foreach ($item in $requiredPaths) {
    $allOk = (Test-RequiredPath -Path $item.Path -Label $item.Label) -and $allOk
}

$exampleFiles = @(
    "examples\webgl\S3MTiles.html",
    "examples\webgl\terrainAndImagery.html",
    "examples\webgl\SuperMapTileImagery.html",
    "examples\webgl\entity_polyline.html",
    "examples\webgl\entity_polygon.html",
    "examples\webgl\entity_point.html",
    "examples\component\vue_viewer.html",
    "examples\TopicDOC\HowToUseWebGPU.html",
    "examples\TopicDOC\Vue&WebGLDevelopment.html"
)

foreach ($relativePath in $exampleFiles) {
    $path = Join-Path $SdkRoot $relativePath
    $allOk = (Test-RequiredPath -Path $path -Label "Reference example $relativePath") -and $allOk
}

$webglDir = Join-Path $SdkRoot "examples\webgl"
$apiDir = Join-Path $SdkRoot "docs\Documentation"

if (Test-Path -LiteralPath $webglDir) {
    $webglCount = (Get-ChildItem -LiteralPath $webglDir -Filter "*.html" | Measure-Object).Count
    Write-Host "[INFO] WebGL example html count: $webglCount"
}

if (Test-Path -LiteralPath $apiDir) {
    $apiCount = (Get-ChildItem -LiteralPath $apiDir -Filter "*.html" | Measure-Object).Count
    Write-Host "[INFO] API documentation html count: $apiCount"
}

$patterns = @(
    "new SuperMap3D.Viewer",
    "viewer.scenePromise",
    "scene.open",
    "SuperMapImageryProvider",
    "SuperMapTerrainProvider",
    "UrlTemplateImageryProvider",
    "viewer.entities.add",
    "Cartesian3.fromDegrees",
    "Cartesian3.fromDegreesArray"
)

foreach ($pattern in $patterns) {
    $match = Select-String -Path (Join-Path $SdkRoot "examples\**\*.html") -Pattern $pattern -SimpleMatch -List -ErrorAction SilentlyContinue
    if ($match) {
        Write-Host "[OK] API pattern found: $pattern"
    }
    else {
        Write-Host "[WARN] API pattern not found in sampled examples: $pattern"
    }
}

if (-not $allOk) {
    throw "iClient3D local SDK verification failed. Some required paths are missing."
}

Write-Host "[PASS] iClient3D local SDK package appears complete. Browser rendering and license status still require manual verification."

