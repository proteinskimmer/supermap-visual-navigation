# 真实 / 半真实 Demo 数据采集任务书

本文用于下发给 GIS、视觉、材料组成员，指导他们为项目自建 `low_altitude_demo` 工作空间准备数据。目标不是一次性拿到完美真实数据，而是先拿到一套来源可说明、格式可导入、位置能对齐、可发布到 iServer 的比赛演示数据。

## 1. 交付目标

最终要形成：

```text
我们的数据 -> iDesktopX 工作空间 -> iServer 服务 -> 前端 iClient3D 加载
```

当前已经完成的是：

```text
SuperMap 内置 3D-CBD 样例 -> iServer -> iClient3D -> 前端工作台
```

下一步要替换为：

```text
low_altitude_demo 项目数据 -> iServer -> 前端工作台
```

## 2. 数据分级

### A 级：最低必交

没有这些数据，项目自建服务无法成立。

| 数据 | 数量 | 格式 | 用途 | 负责人建议 |
|---|---:|---|---|---|
| 任务区域边界 | 1 个 | GeoJSON / SHP / iDesktopX 手绘 | 定义规划范围 | GIS |
| 起点 | 1 个 | GeoJSON Point / 表格经纬度 | 航线起飞点 | GIS / 规划 |
| 终点 | 1 个 | GeoJSON Point / 表格经纬度 | 航线目标点 | GIS / 规划 |
| 风险区 | 至少 2 个 | GeoJSON Polygon / SHP | 风险校验、避障展示 | GIS / 规划 |
| 障碍物 | 至少 2 个 | GeoJSON Point 或 Polygon / SHP | 高楼、塔、禁入区等 | GIS / 规划 |
| 数据来源说明 | 1 份 | Markdown / Word | 答辩可信度 | 材料 / GIS |

### B 级：强烈建议

有这些数据，演示效果会明显更像真实系统。

| 数据 | 数量 | 格式 | 用途 |
|---|---:|---|---|
| 道路 | 1 层 | GeoJSON / SHP / OSM 导出 | 场景表达、路径解释 |
| 水系 / 湖泊 / 河流 | 1 层 | GeoJSON / SHP | 场景识别、视觉解释 |
| 建筑轮廓 | 1 层 | GeoJSON / SHP | 障碍物、高度风险解释 |
| 影像底图 | 1 份 | tif / tiff / iServer 地图服务 | 背景表达 |
| DEM / 高程 | 1 份 | tif / tiff / SuperMap 数据集 | 高程剖面、飞行高度解释 |

### C 级：加分项

有则加分，没有不阻塞主流程。

| 数据 | 数量 | 格式 | 用途 |
|---|---:|---|---|
| 真实或模拟无人机视角图 | 3 张以上 | jpg / png | 视觉匹配展示 |
| 倾斜摄影 / 三维模型 | 1 份 | SuperMap 三维缓存 / 3D Tiles / OSGB 等 | 真三维效果 |
| 真实建筑高度 | 若干 | 表格 / 属性字段 | 障碍物高度更可信 |
| 现场/公开截图 | 若干 | png / jpg | PPT 说明数据来源 |

## 3. 区域选择标准

优先选择：

- 面积适中：建议 `2 km x 2 km` 到 `8 km x 8 km`。
- 地物丰富：有道路、建筑、水系、绿地或开阔地。
- 适合低空巡检叙事：河道巡检、园区巡检、校园巡检、城区应急巡检都可以。
- 数据公开或可自制说明。
- 不涉及军事、机场、涉密设施、重点敏感区域。

不建议选择：

- 区域过大，导致三维加载慢。
- 地物太单一，例如纯农田或纯山地。
- 数据来源说不清。
- 与真实飞控、真实无人机执行强绑定的场景。

推荐叙事模板：

```text
任务名称：低空巡检示范任务
任务场景：无人机从起点出发，对河道 / 园区 / 城区边缘进行巡检，避开高风险区和障碍物，必要时动态重规划，并用视觉匹配辅助定位。
数据用途：比赛演示与软件仿真，不用于真实飞行。
```

## 4. 坐标和范围要求

所有数据优先使用：

```text
坐标系：WGS84
坐标顺序：[lon, lat, height]
经度：lon
纬度：lat
高度：height，单位 m
```

如果拿到的数据是 CGCS2000、Web Mercator 或其他坐标系，组员必须在提交说明中写明：

```text
原始坐标系：
是否已转换为 WGS84：
转换工具：
转换人：
```

