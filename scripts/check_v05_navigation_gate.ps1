param(
  [string]$PythonExe = "E:\anaconda\envs\supermap_nav\python.exe",
  [string]$ChromeExe = "C:\Program Files\Google\Chrome\Application\chrome.exe",
  [int]$BackendPort = 8000,
  [int]$FrontendPort = 5173,
  [switch]$SkipRuntime,
  [switch]$SkipBuild,
  [switch]$SkipBrowserGates,
  [switch]$KeepServers
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$TempDir = Join-Path $ProjectRoot ".tmp\v05_gate"
$BackendLog = Join-Path $TempDir "backend.log"
$FrontendLog = Join-Path $TempDir "frontend.log"
$ProbeScript = Join-Path $TempDir "v05_navigation_probe.py"
$BackendProcess = $null
$FrontendProcess = $null

function Write-Step {
  param([string]$Message)
  Write-Host ""
  Write-Host "== $Message =="
}

function Test-Url {
  param([string]$Url)
  try {
    $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3
    return $response.StatusCode -ge 200 -and $response.StatusCode -lt 500
  }
  catch {
    return $false
  }
}

function Wait-Url {
  param([string]$Url, [int]$TimeoutSeconds = 60)
  $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
  while ((Get-Date) -lt $deadline) {
    if (Test-Url -Url $Url) {
      Write-Host "[OK] $Url"
      return
    }
    Start-Sleep -Seconds 1
  }
  throw "Timed out waiting for $Url"
}

function Start-GateProcess {
  param(
    [string]$Name,
    [string]$Command,
    [string]$WorkingDirectory,
    [string]$LogPath
  )
  $runner = Join-Path $TempDir "$Name.runner.ps1"
  $workingLiteral = $WorkingDirectory.Replace("'", "''")
  $logLiteral = $LogPath.Replace("'", "''")
  $content = @"
`$ErrorActionPreference = "Stop"
Set-Location '$workingLiteral'
Start-Transcript -LiteralPath '$logLiteral' -Force | Out-Null
try {
  $Command
}
finally {
  Stop-Transcript | Out-Null
}
"@
  Set-Content -LiteralPath $runner -Value $content -Encoding UTF8
  return Start-Process `
    -FilePath "powershell.exe" `
    -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $runner) `
    -WorkingDirectory $WorkingDirectory `
    -WindowStyle Hidden `
    -PassThru
}

function Stop-GateProcess {
  param($Process, [string]$Name)
  if ($Process -and -not $Process.HasExited) {
    Write-Host "[STOP] $Name pid=$($Process.Id)"
    Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue
  }
}

function Invoke-Checked {
  param([string]$Label, [scriptblock]$Script)
  & $Script
  if ($LASTEXITCODE -ne 0) {
    throw "$Label failed with exit code $LASTEXITCODE"
  }
}

try {
  New-Item -ItemType Directory -Force -Path $TempDir | Out-Null
  Set-Location $ProjectRoot

  Write-Step "v0.5 runtime baseline"
  if (-not $SkipRuntime) {
    $runtimeArgs = @("-ExecutionPolicy", "Bypass", "-File", (Join-Path $PSScriptRoot "check_project_runtime.ps1"), "-PythonExe", $PythonExe)
    if ($SkipBuild) {
      $runtimeArgs += "-SkipBuild"
    }
    & powershell @runtimeArgs
  }
  else {
    Write-Host "[SKIP] runtime baseline"
  }

  Write-Step "v0.5 ORB evidence generation"
  & $PythonExe (Join-Path $PSScriptRoot "generate_v05_match_evidence.py") --task-id task_001 --top-k-tiles 2 --limit 6
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }

  Write-Step "v0.5 backend API and report gate"
  $probe = @'
import json
import pathlib
import sys

sys.path.insert(0, "backend")

from fastapi.testclient import TestClient

from app.main import app

root = pathlib.Path(".").resolve()
client = TestClient(app)


def unwrap(response):
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["success"] is True, payload
    return payload["data"]


task = unwrap(client.get("/api/tasks/task_001"))["task"]
route = unwrap(
    client.post(
        "/api/routes/plan",
        json={
            "task_id": task["id"],
            "start": task["start"],
            "target": task["target"],
            "modes": ["balanced"],
        },
    )
)[0]

matchers = unwrap(client.get("/api/vision/matchers"))
assert matchers["opencv_orb"]["status"] == "available", matchers["opencv_orb"]

session = unwrap(
    client.post(
        "/api/navigation/start",
        json={
            "task_id": task["id"],
            "route": route,
            "mode": "autonomous",
            "matcher_mode": "opencv_orb",
        },
    )
)
providers = {}
visual_frames = []
for frame in session["timeline"]:
    visual = frame.get("visual_position")
    if not visual:
        continue
    visual_frames.append(frame)
    provider = visual.get("localization_mode", "")
    providers[provider] = providers.get(provider, 0) + 1

assert session["matcher_mode"] == "opencv_orb"
assert len(session["timeline"]) >= 30
assert len(visual_frames) >= 6
assert set(providers) == {"opencv_orb"}, providers
assert max(frame["visual_position"]["confidence"] for frame in visual_frames) >= 0.8
assert any(frame["navigation_mode"] == "autonomous" for frame in visual_frames)

report = unwrap(client.get("/api/reports/task_001"))
quality = report["navigation_quality"]
assert quality["matcher_mode"] == "opencv_orb", quality
assert quality["visual_observation_count"] >= 6, quality
assert quality["provider_counts"] == {"opencv_orb": quality["visual_observation_count"]}, quality["provider_counts"]
assert quality["fallback_count"] == 0, quality
assert quality["confidence"]["average"] >= 0.65, quality["confidence"]
assert quality["fused_trajectory"]["smoothness_passed"] is True, quality["fused_trajectory"]
assert quality["fused_trajectory"]["average_deviation_m"] <= 10, quality["fused_trajectory"]
assert quality["quality_grade"] in {"demo_verified", "navigation_verified"}, quality

summary_path = root / "demo_data" / "generated" / "v05_match_evidence" / "summary_opencv_orb.json"
assert summary_path.exists(), summary_path
summary = json.loads(summary_path.read_text(encoding="utf-8"))
assert summary["provider"] == "opencv_orb", summary
assert summary["image_count"] >= 6, summary
assert summary["localized_count"] >= 6, summary

evidence_dir = summary_path.parent
png_count = len(list(evidence_dir.glob("*.png")))
json_count = len(list(evidence_dir.glob("*.json")))
tmp_count = len(list((root / "frontend" / "public" / "demo").rglob(".*.tmp.*"))) + len(list(evidence_dir.glob(".*.tmp.*")))
assert png_count >= 24, png_count
assert json_count >= 7, json_count
assert tmp_count == 0, tmp_count

print(json.dumps({
    "navigation_frames": len(session["timeline"]),
    "visual_observation_count": len(visual_frames),
    "providers": providers,
    "quality_grade": quality["quality_grade"],
    "average_confidence": quality["confidence"]["average"],
    "average_fused_deviation_m": quality["fused_trajectory"]["average_deviation_m"],
    "final_error_m": quality["fused_trajectory"]["final_error_m"],
    "evidence_png_count": png_count,
    "evidence_json_count": json_count,
}, ensure_ascii=False, indent=2))
print("[PASS] v0.5 backend ORB navigation and report gate verified.")
'@
  Set-Content -LiteralPath $ProbeScript -Value $probe -Encoding UTF8
  & $PythonExe $ProbeScript
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }

  if (-not $SkipBrowserGates) {
    Write-Step "v0.5 browser gates"
    if (-not (Test-Path -LiteralPath $ChromeExe)) {
      throw "Chrome executable not found: $ChromeExe. Re-run with -SkipBrowserGates to skip DOM/screenshot gates."
    }

    $backendUrl = "http://localhost:$BackendPort/api/health"
    if (Test-Url -Url $backendUrl) {
      Write-Host "[OK] backend already running: $backendUrl"
    }
    else {
      Write-Host "[START] backend on port $BackendPort"
      $backendCommand = "& '$PythonExe' -m uvicorn app.main:app --host 127.0.0.1 --port $BackendPort"
      $BackendProcess = Start-GateProcess -Name "backend" -Command $backendCommand -WorkingDirectory (Join-Path $ProjectRoot "backend") -LogPath $BackendLog
      Wait-Url -Url $backendUrl -TimeoutSeconds 60
    }

    $frontendUrl = "http://localhost:$FrontendPort"
    if (Test-Url -Url $frontendUrl) {
      Write-Host "[OK] frontend already running: $frontendUrl"
    }
    else {
      Write-Host "[START] frontend on port $FrontendPort"
      $apiBase = "http://localhost:$BackendPort/api"
      $frontendCommand = "`$env:VITE_API_BASE='$apiBase'; & '$ProjectRoot\scripts\start_frontend_supermap_project.ps1' -Port $FrontendPort"
      $FrontendProcess = Start-GateProcess -Name "frontend" -Command $frontendCommand -WorkingDirectory $ProjectRoot -LogPath $FrontendLog
      Wait-Url -Url $frontendUrl -TimeoutSeconds 80
    }

    Invoke-Checked -Label "Luojia frontend DOM gate" -Script {
      & powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "check_luojia_frontend_dom_gate.ps1") -FrontendUrl $frontendUrl -ChromeExe $ChromeExe
    }
    Invoke-Checked -Label "Luojia frontend visual gate" -Script {
      & powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "check_luojia_frontend_visual_gate.ps1") -FrontendUrl $frontendUrl -ChromeExe $ChromeExe
    }
  }
  else {
    Write-Host "[SKIP] browser DOM/screenshot gates"
  }

  Write-Host ""
  Write-Host "[PASS] v0.5 navigation gate passed."
}
finally {
  if (-not $KeepServers) {
    Stop-GateProcess -Process $FrontendProcess -Name "frontend"
    Stop-GateProcess -Process $BackendProcess -Name "backend"
  }
}
