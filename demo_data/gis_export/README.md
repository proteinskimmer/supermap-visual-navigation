# Demo GIS Export Package

Generated from `demo_data/task_demo.json` for iDesktopX import.

Coordinate reference:
- CRS: WGS84 longitude/latitude, GeoJSON CRS84 axis order.
- Geometry coordinates use `[longitude, latitude]`.
- Point and route preview coordinates may include altitude as the third value in meters.

Recommended iDesktopX import order:
1. `task_area.geojson`
2. `risk_zone.geojson`
3. `obstacle.geojson`
4. `vision_tile.geojson`
5. `start_target.geojson`
6. `routes_preview.geojson`
7. `vision_image_center.geojson`
8. `uav_position.geojson`

Layer styling suggestion:
- `task_area`: transparent fill, cyan or blue border.
- `risk_zone`: red/orange fill by `level`, 40%-55% transparency.
- `obstacle`: tower/building point symbols, label by `name`, show `height_m`.
- `vision_tile`: yellow outline with light transparent fill, label by `tile_id`.
- `routes_preview`: style by `mode`; shortest gray, safest green, balanced blue.
- `start_target`: start green marker, target red marker.
- `uav_position`: bright moving/aircraft marker if available.

Publishing note:
- These files are mock/demo vector layers, not a real iServer scene.
- After iDesktopX scene production, publish with iServer and fill the resulting scene URL into the frontend `scene.open(sceneUrl)` configuration.