# iDesktopX 操作流程

## 0. 当前 demo 数据包

在 iDesktopX 已安装并能打开样例三维场景后，可以先使用本仓库导出的 demo GeoJSON 数据包制作任务区工作空间：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\export_demo_geojson.ps1
```

输出目录：

```text
demo_data/gis_export/
```

建议导入顺序：

1. `task_area.geojson`
2. `risk_zone.geojson`
3. `obstacle.geojson`
4. `vision_tile.geojson`
5. `start_target.geojson`
6. `routes_preview.geojson`
7. `vision_image_center.geojson`
8. `uav_position.geojson`

坐标系统一按 WGS84 经纬度处理。详细字段、样式和验收截图要求见 `09_idesktopx_demo_data_import.md`。

## 1. 目标

使用 SuperMap iDesktopX 2025 完成任务区域 GIS 数据整理、图层规范化、三维场景制作和工作空间保存，为 iServer 发布服务做准备。

## 2. 输入材料

| 数据 | 是否必需 | 说明 |
|---|---|---|
| 任务区域边界 | 是 | 面数据，限定规划范围 |
| 遥感影像 | 是 | 作为底图和视觉瓦片来源 |
| DEM 高程 | 是 | 用于地形和高程剖面 |
| 道路、水系、建筑物 | 建议 | 用于场景表达和风险解释 |
| 风险区、禁入区 | 是 | 可在 iDesktopX 中手工绘制 |
| 障碍物点/面 | 是 | 通信塔、高层建筑、地形危险点等 |
| 三维建筑模型 | 可选 | 有则增强效果 |

## 3. 推荐图层命名

| 图层名 | 几何类型 | 用途 |
|---|---|---|
| `task_area` | Polygon | 任务区域边界 |
| `risk_zone` | Polygon | 风险区/禁入区/临时风险区 |
| `obstacle` | Point/Polygon | 障碍物 |
| `road` | LineString | 道路 |
| `water` | Polygon/LineString | 水系 |
| `building` | Polygon/Model | 建筑 |
| `dem` | Raster | 高程 |
| `imagery` | Raster | 遥感影像 |

## 4. 字段规范

### risk_zone

| 字段 | 类型 | 示例 | 说明 |
|---|---|---|---|
| `id` | Text | `risk_fire_001` | 唯一编号 |
| `name` | Text | `山火风险区` | 中文名称 |
| `type` | Text | `fire` | `fire`、`landslide`、`no_fly`、`manual` |
| `level` | Int | `5` | 1 到 5 |
| `buffer_m` | Double | `120` | 安全缓冲距离 |
| `active` | Bool/Int | `1` | 是否启用 |

### obstacle

| 字段 | 类型 | 示例 | 说明 |
|---|---|---|---|
| `id` | Text | `obs_tower_001` | 唯一编号 |
| `name` | Text | `通信塔` | 中文名称 |
| `type` | Text | `tower` | `tower`、`building`、`terrain` |
| `height_m` | Double | `65` | 障碍物高度 |
| `buffer_m` | Double | `80` | 安全缓冲距离 |

## 5. 操作步骤

### 步骤 1：新建工程/工作空间

1. 打开 iDesktopX。
2. 新建或打开工作空间。
3. 新建数据源，建议命名为 `low_altitude_demo`。
4. 设置统一坐标系，优先使用 WGS84；如果公开数据使用投影坐标，记录 EPSG 编号。

交付：

- 工作空间文件。
- 坐标系说明。

### 步骤 2：导入基础数据

1. 导入任务区域边界。
2. 导入遥感影像。
3. 导入 DEM。
4. 导入道路、水系、建筑物等矢量数据。
5. 若坐标系不一致，进行坐标转换或配准。

检查：

- 影像、DEM、矢量图层能正确叠加。
- 图层没有明显偏移。

### 步骤 3：裁剪任务区域

1. 使用 `task_area` 对影像、DEM、矢量数据裁剪。
2. 删除或隐藏任务区域外无关数据。
3. 保持任务区域大小适中，建议 3 km x 3 km 到 10 km x 10 km。

检查：

- 前端加载不会过慢。
- 风险区和航线规划范围在同一边界内。

### 步骤 4：绘制风险区和障碍物

1. 新建 `risk_zone` 面图层。
2. 绘制至少 2 个固定风险区。
3. 填写 `id`、`name`、`type`、`level`、`buffer_m`、`active`。
4. 新建或整理 `obstacle` 图层。
5. 标注通信塔、高层建筑、危险地形等障碍物。

检查：

- 至少有一个高风险区能影响航线。
- 至少有一个障碍物能被风险校验解释。

### 步骤 5：制作三维场景

1. 创建三维场景。
2. 加载影像作为底图。
3. 加载 DEM 作为地形。
4. 添加风险区、障碍物、建筑、道路、水系。
5. 设置默认视角，能看到完整任务区域。
6. 设置风险区样式：高风险区红色，普通风险区黄色/橙色。

检查：

- 三维场景打开后能清楚看到任务区域。
- 风险区、障碍物、地形关系直观。

### 步骤 6：保存和交付

1. 保存工作空间。
2. 记录工作空间路径。
3. 导出或截图三维场景。
4. 将服务发布所需工作空间交给 iServer 发布负责人。

交付物：

- 工作空间路径。
- 数据源名称。
- 图层列表。
- 字段说明。
- 默认视角截图。

## 6. 常见问题

| 问题 | 处理 |
|---|---|
| 图层错位 | 检查坐标系和投影转换 |
| DEM 不显示 | 检查栅格格式、范围和三维场景地形配置 |
| 影像过大 | 裁剪任务区域或生成金字塔 |
| 风险区不明显 | 调整面样式、透明度和边界线 |
| 前端加载慢 | 缩小区域、降低模型复杂度、优先使用样例数据 |
