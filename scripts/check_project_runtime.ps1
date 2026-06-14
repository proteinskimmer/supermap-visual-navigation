param(
  [string]$CondaExe = "E:\anaconda\Scripts\conda.exe",
  [string]$EnvName = "supermap_nav",
  [string]$PythonExe = "E:\anaconda\envs\supermap_nav\python.exe",
  [switch]$SkipBuild,
  [switch]$SkipBackend
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$FrontendDir = Join-Path $ProjectRoot "frontend"
$SdkPublicRoot = Join-Path $FrontendDir "public\vendor\supermap3d\Build\SuperMap3D"
$MinimalPage = Join-Path $FrontendDir "public\supermap-minimal.html"
$PytestBaseTemp = Join-Path $ProjectRoot ".tmp\pytest"

function Write-Step {
  param([string]$Message)
  Write-Host ""
  Write-Host "== $Message =="
}

function Assert-Path {
  param(
    [string]$Path,
    [string]$Label
  )

  if (-not (Test-Path -LiteralPath $Path)) {
    throw "$Label missing: $Path"
  }
  Write-Host "[OK] $Label"
}

Set-Location $ProjectRoot

Write-Step "GeoJSON export and parse"
& (Join-Path $PSScriptRoot "export_demo_geojson.ps1")

$geojsonFiles = Get-ChildItem -LiteralPath (Join-Path $ProjectRoot "demo_data\gis_export") -Filter "*.geojson"
foreach ($file in $geojsonFiles) {
  $data = Get-Content -LiteralPath $file.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
  if (-not $data.features -or $data.features.Count -lt 1) {
    throw "$($file.Name) has no features"
  }
  Write-Host ("[OK] {0}: {1} features" -f $file.Name, $data.features.Count)
}

Write-Step "SuperMap frontend static assets"
Assert-Path -Path $MinimalPage -Label "supermap-minimal.html"
Assert-Path -Path (Join-Path $SdkPublicRoot "SuperMap3D.js") -Label "SuperMap3D.js"
Assert-Path -Path (Join-Path $SdkPublicRoot "Widgets\widgets.css") -Label "widgets.css"
Assert-Path -Path (Join-Path $SdkPublicRoot "Workers") -Label "Workers"
Assert-Path -Path (Join-Path $SdkPublicRoot "Assets") -Label "Assets"
Assert-Path -Path (Join-Path $SdkPublicRoot "ThirdParty") -Label "ThirdParty"

$minimalContent = Get-Content -LiteralPath $MinimalPage -Raw -Encoding UTF8
$requiredMinimalMarkers = @(
  "new SuperMap3D.Viewer",
  "detectWebGL2",
  "scene.open",
  "SuperMap3D.js",
  "widgets.css"
)
foreach ($marker in $requiredMinimalMarkers) {
  if ($minimalContent -notlike "*$marker*") {
    throw "supermap-minimal.html missing marker: $marker"
  }
  Write-Host "[OK] minimal page marker: $marker"
}

Write-Step "Frontend syntax and build"
Set-Location $FrontendDir
node --check "src\services\api.js"
node --check "src\services\supermap3d.js"
if (-not $SkipBuild) {
  npm run build
}

Set-Location $ProjectRoot
if (-not $SkipBackend) {
  Write-Step "Backend tests and smoke"
  New-Item -ItemType Directory -Force -Path $PytestBaseTemp | Out-Null
  if (Test-Path -LiteralPath $PythonExe) {
    & $PythonExe -m pytest backend/tests --basetemp $PytestBaseTemp
    if ($LASTEXITCODE -ne 0) {
      exit $LASTEXITCODE
    }
    & (Join-Path $PSScriptRoot "check_backend_smoke_full.ps1") -PythonExe $PythonExe
  }
  else {
    if (-not (Test-Path -LiteralPath $CondaExe)) {
      throw "Python executable not found: $PythonExe; Conda executable not found: $CondaExe"
    }
    & $CondaExe run -n $EnvName python -m pytest backend/tests --basetemp $PytestBaseTemp
    if ($LASTEXITCODE -ne 0) {
      exit $LASTEXITCODE
    }
    & (Join-Path $PSScriptRoot "check_backend_smoke_full.ps1") -PythonExe $CondaExe -PythonArgs @("run", "-n", $EnvName, "python")
  }
}

Write-Host ""
Write-Host "[PASS] Project runtime checks passed. Browser screenshots and iServer service publication remain manual gates."
