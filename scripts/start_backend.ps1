param(
  [string]$CondaExe = "E:\anaconda\Scripts\conda.exe",
  [string]$EnvName = "supermap_nav",
  [string]$PythonExe = "",
  [int]$Port = 8000
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")

Set-Location $ProjectRoot
Set-Location (Join-Path $ProjectRoot "backend")

if ($PythonExe -and (Test-Path -LiteralPath $PythonExe)) {
  & $PythonExe -m uvicorn app.main:app --host 127.0.0.1 --port $Port
  exit $LASTEXITCODE
}

$CondaEnvPython = Join-Path (Split-Path (Split-Path $CondaExe -Parent) -Parent) "envs\$EnvName\python.exe"
if (Test-Path -LiteralPath $CondaEnvPython) {
  & $CondaEnvPython -m uvicorn app.main:app --host 127.0.0.1 --port $Port
  exit $LASTEXITCODE
}

if (-not (Test-Path -LiteralPath $CondaExe)) {
  throw "Conda executable not found: $CondaExe"
}

& $CondaExe run -n $EnvName python -m uvicorn app.main:app --host 127.0.0.1 --port $Port
