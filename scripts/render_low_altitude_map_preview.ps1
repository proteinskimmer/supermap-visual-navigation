param(
  [string]$InstallRoot = "E:\supermap_software\SuperMap iDesktopX 2025",
  [string]$ProjectRoot = "E:\supermap_project",
  [string]$Workspace = "supermap_file_root\demo_workspace\low_altitude_demo.smwu",
  [string]$MapName = "low_altitude_demo_map",
  [string]$Output = "docs\delivery\screenshots\low_altitude_demo_map_iobjectspy_preview.png",
  [string]$Summary = "docs\delivery\screenshots\low_altitude_demo_map_iobjectspy_preview.json",
  [int]$Width = 1600,
  [int]$Height = 1000
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
$renderScript = Join-Path $ProjectRoot "scripts\render_low_altitude_map_preview.py"

Require-Path -Path $pythonExe -Label "SuperMap bundled Python"
Require-Path -Path $iobjectspyPath -Label "iObjectSpy py38 package"
Require-Path -Path $renderScript -Label "map preview render script"
Require-Path -Path (Join-Path $ProjectRoot $Workspace) -Label "SuperMap workspace"

$env:JAVA_HOME = Join-Path $InstallRoot "jre"
$env:HADOOP_HOME = Join-Path $InstallRoot "support\hadoop"
$env:PYTHONPATH = "$iobjectspyPath;$pythonLibPath"
$env:Path = ".\bin;.\jre\bin;$(Join-Path $InstallRoot 'support\browser');$env:Path;$env:HADOOP_HOME\bin"
Remove-Item Env:JAVA_TOOL_OPTIONS -ErrorAction SilentlyContinue

$argsList = @(
  $renderScript,
  "--project-root", $ProjectRoot,
  "--workspace", $Workspace,
  "--map-name", $MapName,
  "--output", $Output,
  "--summary", $Summary,
  "--width", $Width,
  "--height", $Height
)

Push-Location $InstallRoot
try {
  & $pythonExe @argsList
  if ($LASTEXITCODE -ne 0) {
    throw "iObjectSpy map preview renderer failed with exit code $LASTEXITCODE"
  }
}
finally {
  Pop-Location
}
