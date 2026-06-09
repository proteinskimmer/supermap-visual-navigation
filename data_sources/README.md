# 数据采集提交目录

本目录用于临时接收组员提交的真实 / 半真实 demo 数据。详细要求见：

```text
docs/project_management/14_real_data_collection_guide.md
```

组员提交时请按以下结构新建子目录：

```text
data_sources/
  低空巡检示范区_YYYYMMDD/
    README.md
    raw/
    processed/
    imagery/
    vision/
    screenshots/
```

最低必交：

```text
processed/task_area.geojson
processed/start_target.geojson
processed/risk_zone.geojson
processed/obstacle.geojson
README.md
```

注意：

- 坐标优先使用 WGS84。
- 经纬度顺序统一为 `[lon, lat, height]`。
- 不提交来源说不清或涉及敏感区域的数据。
- 大体积影像、DEM、三维缓存先放本地，不直接提交 Git。
