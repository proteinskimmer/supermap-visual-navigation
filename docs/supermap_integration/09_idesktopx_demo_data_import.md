# iDesktopX demo GeoJSON 数据导入说明

## 1. 当前结论

iDesktopX 已完成本机安装和样例三维场景验证后，当前可以继续做“demo GIS 数据入库和三维场景制作准备”。本步骤不依赖 iServer，也不代表服务发布完成。

已生成可导入数据包：

```text
demo_data/gis_export/
```

生成命令：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\export_demo_geojson.ps1
```

## 2. 数据清单

| 文件 | 几何 | 要素数 | 用途 |
|---|---:|---:|---|
| `task_area.geojson` | Polygon | 1 | 任务边界 |
| `risk_zone.geojson` | Polygon | 2 | 固定风险区 |
| `obstacle.geojson` | Point | 2 | 通信塔、高层建筑等障碍物 |
| `vision_tile.geojson` | Polygon | 5 | 视觉匹配候选瓦片 |
| `start_target.geojson` | Point | 2 | 起点和目标点 |
| `routes_preview.geojson` | LineString | 3 | 最短、安全、均衡三条预览航线 |
| `vision_image_center.geojson` | Point | 3 | 三张视觉样例的预期中心点 |
| `uav_position.geojson` | Point | 1 | 当前无人机 mock 位置 |

坐标口径：

- 坐标系：WGS84，经纬度。
- GeoJSON 轴顺序：`[longitude, latitude]`。
- 点和航线预览包含第三维高程，单位为米。
- 这些数据是 demo 矢量数据，不是真实 GIS 底座。

## 3. iDesktopX 导入顺序

1. 打开 iDesktopX，新建或打开项目工作空间。
2. 新建数据源，建议命名为 `low_altitude_demo`。
3. 依次导入 `demo_data/gis_export/` 下的 GeoJSON 文件。
4. 导入时坐标系选择 WGS84；如界面要求 EPSG，可记录为 EPSG:4326。
5. 导入完成后检查任务区、风险区、障碍物、瓦片、航线和点位是否叠加在同一范围内。
6. 保存工作空间，记录 `.smwu` 路径。

推荐保存路径：

```text
E:\supermap_project\supermap_file_root\demo_workspace\low_altitude_demo.smwu
```

注意：`3D-CBD` 是 SuperMap 官方样例，只用于证明链路可跑通。比赛项目服务应使用上面的 `low_altitude_demo.smwu` 发布。

## 4. 推荐图层样式

| 图层 | 样式建议 |
|---|---|
| `task_area` | 透明填充，蓝色或青色边界 |
| `risk_zone` | 按 `level` 做红/橙色半透明填充，边界加粗 |
| `obstacle` | 通信塔和建筑使用不同点符号，标注 `name` 和 `height_m` |
| `vision_tile` | 黄色边界、浅色透明填充，标注 `tile_id` |
| `routes_preview` | 按 `mode` 区分：`shortest` 灰色、`safest` 绿色、`balanced` 蓝色 |
| `start_target` | 起点绿色，目标点红色 |
| `vision_image_center` | 紫色或青色小点，标注视觉样例名称 |
| `uav_position` | 高亮当前无人机位置 |

## 5. 字段说明

### `risk_zone`

| 字段 | 说明 |
|---|---|
| `id` | 风险区唯一编号 |
| `name` | 风险区名称 |
| `risk_type` | 风险类型，例如 `fire`、`landslide` |
| `level` | 风险等级，1 到 5 |
| `buffer_m` | 安全缓冲距离 |
| `active` | 是否启用，1 表示启用 |

### `obstacle`

| 字段 | 说明 |
|---|---|
| `id` | 障碍物唯一编号 |
| `name` | 障碍物名称 |
| `obstacle_type` | 障碍物类型 |
| `altitude_m` | 点位高程 |
| `height_m` | 障碍物高度 |
| `buffer_m` | 安全缓冲距离 |

### `routes_preview`

| 字段 | 说明 |
|---|---|
| `id` | 预览航线编号 |
| `mode` | `shortest`、`safest`、`balanced` |
| `preview` | 1 表示演示预览线，不是真实算法最终结果 |
| `source` | 数据来源 |

## 6. 验收截图

完成导入后建议保存以下截图到 `docs/delivery/screenshots/`：

1. iDesktopX 数据源中已导入全部 demo 图层。
2. 二维视图中任务区、风险区、障碍物、瓦片和航线正常叠加。
3. 三维场景中能看到任务区范围和关键点线面。
4. 工作空间保存路径截图或记录。

## 7. 后续衔接

- iServer 安装完成后，使用保存好的 iDesktopX 工作空间发布三维服务。
- 发布后把真实 `sceneUrl` 写入 `config/supermap_services.local.json` 或前端环境变量。
- 前端承载层已经预留 `scene.open(sceneUrl)`，服务 URL 出来后不用大改结构。
- 当前状态只能表述为“demo GeoJSON 数据包已生成，可用于 iDesktopX 导入和场景制作准备”；不能表述为“真实 SuperMap 服务已发布”。

发布前检查：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\check_low_altitude_demo_publish_ready.ps1
```
