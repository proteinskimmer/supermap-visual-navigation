# Version Record

Version: `v0.5`

Recorded at: `2026-06-10`

## Scope

This version records the current software-simulation visual autonomous navigation baseline:

- SuperMap Luojia Mountain scene/map/data service integration.
- Backend authoritative visual navigation timeline.
- OpenCV ORB matcher provider for semi-real UAV frames.
- ORB-driven `visual_position` and `fused_position`.
- Smooth three-dimensional UAV playback.
- Navigation quality report.
- One-command v0.5 navigation gate.

## Required Verification

```powershell
powershell -ExecutionPolicy Bypass -File E:\supermap_project\scripts\check_v05_navigation_gate.ps1 -PythonExe E:\anaconda\envs\supermap_nav\python.exe
```

Expected key results:

```text
backend tests: 12 passed
ORB evidence: 6/6 localized
provider_counts: {"opencv_orb": 27}
quality_grade: demo_verified
fallback_frames: 0
```

## Evidence

Primary evidence directory:

```text
E:\supermap_project\docs\delivery\screenshots
```

Required screenshots currently available:

- `frontend_luojia_scene_headless.png`
- `v05_report_page_summary_route_risk_profile.png`
- `frontend_supermap_workspace.png`
- `iserver_services_list.png`
- `iserver_3d_low_altitude_demo_scenes.png`
- `iserver_data_low_altitude_demo_datasets.png`

Generated matching evidence:

```text
E:\supermap_project\demo_data\generated\v05_match_evidence
```

## Strict Wording

Allowed:

```text
The project has completed a v0.5a ORB-based visual localization prototype over semi-real UAV frames, and the ORB observations can drive the backend fused navigation timeline in software simulation.
```

Not allowed:

```text
The project has completed real-flight visual autonomous navigation.
The system can control a real UAV.
The current UAV frames are real flight-camera images.
```

## Worktree Note

This record is a delivery-material baseline and does not by itself imply a clean Git release tag.

## Git Tag

Saved on 2026-06-14:

```text
tag: v0.5
commit: baa6121
message: Archive v0.5 visual navigation gate
```

Post-tag work has started under R9 for global/large-area 3D context display. R9 is not part of the `v0.5` tag unless committed and tagged separately later.
