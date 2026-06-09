param(
  [string]$InstallRoot = "E:\supermap_software\SuperMap iDesktopX 2025",
  [string]$ProjectRoot = "E:\supermap_project",
  [string]$GeoJsonDir = "demo_data\gis_export",
  [string]$Workspace = "supermap_file_root\demo_workspace_auto\low_altitude_demo.smwu",
  [string]$Datasource = "supermap_file_root\demo_workspace_auto\low_altitude_demo.udbx",
  [string]$MapName = "low_altitude_demo_map",
  [switch]$Overwrite
)

$ErrorActionPreference = "Stop"

function Require-Path {
  param([string]$Path, [string]$Label)
  if (-not (Test-Path -LiteralPath $Path)) {
    throw "$Label not found: $Path"
  }
}

Require-Path -Path $InstallRoot -Label "SuperMap iDesktopX install root"
$pythonExe = Join-Path $InstallRoot "support\python\python.exe"
$iobjectspyPath = Join-Path $InstallRoot "bin_python\iobjectspy\iobjectspy-py38_64"
$pythonLibPath = Join-Path $InstallRoot "support\PythonLib"
$builderScript = Join-Path $ProjectRoot "scripts\build_low_altitude_workspace.py"

Require-Path -Path $pythonExe -Label "SuperMap bundled Python"
Require-Path -Path $iobjectspyPath -Label "iObjectSpy py38 package"
Require-Path -Path $builderScript -Label "workspace builder script"
Require-Path -Path (Join-Path $ProjectRoot $GeoJsonDir) -Label "GeoJSON directory"

$env:JAVA_HOME = Join-Path $InstallRoot "jre"
$env:HADOOP_HOME = Join-Path $InstallRoot "support\hadoop"
$env:PYTHONPATH = "$iobjectspyPath;$pythonLibPath"
$env:Path = ".\bin;.\jre\bin;$(Join-Path $InstallRoot 'support\browser');$env:Path;$env:HADOOP_HOME\bin"
Remove-Item Env:JAVA_TOOL_OPTIONS -ErrorAction SilentlyContinue

$argsList = @(
  $builderScript,
  "--project-root", $ProjectRoot,
  "--geojson-dir", $GeoJsonDir,
  "--workspace", $Workspace,
  "--datasource", $Datasource,
  "--map-name", $MapName
)

if ($Overwrite) {
  $argsList += "--overwrite"
}

Push-Location $InstallRoot
try {
  & $pythonExe @argsList
  if ($LASTEXITCODE -ne 0) {
    throw "iObjectSpy workspace builder failed with exit code $LASTEXITCODE"
  }
}
finally {
  Pop-Location
}
