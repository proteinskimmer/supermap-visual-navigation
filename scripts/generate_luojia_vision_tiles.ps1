param(
  [string]$PythonExe = "E:\anaconda\envs\supermap_nav\python.exe",
  [int]$TileSizePx = 1024,
  [switch]$NoPreviews
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "generate_luojia_vision_tiles.py"
$argsList = @(
  $scriptPath,
  "--tile-size-px", $TileSizePx,
  "--update-demo",
  "--update-matches"
)

if ($NoPreviews) {
  $argsList += "--no-previews"
}

& $PythonExe @argsList
