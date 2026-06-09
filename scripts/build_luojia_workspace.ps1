param(
  [string]$InstallRoot = "E:\supermap_software\SuperMap iDesktopX 2025",
  [string]$ProjectRoot = "E:\supermap_project",
  [string]$SourceDir = "data_sources\luojia_mountain",
  [string]$Workspace = "supermap_file_root\luojia_workspace\luojia_mountain_demo.smwu",
  [string]$Datasource = "supermap_file_root\luojia_workspace\luojia_mountain_demo.udbx",
  [string]$MapName = "luojia_mountain_map",
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
$builderScript = Join-Path $ProjectRoot "scripts\build_luojia_workspace.py"

Require-Path -Path $pythonExe -Label "SuperMap bundled Python"
Require-Path -Path $iobjectspyPath -Label "iObjectSpy py38 package"
Require-Path -Path $builderScript -Label "Luojia workspace builder script"
Require-Path -Path (Join-Path $ProjectRoot $SourceDir) -Label "Luojia source directory"

$env:JAVA_HOME = Join-Path $InstallRoot "jre"
$env:HADOOP_HOME = Join-Path $InstallRoot "support\hadoop"
$env:PYTHONPATH = "$iobjectspyPath;$pythonLibPath"
$env:Path = "$(Join-Path $InstallRoot 'bin');$(Join-Path $InstallRoot 'jre\bin');$(Join-Path $InstallRoot 'support\browser');$env:Path;$env:HADOOP_HOME\bin"
Remove-Item Env:JAVA_TOOL_OPTIONS -ErrorAction SilentlyContinue

$argsList = @(
  $builderScript,
  "--project-root", $ProjectRoot,
  "--source-dir", $SourceDir,
  "--workspace", $Workspace,
  "--datasource", $Datasource,
  "--map-name", $MapName
)

if ($Overwrite) {
  $argsList += "--overwrite"
}

Push-Location $ProjectRoot
try {
  & $pythonExe @argsList
  if ($LASTEXITCODE -ne 0) {
    throw "Luojia iObjectSpy workspace builder failed with exit code $LASTEXITCODE"
  }
}
finally {
  Pop-Location
}
