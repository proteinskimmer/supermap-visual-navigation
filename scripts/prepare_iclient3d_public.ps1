param(
    [string]$SdkRoot = "E:\supermap_software\supermap-iclient3d-for-webgl_webgpu-2025u1",
    [string]$TargetRoot = "frontend\public\vendor\supermap3d"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$ResolvedTarget = Join-Path $ProjectRoot $TargetRoot
$ResolvedSdkRoot = Resolve-Path -LiteralPath $SdkRoot

$required = @(
    "Build\SuperMap3D\SuperMap3D.js",
    "Build\SuperMap3D\Widgets",
    "Build\SuperMap3D\Workers",
    "Build\SuperMap3D\Assets",
    "Build\SuperMap3D\ThirdParty"
)

foreach ($relative in $required) {
    $source = Join-Path $ResolvedSdkRoot $relative
    if (-not (Test-Path -LiteralPath $source)) {
        throw "Required iClient3D resource missing: $source"
    }
}

New-Item -ItemType Directory -Force -Path $ResolvedTarget | Out-Null

foreach ($relative in $required) {
    $source = Join-Path $ResolvedSdkRoot $relative
    $target = Join-Path $ResolvedTarget $relative
    $targetParent = Split-Path -Parent $target
    New-Item -ItemType Directory -Force -Path $targetParent | Out-Null

    if (Test-Path -Path $source -PathType Container) {
        Copy-Item -LiteralPath $source -Destination $targetParent -Recurse -Force
    }
    else {
        Copy-Item -LiteralPath $source -Destination $target -Force
    }
    Write-Host "[OK] copied $relative"
}

Write-Host "[PASS] iClient3D SDK resources prepared under $ResolvedTarget"
Write-Host "Open: http://localhost:5173/supermap-minimal.html"
