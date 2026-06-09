# 可复用场景数据导入流水线

## 目标

把某一地区的 DEM、正射影像、建筑信息和业务图层整理成项目可用的两类成果：

- 前端演示预览数据：轻量 DEM 网格、正射影像贴图、建筑拉伸 JSON。
- SuperMap 发布准备数据：iObjectsPy 可导入的工作空间、数据源、地图图层清单。

这条流水线用于快速换区验证。正式交付时，仍应优先用 SuperMap 的正式三维地形、影像缓存和场景发布能力替换前端轻量预览层。

## 输入数据要求

每个地区建议建立一个目录：

```text
data_sources/<scene_id>/
  raw_test_data/
  raw_student_output/
  README.md
```

必须准备：

- 正射影像：GeoTIFF，最好同时提供 `.tfw` 或明确投影范围。
- 高程数据：优先提供 `X,Y,Z` 地形点 CSV；DEM GeoTIFF 可用于 SuperMap 导入，但当前轻量前端预览暂不直接解析压缩 DEM。
- 建筑信息：Polygon Shapefile，必须带 `.shp/.shx/.dbf/.prj`，高度字段优先命名为 `HEIGHT_M`。
- 投影参数：至少明确 EPSG、中央经线、假东、假北。当前脚本已支持 WGS84 和横轴墨卡托/高斯克吕格反算。

可选准备：

- 禁飞区、风险区、航线走廊、视觉匹配瓦片范围。
- 地物分类、道路、水体、兴趣点。
- 合成视角瓦片索引，用于视觉自主导航演示。

## 配置文件

复制现有样例：

```powershell
Copy-Item E:\supermap_project\config\scene_data_profiles\luojia_mountain.example.json E:\supermap_project\config\scene_data_profiles\<scene_id>.json
```

重点修改：

- `scene_id`：地区唯一标识。
- `source_dir`：地区数据根目录。
- `projection`：数据源投影参数。
- `extent.projected`：正射影像和 DEM 的投影坐标范围。如果留空，脚本会尝试用正射影像 `.tfw` 和 TIFF 宽高推算。
- `orthophoto.path`、`orthophoto.world_file`、`orthophoto.texture_url`。
- `terrain.source.path`、`x_field`、`y_field`、`z_field`、网格 `cols/rows`。
- `buildings.source.path`、`height.field`、高度默认值和上下限。
- `supermap.imports`：需要导入 iDesktopX/iServer 的 raster/shape 清单。

## 前端预览数据生成

运行：

```powershell
E:\anaconda\envs\supermap_nav\python.exe E:\supermap_project\scripts\build_scene_preview_data.py --project-root E:\supermap_project --config E:\supermap_project\config\scene_data_profiles\<scene_id>.json --all
```

输出：

- `frontend/public/demo/<scene>_terrain_preview.json`
- `frontend/public/demo/<scene>_buildings_preview.json`
- `frontend/public/demo/<scene>_scene_manifest.json`

验收重点：

- 地形顶点数大于 0。
- 三角面数大于 0。
- `z_min/z_max` 合理，不出现明显离谱高程。
- 建筑数量与源 Shapefile 大致一致。
- 前端加载后，正射影像贴在地形上，建筑底部贴近地表。

## SuperMap 工作空间生成

在已安装 iObjectsPy 的 SuperMap Python 环境中运行：

```powershell
E:\anaconda\envs\supermap_nav\python.exe E:\supermap_project\scripts\build_scene_supermap_workspace.py --project-root E:\supermap_project --config E:\supermap_project\config\scene_data_profiles\<scene_id>.json --overwrite
```

输出：

- `supermap_file_root/.../<scene>.smwu`
- `supermap_file_root/.../<scene>.udbx`
- `supermap_file_root/.../build_summary.json`

随后在 iServer 发布地图、数据服务和三维服务，前端再把真实 `sceneUrl/mapUrl/dataUrl` 写入 `config/supermap_services.local.json`。

## 新地区接入顺序

1. 收集数据，确认正射影像、DEM/地形点、建筑、投影信息齐全。
2. 建立 `data_sources/<scene_id>` 目录，保留原始数据，不要手工改坏源文件。
3. 复制并填写 `config/scene_data_profiles/<scene_id>.json`。
4. 运行 `build_scene_preview_data.py --all`，先让前端可见。
5. 运行前端构建和视觉验收脚本，确认没有黑屏、重影、漂移。
6. 运行 `build_scene_supermap_workspace.py`，生成 SuperMap 工作空间。
7. 在 iServer 发布真实服务，记录 URL。
8. 用截图和接口检查脚本留存验收证据。

## 当前限制

- 轻量预览脚本不直接采样压缩 DEM GeoTIFF；现在优先使用地形点 CSV 生成网格。
- Shapefile 读取器只覆盖 Polygon/PolygonZ/PolygonM 建筑轮廓，不处理复杂多层属性建模。
- 正射影像预览需要已有 JPG/PNG/WebP 贴图文件；GeoTIFF 到 Web 贴图的高质量转换建议交给 SuperMap 或 GDAL 类工具完成。
- 正式生产级三维效果应以 SuperMap 地形缓存、影像缓存、S3M/场景发布为准，前端 JSON 只是演示可靠性兜底。

## 珞珈山验证记录

已用 `config/scene_data_profiles/luojia_mountain.example.json` 跑通：

- 地形网格：2880 vertices / 5538 triangles。
- 高程范围：5.96m 到 103.06m。
- 建筑：169 栋。
- 输出清单：`frontend/public/demo/luojia_scene_manifest.json`。
