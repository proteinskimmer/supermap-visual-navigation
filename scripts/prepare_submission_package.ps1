param(
  [string]$ProjectRoot = "E:\supermap_project",
  [string]$OutputRoot = "E:\supermap_project\release\low_altitude_demo_submission"
)

$ErrorActionPreference = "Stop"

function Copy-RequiredFile {
  param(
    [string]$Source,
    [string]$Destination
  )

  if (-not (Test-Path -LiteralPath $Source)) {
    throw "Required file missing: $Source"
  }
  New-Item -ItemType Directory -Force -Path (Split-Path $Destination -Parent) | Out-Null
  Copy-Item -LiteralPath $Source -Destination $Destination -Force
  Write-Host "[COPY] $Source => $Destination"
}

Set-Location $ProjectRoot

$docsOut = Join-Path $OutputRoot "docs"
$screensOut = Join-Path $OutputRoot "screenshots"
$scriptsOut = Join-Path $OutputRoot "scripts"

New-Item -ItemType Directory -Force -Path $OutputRoot, $docsOut, $screensOut, $scriptsOut | Out-Null

$docFiles = @(
  "docs\delivery\version_record.md",
  "docs\delivery\current_progress_brief.md",
  "docs\delivery\supermap_interface_goal_audit.md",
  "docs\delivery\screenshot_evidence_registry.md",
  "docs\delivery\ppt_outline.md",
  "docs\delivery\defense_script.md",
  "docs\delivery\demo_video_script.md",
  "docs\delivery\submission_package_template.md",
  "docs\system_design.md",
  "docs\deploy_guide.md",
  "docs\data_description.md",
  "docs\source_code_structure.md"
)

foreach ($relative in $docFiles) {
  Copy-RequiredFile -Source (Join-Path $ProjectRoot $relative) -Destination (Join-Path $docsOut (Split-Path $relative -Leaf))
}

$screenshotFiles = @(
  "frontend_supermap_workspace.png",
  "iserver_publish_success_admin.png",
  "iserver_map_low_altitude_demo_map.png",
  "iserver_map_low_altitude_demo_map_json.png",
  "iserver_data_low_altitude_demo_datasets.png",
  "idesktopx_low_altitude_demo_map_layers.png",
  "iserver_3d_low_altitude_demo_scenes.png",
  "low_altitude_demo_map_iobjectspy_preview.png"
)

foreach ($name in $screenshotFiles) {
  Copy-RequiredFile -Source (Join-Path $ProjectRoot "docs\delivery\screenshots\$name") -Destination (Join-Path $screensOut $name)
}

Copy-RequiredFile `
  -Source (Join-Path $ProjectRoot "docs\delivery\screenshots\compat_cbd\frontend_supermap_workspace.png") `
  -Destination (Join-Path $screensOut "compat_cbd_frontend_supermap_workspace.png")

$scriptFiles = @(
  "scripts\check_supermap_goal_evidence.ps1",
  "scripts\run_supermap_browser_acceptance.ps1",
  "scripts\run_low_altitude_map_data_pipeline.ps1",
  "scripts\start_demo_one_click.ps1",
  "scripts\stop_demo_one_click.ps1",
  "scripts\start_backend.ps1",
  "scripts\start_frontend_supermap_project.ps1",
  "scripts\start_frontend_supermap_cbd.ps1"
)

foreach ($relative in $scriptFiles) {
  Copy-RequiredFile -Source (Join-Path $ProjectRoot $relative) -Destination (Join-Path $scriptsOut (Split-Path $relative -Leaf))
}

$readme = @"
# Low Altitude SuperMap Demo Submission

Version: v0.3-supermap-verified

This package contains the current evidence and defense materials for the SuperMap interface-level delivery gate.

## Verify

Run from the project root:

```powershell
powershell -ExecutionPolicy Bypass -File E:\supermap_project\scripts\check_supermap_goal_evidence.ps1 -Strict
```

Expected:

```text
[PASS] SuperMap goal evidence is complete.
```

## Demo Entry

```powershell
powershell -ExecutionPolicy Bypass -File E:\supermap_project\scripts\start_demo_one_click.ps1
```

Open:

```text
http://localhost:5173
```

Stop:

```powershell
powershell -ExecutionPolicy Bypass -File E:\supermap_project\scripts\stop_demo_one_click.ps1
```

## Strict Scope

Completed: SuperMap scene/map/data interface loop, frontend service status, screenshots, and REST gates.

Not claimed: fine-grained 3D modeling or real oblique-photogrammetry-level visualization.
"@

Set-Content -LiteralPath (Join-Path $OutputRoot "README.md") -Value $readme -Encoding UTF8

$runDemo = @"
param(
  [int]`$BackendPort = 8000,
  [int]`$FrontendPort = 5173
)

`$ErrorActionPreference = "Stop"
`$ProjectRoot = "E:\supermap_project"

powershell -ExecutionPolicy Bypass -File "`$ProjectRoot\scripts\start_demo_one_click.ps1" `
  -BackendPort `$BackendPort `
  -FrontendPort `$FrontendPort `
  -VerifyEvidence
"@

Set-Content -LiteralPath (Join-Path $OutputRoot "run_demo.ps1") -Value $runDemo -Encoding UTF8

$manifest = [ordered]@{
  version = "v0.3-supermap-verified"
  generated_at = (Get-Date).ToString("s")
  output_root = $OutputRoot
  docs = $docFiles
  screenshots = $screenshotFiles + @("compat_cbd_frontend_supermap_workspace.png")
  scripts = $scriptFiles
}

$manifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $OutputRoot "manifest.json") -Encoding UTF8

Write-Host ""
Write-Host "[PASS] submission package prepared: $OutputRoot"
