param(
  [string]$CondaExe = "E:\anaconda\Scripts\conda.exe",
  [string]$EnvName = "supermap_nav",
  [int]$Port = 8000
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")

if (-not (Test-Path -LiteralPath $CondaExe)) {
  throw "Conda executable not found: $CondaExe"
}

Set-Location $ProjectRoot
Set-Location (Join-Path $ProjectRoot "backend")
& $CondaExe run -n $EnvName fastapi dev app\main.py --port $Port
