param(
  [int]$Port = 5173
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$FrontendDir = Join-Path $ProjectRoot "frontend"
$LocalVite = Join-Path $FrontendDir "node_modules\.bin\vite.cmd"

Set-Location $FrontendDir
if (Test-Path -LiteralPath $LocalVite) {
  & $LocalVite --host 0.0.0.0 --port $Port
  exit $LASTEXITCODE
}

npm run dev -- --port $Port
