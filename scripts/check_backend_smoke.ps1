param(
  [string]$PythonExe = "python"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectRoot
$env:PYTHONDONTWRITEBYTECODE = "1"

& $PythonExe -c "import sys; sys.path.insert(0, 'backend'); from app.services.data_store import get_demo_data; from app.services.planning_service import plan_routes; from app.services.risk_service import analyze_route; data=get_demo_data(); routes=plan_routes(data['task'], data['risk_zones']); risk=analyze_route(data['task'], routes[0], data['risk_zones'], data['obstacles']); print({'routes': [r['mode'] for r in routes], 'score': risk['score'], 'points': len(routes[0]['points'])})"