禁止只交一堆文件但不说明坐标系。

## 5. 文件提交目录

组员提交数据时，统一放到：

```text
E:\supermap_project\data_sources\低空巡检示范区_YYYYMMDD\
```

建议结构：

```text
data_sources/
  低空巡检示范区_YYYYMMDD/
    README.md
    raw/
      原始下载或原始绘制文件
    processed/
      task_area.geojson
      start_target.geojson
      risk_zone.geojson
      obstacle.geojson
      road.geojson
      water.geojson
      building.geojson
    imagery/
      imagery.tif
      dem.tif
    vision/
      uav_view_001.jpg
      uav_view_002.jpg
      uav_view_003.jpg
      vision_metadata.csv
    screenshots/
      数据来源页面或处理过程截图
```

如果文件很大，不要直接塞进 Git。先放本地目录，最后由统筹决定是否进入提交包。

## 6. 必填字段规范

### task_area.geojson

几何类型：

```text
Polygon
```

字段：

| 字段 | 类型 | 必填 | 示例 | 说明 |
|---|---|---|---|---|
| `id` | string | 是 | `task_area_001` | 区域编号 |
| `name` | string | 是 | `低空巡检示范区` | 区域名称 |
| `source` | string | 是 | `manual_drawn` / `open_data` | 来源 |
| `note` | string | 否 | `用于比赛演示` | 备注 |

### start_target.geojson

几何类型：

```text
Point
```

字段：

| 字段 | 类型 | 必填 | 示例 | 说明 |
|---|---|---|---|---|
| `id` | string | 是 | `start_001` | 点编号 |
| `role` | string | 是 | `start` / `target` | 起点或终点 |
| `name` | string | 是 | `起飞点` | 展示名 |
| `height_m` | number | 是 | `120` | 规划飞行高度 |
| `note` | string | 否 | `开阔区域` | 备注 |

### risk_zone.geojson

几何类型：

```text
Polygon
```

字段：

| 字段 | 类型 | 必填 | 示例 | 说明 |
|---|---|---|---|---|
| `id` | string | 是 | `risk_001` | 风险区编号 |
| `name` | string | 是 | `临时施工区` | 展示名 |
| `type` | string | 是 | `construction` / `no_fly` / `crowd` / `power` / `weather` | 风险类型 |
| `level` | number | 是 | `4` | 风险等级，1 到 5 |
| `buffer_m` | number | 是 | `80` | 安全缓冲距离 |
| `active` | boolean | 是 | `true` | 是否启用 |
| `reason` | string | 是 | `施工吊装区域，建议绕行` | 风险解释 |

### obstacle.geojson

几何类型：

```text
Point 或 Polygon
```

字段：

| 字段 | 类型 | 必填 | 示例 | 说明 |
|---|---|---|---|---|
| `id` | string | 是 | `obs_001` | 障碍物编号 |
| `name` | string | 是 | `高层建筑` | 展示名 |
| `type` | string | 是 | `building` / `tower` / `bridge` / `crane` / `tree` | 类型 |
| `height_m` | number | 是 | `85` | 高度 |
| `buffer_m` | number | 是 | `50` | 安全缓冲 |
| `risk_level` | number | 否 | `3` | 风险等级 |
| `note` | string | 否 | `建议绕行` | 备注 |

### road.geojson / water.geojson / building.geojson

这些是增强图层，字段可以简化：

| 字段 | 类型 | 必填 | 示例 |
|---|---|---|---|
| `id` | string | 是 | `road_001` |
| `name` | string | 否 | `主干路` |
| `type` | string | 否 | `primary` / `river` / `building` |
| `source` | string | 是 | `OSM` / `manual_drawn` / `open_data` |

建筑如果有高度，增加：

```text
height_m
```

## 7. 视觉样例要求

视觉组至少准备 3 张图。真实航拍没有也可以先用模拟截图或公开图片，但必须能说明它对应哪个区域。

图片命名：

```text
uav_view_001.jpg
uav_view_002.jpg
uav_view_003.jpg
```

元数据文件：

```text
vision_metadata.csv
```

字段：

