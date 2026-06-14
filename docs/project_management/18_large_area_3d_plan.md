# R9 Regional Large-Area 3D Display Plan

Created: 2026-06-14

Baseline tag: `v0.5`

## Goal

Add a regional large-area 3D context layer that is spatially connected with the Luojia local scene, while keeping the visual autonomous navigation mainline locked to local high-precision Luojia data.

This is not a global-view feature. The required effect is:

```text
regional low-resolution 3D context
-> local Luojia high-resolution DEM/orthophoto/buildings
-> UAV visual autonomous navigation inside the local high-precision area
```

## Data Source Priority

1. `local_verified_luojia`
   - Local Luojia DEM, orthophoto, building, route, risk, and generated UAV frame data.
   - Used for visual localization, synthetic-view generation, ORB matching, fused navigation, and report metrics.

2. `regional_3d_context`
   - Local generated low-resolution terrain context around Luojia.
   - Used to visually connect the task scene with a broader surrounding area.
   - Does not enter ORB matching or navigation fusion.

3. `online_large_area_context`
   - Optional online basemap or terrain services.
   - Used for regional 3D display only after provider/license/coordinate checks.
   - Not accepted as high-precision visual navigation evidence unless separately verified.

4. `display_only`
   - If online data has coordinate offset, license limits, labels, watermarks, or unstable resolution, it remains display-only.

## Completed In This Step

| ID | Task | Status | Evidence |
|---|---|---|---|
| R9-01 | Add regional 3D view switch | Runtime Verified | `SuperMapScene` has `区域三维` control and `fitToLargeArea` now flies to Luojia regional context, not global height |
| R9-02 | Add connected regional terrain context | Runtime Verified | Local generated low-resolution regional terrain mesh surrounds the high-precision Luojia terrain |
| R9-03 | Reserve online basemap and terrain config | Runtime Verified | `online_basemap` and `online_terrain` templates remain optional, not required for the regional local context |
| R9-04 | Preserve visual-navigation local-data boundary | Runtime Verified | Code only changes display context; ORB/navigation APIs still use Luojia task data |
| R9-05 | Extend DOM gate | Runtime Verified | DOM gate checks `data-view-scope`, regional terrain marker, online layer status markers, and regional 3D button |

## Pending

| ID | Task | Status | Acceptance |
|---|---|---|---|
| R9-06 | Choose real online provider | Todo | Confirm service URL, key/license, coordinate system, and access stability |
| R9-07 | Configure local online service URL | Todo | Fill `services.online_basemap.url` and optionally `services.online_terrain.url` in local config |
| R9-08 | Capture regional 3D evidence screenshot | Todo | Screenshot shows regional 3D context connected to the local Luojia scene; caption clearly says visual navigation still uses local Luojia data |

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
regional 3D view button verified
regional terrain context installed
online basemap status marker verified
online terrain status marker verified
```

## Strict Wording

Allowed:

```text
The system supports a regional large-area 3D context connected with the local Luojia scene. Visual autonomous navigation remains based on local Luojia high-precision DEM, orthophoto, and building data.
```

Not allowed:

```text
Online basemap data is already verified as high-precision visual navigation input.
Global high-precision visual autonomous navigation has been completed.
The large-area scene is a separate global view unrelated to the local task scene.
```
