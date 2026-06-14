# R9 Large-Area 3D Display And Online Context Plan

Created: 2026-06-14

Baseline tag: `v0.5`

## Goal

Add a global or large-area 3D context layer for task browsing and demonstration, while keeping the visual autonomous navigation mainline locked to local high-precision Luojia data.

## Data Source Priority

1. `local_verified_luojia`
   - Local Luojia DEM, orthophoto, building, route, risk, and generated UAV frame data.
   - Used for visual localization, synthetic-view generation, ORB matching, fused navigation, and report metrics.

2. `online_large_area_context`
   - Optional online basemap or terrain services.
   - Used for global or regional 3D display only.
   - Not accepted as high-precision visual navigation evidence unless separately verified.

3. `display_only`
   - If online data has coordinate offset, license limits, labels, watermarks, or unstable resolution, it remains display-only.

## Completed In This Step

| ID | Task | Status | Evidence |
|---|---|---|---|
| R9-01 | Add large-area 3D view switch | Runtime Verified | `SuperMapScene` has large-area view control and `fitToLargeArea` |
| R9-02 | Reserve online basemap and terrain config | Runtime Verified | `online_basemap` and `online_terrain` templates added |
| R9-03 | Preserve visual-navigation local-data boundary | Runtime Verified | Code only changes display context; ORB/navigation APIs still use Luojia task data |
| R9-04 | Extend DOM gate | Runtime Verified | DOM gate checks `data-view-scope`, online layer status markers, and large-area button |

## Pending

| ID | Task | Status | Acceptance |
|---|---|---|---|
| R9-05 | Choose real online provider | Todo | Confirm service URL, key/license, coordinate system, and access stability |
| R9-06 | Configure local online service URL | Todo | Fill `services.online_basemap.url` and optionally `services.online_terrain.url` in local config |
| R9-07 | Capture large-area evidence screenshot | Todo | Screenshot shows global/regional 3D context and a caption that visual navigation still uses local Luojia data |

## Verification

Passed on 2026-06-14:

```powershell
npm run build
powershell -ExecutionPolicy Bypass -File E:\supermap_project\scripts\check_v05_navigation_gate.ps1 -PythonExe E:\anaconda\envs\supermap_nav\python.exe -SkipRuntime
```

Observed gate result:

```text
v0.5 navigation gate passed
Luojia frontend DOM gate verified
large-area view button verified
online basemap status marker verified
online terrain status marker verified
```

## Strict Wording

Allowed:

```text
The system supports global or large-area 3D context display through configurable online basemap/terrain services, while visual autonomous navigation remains based on local Luojia high-precision DEM, orthophoto, and building data.
```

Not allowed:

```text
Online basemap data is already verified as high-precision visual navigation input.
Global high-precision visual autonomous navigation has been completed.
```