| 字段 | 必填 | 示例 | 说明 |
|---|---|---|---|
| `image_id` | 是 | `demo_uav_001` | 与系统 id 对应 |
| `file_name` | 是 | `uav_view_001.jpg` | 图片文件名 |
| `capture_lon` | 是 | `116.1701` | 拍摄中心经度 |
| `capture_lat` | 是 | `39.1602` | 拍摄中心纬度 |
| `height_m` | 是 | `120` | 拍摄高度 |
| `heading_deg` | 否 | `45` | 航向角 |
| `capture_time_s` | 是 | `74` | 仿真时间点 |
| `scene_tags` | 是 | `river,road,building` | 场景标签 |
| `source` | 是 | `simulated` / `public_image` / `real_uav` | 来源 |
| `note` | 否 | `用于视觉匹配演示` | 备注 |

视觉数据不能乱编成“真实航拍”。如果是公开图片或模拟图，必须如实标注。

## 8. 数据来源说明 README 模板

每个数据包必须带一个：

```text
README.md
```

内容按这个模板写：

```markdown
# 低空巡检示范区数据说明

## 区域

- 区域名称：
- 大致位置：
- 选择原因：
- 是否涉及敏感区域：否

## 坐标

- 坐标系：
- 坐标顺序：
- 是否经过坐标转换：

## 数据来源

| 数据 | 来源 | 获取方式 | 是否加工 | 备注 |
|---|---|---|---|---|
| 任务区域 | 手工绘制 / 公开数据 | iDesktopX 绘制 / 下载 | 是 / 否 | |
| 风险区 | 手工绘制 | 按演示场景设置 | 是 | |
| 障碍物 | 手工标注 / 建筑数据 | | 是 | |
| 道路 | OSM / 公开数据 | | 是 | |
| 水系 | OSM / 公开数据 | | 是 | |
| 影像 | 公开影像 / 样例 | | 否 | |
| DEM | 公开 DEM / 样例 | | 否 | |
| 视觉图片 | 模拟 / 公开 / 真实 | | 是 / 否 | |

## 用途声明

本数据仅用于比赛演示和软件仿真，不用于真实无人机飞行。

## 处理人

- 采集人：
- 整理人：
- 日期：
```

## 9. 验收标准

组员提交数据后，按下面检查。

### 必过检查

- [ ] 文件能打开，不是空文件。
- [ ] 坐标系说明存在。
- [ ] 任务区域是 Polygon。
- [ ] 起点和终点在任务区域内或边界附近。
- [ ] 风险区和障碍物能落在任务区域附近。
- [ ] `risk_zone` 字段包含 `id/name/type/level/buffer_m/active/reason`。
- [ ] `obstacle` 字段包含 `id/name/type/height_m/buffer_m`。
- [ ] README 写明数据来源和用途。
- [ ] 不包含敏感区域或无法说明来源的数据。

### iDesktopX 检查

- [ ] 可导入 iDesktopX。
- [ ] 各图层能叠加显示。
- [ ] 起终点、风险区、障碍物相对位置合理。
- [ ] 图层名称清楚。
- [ ] 样式便于截图展示。

### iServer 检查

- [ ] 工作空间能保存到：

```text
E:\supermap_project\supermap_file_root\demo_workspace
```

- [ ] 能发布地图服务或数据服务。
- [ ] 服务 URL 能在浏览器打开。
- [ ] 服务 URL 已记录到：

```text
docs/supermap_integration/04_service_url_registry_template.md
```

## 10. 最低交付包

如果时间很紧，组员最少交这个：

```text
processed/task_area.geojson
processed/start_target.geojson
processed/risk_zone.geojson
processed/obstacle.geojson
README.md
```

这个包就足够我们做：

```text
项目自建数据服务发布 + 前端服务 URL 替换 + 答辩说明
```

## 11. 分工建议

| 角色 | 任务 |
|---|---|
| GIS 组员 A | 选区域、整理任务边界、道路、水系、建筑 |
| GIS 组员 B | 整理风险区、障碍物、起终点，导入 iDesktopX |
| 视觉组员 | 准备 3 张视觉样例图和 `vision_metadata.csv` |
| 规划组员 | 检查起终点、风险区、障碍物是否适合航线规划 |
| 材料组员 | 整理 README、数据来源截图、答辩口径 |
| 统筹 | 验收字段、坐标、来源和可发布性 |

## 12. 给组员的交付口径

可以直接发：

```text
请按 docs/project_management/14_real_data_collection_guide.md 准备低空巡检 demo 数据。

优先交最低包：
1. task_area.geojson
2. start_target.geojson
3. risk_zone.geojson
4. obstacle.geojson
5. README.md

所有数据统一说明坐标系，优先 WGS84，经纬度顺序为 lon, lat。不要提交来源说不清或敏感区域数据。数据只用于比赛演示和软件仿真，不用于真实飞行。
```
