# 珞珈山数据 SuperMap 接入方案

更新日期：2026-06-09

## 1. 目标

将 `data_sources/luojia_mountain` 中的珞珈山三维场景数据整理为 SuperMap 可发布的项目服务，用于替换当前演示级三维建筑体块和占位底图。

目标服务建议命名：

```text
workspace: luojia_mountain_demo.smwu
map service: map-luojia_mountain_demo
data service: data-luojia_mountain_demo
scene service: 3D-luojia_mountain_demo
scene name: luojia_mountain_demo
```

## 2. 主处理路线

优先使用 SuperMap，不使用 ArcGIS Pro 作为主处理链。

```text
源数据副本
 -> iDesktopX 导入 TIF/SHP/CSV
 -> 统一坐标系检查
 -> 制作二维地图和三维场景
 -> 建筑按 HEIGHT_M 拉伸
 -> 保存 smwu/udbx
 -> iServer 发布 map/data/scene
 -> 前端配置 sceneUrl/mapUrl/dataUrl
 -> 截图和 REST 门禁验收
```

ArcGIS Pro 仅作为备用工具，用于极端情况下的格式诊断或课程作业式制图，不作为本项目优先方案。

## 3. 输入数据

项目内副本路径：

```text
E:\supermap_project\data_sources\luojia_mountain
```

优先导入：

| 图层名建议 | 源文件 | 类型 | 用途 |
|---|---|---|---|
| `luojia_ortho` | `raw_test_data\珞珈山影像.tif` | Raster | 正射影像/底图 |
| `luojia_dem` | `raw_student_output\珞珈山DEM.tif` | Raster/DEM | 地形 |
| `luojia_terrain_points` | `raw_student_output\区域地形点.shp` | PointZ | 高程点备份 |
| `luojia_buildings_3d` | `raw_student_output\珞珈山周边建筑3D.shp` | Polygon | 建筑底面，按 `HEIGHT_M` 拉伸 |

暂不优先：

- `raw_student_output\珞珈山TIN\`：ArcGIS TIN 格式，SuperMap 主链路先用 DEM。
- `raw_test_data\珞珈山周边建筑.shp`：原始建筑面，不含清晰的 `HEIGHT_M` 字段。

## 4. 坐标系

数据主要坐标系：

```text
CGCS2000 / 3-degree Gauss-Kruger CM 114E
EPSG:4547
Unit: meter
```

iDesktopX 导入后必须检查：

- 影像、DEM、建筑、地形点是否叠合。
- 图层范围是否都在约 `534170 - 535710, 3379310 - 3380150`。
- 建筑面是否落在影像和 DEM 范围内。
- 不要强制转 WGS84，除非后续前端叠加业务 GeoJSON 明确需要经纬度。

## 5. iDesktopX 操作建议

1. 新建工作空间：

```text
E:\supermap_project\supermap_file_root\luojia_workspace\luojia_mountain_demo.smwu
```

2. 新建或连接数据源：

```text
E:\supermap_project\supermap_file_root\luojia_workspace\luojia_mountain_demo.udbx
```

3. 导入栅格：

- `珞珈山影像.tif` 命名为 `luojia_ortho`。
- `珞珈山DEM.tif` 命名为 `luojia_dem`。

4. 导入矢量：

- `区域地形点.shp` 命名为 `luojia_terrain_points`。
- `珞珈山周边建筑3D.shp` 命名为 `luojia_buildings_3d`。

5. 制作二维地图：

```text
map name: luojia_mountain_map
layer order:
  luojia_ortho
  luojia_dem
  luojia_buildings_3d
  luojia_terrain_points
```

6. 制作三维场景：

```text
scene name: luojia_mountain_demo
terrain: luojia_dem
imagery/base: luojia_ortho
buildings: luojia_buildings_3d
extrude field: HEIGHT_M
```

7. 建筑样式建议：

- 面填充：浅灰或淡蓝灰。
- 边线：深灰细线。
- 拉伸高度：`HEIGHT_M`。
- 若 `HEIGHT_M` 不被自动识别，先在属性表确认字段类型为数值。

8. 保存工作空间。

## 6. iServer 发布建议

在 iServer 管理页发布：

```text
workspace:
E:\supermap_project\supermap_file_root\luojia_workspace\luojia_mountain_demo.smwu
```

建议服务：

```text
map-luojia_mountain_demo
data-luojia_mountain_demo
3D-luojia_mountain_demo
```

发布后记录：

```text
map service:
http://localhost:8090/iserver/services/map-luojia_mountain_demo/rest/maps

data service:
http://localhost:8090/iserver/services/data-luojia_mountain_demo/rest/data

scene service:
http://localhost:8090/iserver/services/3D-luojia_mountain_demo/rest/realspace

scenes json:
http://localhost:8090/iserver/services/3D-luojia_mountain_demo/rest/realspace/scenes.json
```

## 7. 前端接入方式

完成发布后，不直接覆盖当前 `low_altitude_demo`，先新增一个候选配置：

```text
config/supermap_services.luojia.example.json
```

验收通过后再决定是否切换 `config/supermap_services.local.json`。

前端接入目标：

- 中央三维场景加载 `3D-luojia_mountain_demo`。
- 保留当前视觉自主导航指挥舱。
- 后续将 UAV 视觉帧和导航时间线绑定到珞珈山场景范围。

## 8. 验收清单

- [x] SuperMap 工作空间中已导入影像、DEM、建筑和地形点。
- [x] 三维场景保存为 `luojia_mountain_demo`。
- [x] iServer 发布 map/data/scene 服务。
- [x] `scenes.json` 返回 `luojia_mountain_demo`。
- [x] 后端 `/api/supermap/services` 返回珞珈山 scene/map/data verified。
- [ ] 建筑按 `HEIGHT_M` 拉伸效果仍需浏览器或 iDesktopX GUI 截图确认。
- [ ] 前端浏览器画面截图归档。
- [ ] 截图归档到 `docs/delivery/screenshots/`。
- [x] 项目日志记录服务 URL 和验收状态。

## 9. 当前限制

这批数据能解决三维场景和真实地理底座问题，但还不能单独解决视觉自主导航。

仍需补充：

- UAV 视角图像或视频帧。
- 每帧对应的时间戳。
- 每帧大致拍摄位置或参考真值。
- 视觉定位预计算结果或真实模型输出。
- 导航时间线数据。
