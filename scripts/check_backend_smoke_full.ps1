param(
  [string]$PythonExe = "python"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectRoot
$env:PYTHONDONTWRITEBYTECODE = "1"

$SmokeCode = @'
import ast
import json
import pathlib
import sys

sys.path.insert(0, "backend")

root = pathlib.Path(".").resolve()
demo_path = root / "demo_data" / "task_demo.json"
with demo_path.open("r", encoding="utf-8") as file:
    data = json.load(file)
print("[json] task_demo.json ok:", data["task"]["id"])

for path in sorted((root / "backend" / "app").rglob("*.py")):
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
print("[syntax] backend/app python files ok")

from app.services.planning_service import plan_routes
from app.services.risk_service import analyze_route
from app.services.vision_service import get_match_result, list_query_images, list_tile_index

routes = plan_routes(data["task"], data["risk_zones"])
risk = analyze_route(data["task"], routes[0], data["risk_zones"], data["obstacles"])
images = list_query_images("task_001")
tiles = list_tile_index("task_001")
match = get_match_result("task_001", images[0]["id"], top_k=2)
assert len(routes) == 3
assert 0 <= risk["score"] <= 100
assert len(images) >= 3
assert len(tiles) >= 5
assert match["candidate_count"] == 2
print("[services] planning/risk/vision ok")

try:
    from app.main import app
    from fastapi.testclient import TestClient
except ModuleNotFoundError as exc:
    print(f"[blocked] missing backend dependency: {exc.name}")
    print("[blocked] create/update the supermap_nav environment or install backend/requirements.txt, then rerun this script")
    raise SystemExit(2)

client = TestClient(app)

def unwrap(response):
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["success"] is True, payload
    assert payload["message"] == "ok", payload
    return payload["data"]

health = unwrap(client.get("/api/health"))
task = unwrap(client.get("/api/tasks/task_001"))["task"]
planned = unwrap(client.post("/api/routes/plan", json={
    "task_id": task["id"],
    "start": task["start"],
    "target": task["target"],
    "modes": ["shortest", "safest", "balanced"],
}))
analysis = unwrap(client.post("/api/risks/analyze", json={"task_id": task["id"], "route": planned[0]}))
simulation = unwrap(client.post("/api/simulations/start", json={"task_id": task["id"], "route": planned[0]}))
temporary = unwrap(client.post(f"/api/simulations/{simulation['simulation_id']}/temporary-risk", json={
    "task_id": task["id"],
    "current_position": planned[0]["points"][len(planned[0]["points"]) // 2],
    "time_s": 120,
}))
replanned = unwrap(client.post("/api/routes/replan", json={
    "task_id": task["id"],
    "current_position": planned[0]["points"][len(planned[0]["points"]) // 2],
    "target": task["target"],
    "temporary_risks": [temporary["risk"]],
    "time_s": 128,
}))
vision = unwrap(client.post("/api/vision/match", json={
    "task_id": task["id"],
    "image_id": "demo_uav_001",
    "top_k": 2,
    "algorithm_mode": "precomputed",
}))
report = unwrap(client.get("/api/reports/task_001"))
missing = client.get("/api/tasks/missing")
assert health["status"] == "ok"
assert len(planned) == 3
assert analysis["profile"]
assert replanned["route"]["id"] == "route_replanned_001"
assert vision["candidate_count"] == 2
assert report["recommended_route"]["mode"] == "balanced"
assert missing.status_code == 404
assert missing.json()["success"] is False
print("[api] FastAPI contract ok")
print("[smoke] full backend smoke passed")
'@

$TempScript = Join-Path ([System.IO.Path]::GetTempPath()) "supermap_backend_smoke_full.py"
try {
  Set-Content -LiteralPath $TempScript -Value $SmokeCode -Encoding UTF8
  & $PythonExe $TempScript
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }
}
finally {
  if (Test-Path $TempScript) {
    Remove-Item -LiteralPath $TempScript -Force
  }
}
