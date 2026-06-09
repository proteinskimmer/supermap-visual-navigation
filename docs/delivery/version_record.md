# Version Record

Version: `v0.3-supermap-verified`

Recorded at: `2026-06-09`

## Scope

This version records the first fully verified SuperMap interface gate for the low-altitude demo:

- One-command GeoJSON to workspace pipeline.
- Project-owned `map-low_altitude_demo` and `data-low_altitude_demo` REST gates.
- Project-owned `3D-low_altitude_demo` REST gate.
- Frontend SuperMap workbench evidence.
- 3D-CBD compatibility evidence.
- iServer and iDesktopX GUI screenshot evidence.

## Required Verification

```powershell
powershell -ExecutionPolicy Bypass -File E:\supermap_project\scripts\check_supermap_goal_evidence.ps1 -Strict
```

Expected final line:

```text
[PASS] SuperMap goal evidence is complete.
```

## Evidence

Primary evidence directory:

```text
E:\supermap_project\docs\delivery\screenshots
```

Required screenshots:

- `frontend_supermap_workspace.png`
- `iserver_publish_success_admin.png`
- `iserver_map_low_altitude_demo_map.png`
- `iserver_data_low_altitude_demo_datasets.png`
- `idesktopx_low_altitude_demo_map_layers.png`
- `iserver_3d_low_altitude_demo_scenes.png`
- `compat_cbd/frontend_supermap_workspace.png`

## Strict Wording

Allowed:

```text
The project has completed the SuperMap scene/map/data interface-level loop and evidence archive.
```

Not allowed:

```text
The project has completed fine-grained 3D modeling or real oblique-photogrammetry-level visualization.
```

## Worktree Note

The project currently contains many staged and unstaged implementation artifacts from the SuperMap integration work. This record is a documented baseline, not a clean Git release tag.
