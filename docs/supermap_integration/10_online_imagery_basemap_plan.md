# Online Imagery Basemap Integration Plan

Created: 2026-06-14

## Purpose

Use an online imagery/map service as the large-area dynamic background layer. The local Luojia DEM, orthophoto, buildings, UAV frames, and ORB evidence remain the authoritative data for visual autonomous navigation.

The target behavior is tile-based dynamic loading:

```text
camera moves
-> SuperMap3D requests visible imagery tiles
-> local Luojia high-precision layer covers the task area
-> visual navigation still reads local Luojia data
```

## URL Information Needed

When asking for a SuperMap Online, iServer, WMTS, or XYZ imagery URL, collect:

| Field | Required | Notes |
|---|---|---|
| Provider name | Yes | SuperMap Online, iServer, TianDiTu, etc. |
| Service type | Yes | `supermap`, `url_template`, or `wmts` |
| URL | Yes | Full service URL or tile template |
| Token/key required | Yes | Record parameter name and expiration |
| Coverage | Yes | Global, China, Wuhan, or custom region |
| CRS/tiling scheme | Yes | WGS84/WebMercator/CGCS2000/GCJ-02 |
| Image type | Yes | Satellite imagery, vector map, label layer, mixed map |
| License | Yes | Whether competition demo/screenshot/video use is allowed |
| CORS/browser access | Yes | Must be callable from `localhost:5173` |
| Max zoom level | Recommended | Helps set `maximum_level` |
| Attribution text | Recommended | Shown in docs/PPT if required |

## Supported Config Shape

Fill the local config after the URL is confirmed:

```json
{
  "services": {
    "online_basemap": {
      "name": "Confirmed online imagery basemap",
      "url": "TO_BE_FILLED",
      "type": "url_template",
      "provider": "url_template",
      "status": "configured",
      "usage": "regional_3d_context_background_only",
      "minimum_level": 0,
      "maximum_level": 18,
      "alpha": 0.78,
      "credit": "TO_BE_FILLED"
    }
  }
}
```

For a SuperMap iServer map service:

```json
{
  "provider": "supermap",
  "url": "https://.../iserver/services/map-xxx/rest/maps/xxx"
}
```

For an XYZ tile template:

```json
{
  "provider": "url_template",
  "url": "https://.../{z}/{x}/{y}.png"
}
```

## Acceptance Steps After URL Is Available

1. Update `config/supermap_services.local.json`.
2. Start backend and frontend.
3. Open `http://localhost:5173`.
4. Confirm the scene status panel or DOM evidence shows:

```text
online basemap: installed
data-online-basemap-status="installed"
```

5. Click the regional 3D view button.
6. Verify imagery appears outside the Luojia high-precision area.
7. Verify Luojia local orthophoto/DEM still covers the task area.
8. Run:

```powershell
powershell -ExecutionPolicy Bypass -File E:\supermap_project\scripts\check_v05_navigation_gate.ps1 -PythonExe E:\anaconda\envs\supermap_nav\python.exe -SkipRuntime
```

9. Save a screenshot:

```text
docs/delivery/screenshots/r9_online_imagery_regional_3d_context.png
```

## Strict Wording

Allowed:

```text
The platform can load an online imagery basemap as a dynamic large-area background layer. Local Luojia high-precision DEM and orthophoto remain the visual-navigation data source.
```

Not allowed:

```text
The online basemap has been verified as high-precision visual navigation input.
The online imagery replaces the local Luojia orthophoto for ORB matching.
```
