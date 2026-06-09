# low_altitude_demo workspace target

Use iDesktopX to create the project demo workspace in this directory.

Recommended output:

```text
E:\supermap_project\supermap_file_root\demo_workspace\low_altitude_demo.smwu
```

Import source:

```text
E:\supermap_project\demo_data\gis_export
```

Expected datasets:

```text
task_area
risk_zone
obstacle
vision_tile
start_target
routes_preview
vision_image_center
uav_position
```

After saving the workspace, publish it in iServer as:

```text
map-low_altitude_demo
data-low_altitude_demo
3D-low_altitude_demo
```

The 3D service is optional until a real iDesktopX scene is created. Map and data services are the minimum required project services.
