# SuperMap 服务地址记录模板

本模板用于记录 iServer 发布结果。每次发布或变更服务地址后，都应更新本文件，并同步到 `config/supermap_services.local.json`。

## 1. 基础信息

| 项目 | 内容 |
|---|---|
| iServer 根地址 | `http://localhost:8090/iserver` |
| iServer 管理地址 | `http://localhost:8090/iserver/admin-ui/home` |
| iServer 文件管理根目录 | `E:\supermap_project\supermap_file_root` |
| 工作空间路径 | `E:\supermap_project\supermap_file_root\demo_workspace\low_altitude_demo.smwu` |
| 数据源名称 | `low_altitude_demo` |
| 坐标系 | 待填写 |
| 发布日期 | 待填写 |
| 发布负责人 | 待填写 |

## 2. 服务清单

| 服务类型 | 服务名称 | URL | 状态 | 前端接入 | 后端接入 | 备注 |
|---|---|---|---|---|---|---|
| 三维服务 | `3D-CBD` | `http://localhost:8090/iserver/services/3D-CBD/rest/realspace` | Integrated | Integrated | 不需要 | iServer 内置 CBD 三维样例；前端 `scene.open` 已截图确认 |
| 三维服务 | `3D-low_altitude_demo` | `http://localhost:8090/iserver/services/3D-low_altitude_demo/rest/realspace` | Todo | Todo | 不需要 | 项目自建 demo 三维服务；用于替换 `3D-CBD` |
| 地图服务 | `map-low_altitude_demo` | `http://localhost:8090/iserver/services/map-low_altitude_demo/rest/maps` | Todo | Todo | 可选 | 项目任务区和业务图层地图服务 |
| 数据服务 | `data-low_altitude_demo` | `http://localhost:8090/iserver/services/data-low_altitude_demo/rest/data` | Todo | 可选 | Todo | 风险区、障碍物、任务区、视觉瓦片、预览航线 |
| 空间分析服务 | 待填写 | 待填写 | Optional | 不需要 | Optional | 缓冲区/叠加分析 |

状态可选：

- `Todo`：未发布。
- `Published`：已发布但未验证。
- `Verified`：浏览器可访问。
- `Integrated`：已接入项目。
- `Failed`：发布失败。
- `Optional`：可选项。

## 3. 图层/数据集记录

| 数据集 | 服务来源 | 几何类型 | 字段 | 用途 | 验证状态 |
|---|---|---|---|---|---|
| `task_area` | 数据服务 | Polygon | `id,name` | 规划范围 | Todo |
| `risk_zone` | 数据服务 | Polygon | `id,name,type,level,buffer_m,active` | 风险校验和展示 | Todo |
| `obstacle` | 数据服务 | Point/Polygon | `id,name,type,height_m,buffer_m` | 障碍物校验 | Todo |
| `road` | 数据服务/地图服务 | LineString | 待填写 | 场景表达 | Todo |
| `water` | 数据服务/地图服务 | Polygon/LineString | 待填写 | 场景表达 | Todo |
| `building` | 数据服务/三维服务 | Polygon/Model | 待填写 | 场景表达/障碍 | Todo |

## 4. 验证记录

| 日期 | 服务/图层 | 验证方式 | 结果 | 问题 |
|---|---|---|---|---|
| 待填写 | 待填写 | 浏览器打开 URL | 待填写 | 待填写 |
| 2026-06-09 | iServer 初始化向导 | 浏览器完成页 | 已完成；文件管理根目录为 `E:\supermap_project\supermap_file_root` | JVM 内存建议暂未调整，后续发布三维服务如卡顿再处理 |
| 2026-06-09 | `3D-CBD` 三维服务根节点 | 浏览器打开 `http://localhost:8090/iserver/services/3D-CBD/rest/realspace` | 已显示 `三维服务根节点(3D)`，包含 `datas`、`scenes`、`symbols` 子资源 | 前端 WebGL 加载截图已完成 |
| 2026-06-09 | `CBD` 场景元数据 | 命令行请求 `scenes/CBD.json` | HTTP 200，返回 `CBD` 场景 JSON 和三维图层信息 | 无 |
| 2026-06-09 | iClient3D 最小验证页 | 浏览器打开 `supermap-minimal.html?sceneUrl=...3D-CBD...` | WebGL2、SDK、Viewer、实体点和 `scene.open(sceneUrl)` 均成功；`3D-CBD` 城市场景已渲染 | 截图文件待正式归档 |
| 2026-06-09 | 项目工作台 SuperMap 模式 | 浏览器打开 `http://localhost:5173/` | `SuperMap 场景已就绪`，真实三维场景上已叠加候选航线、风险区、视觉候选区和起终点 | 截图文件待正式归档 |
| 2026-06-09 | 项目 demo 发布前检查 | 运行 `scripts\check_low_altitude_demo_publish_ready.ps1` | GeoJSON 数据包齐全，目标配置模板已指向 `low_altitude_demo` | `low_altitude_demo.smwu` 尚未由 iDesktopX 保存，项目服务尚未发布 |

## 5. 截图记录

| 截图 | 路径 | 用途 |
|---|---|---|
| iServer 管理页面 | 待填写 | 部署说明 |
| 三维服务发布成功 | 待填写 | PPT/答辩 |
| 前端加载三维场景 | 对话截图已确认，正式文件待保存到 `docs/delivery/screenshots/` | 演示材料 |

## 2026-06-09 low_altitude_demo 项目服务发布记录

### 发布结果

| 服务 | URL | 验收结果 | 状态口径 |
|---|---|---|---|
| `map-low_altitude_demo` | `http://localhost:8090/iserver/services/map-low_altitude_demo/rest/maps` | HTTP 200；`maps.json` 返回 `[]` | 已发布，但工作空间尚未保存地图对象，暂记为 `published_no_maps` |
| `data-low_altitude_demo` | `http://localhost:8090/iserver/services/data-low_altitude_demo/rest/data` | HTTP 200；`datasources.json` 可见 `low_altitude_demo` | 已发布并完成数据服务验收，记为 `verified` |

### 数据集验收

`data-low_altitude_demo` 已返回 8 个数据集：

```text
obstacle_ZP
routes_preview_ZL
start_target_ZP
task_area_R
uav_position_ZP
vision_image_center_ZP
risk_zone_R
vision_tile_R
```

### 配置同步

已更新 `config/supermap_services.local.json`：

- `workspace_path` 指向 `E:\supermap_project\supermap_file_root\demo_workspace\low_altitude_demo.smwu`。
- `services.data` 指向 `data-low_altitude_demo`，状态为 `verified`。
- `services.map` 指向 `map-low_altitude_demo`，状态为 `published_no_maps`。
- `services.scene` 仍保留官方样例 `3D-CBD`，状态为 `verified`，用于三维底座链路；项目自建 `3D-low_altitude_demo` 尚未发布。

### 下一门禁

若需要让地图服务返回具体地图，需要回到 iDesktopX，把 8 个数据集叠加成一张地图并保存到工作空间，再在 iServer 中刷新/重启对应服务。否则当前阶段可先使用数据服务作为项目自建 GIS 服务验收证据。
### 2026-06-09 low_altitude_demo 地图服务完整验收

- 用户已在 iDesktopX 中将 8 个项目数据集加入地图 `low_altitude_demo_map`，并保存工作空间。
- REST 验收通过：`http://localhost:8090/iserver/services/map-low_altitude_demo/rest/maps/low_altitude_demo_map.json` 返回 WGS84 / EPSG:4326 地图元数据，`bounds` 为 `left=116.1, bottom=39.1, right=116.235, top=39.215`。
- 图层验收通过：`layers.json` 中可见 8 个业务图层，包含 `task_area_R`、`risk_zone_R`、`obstacle_ZP`、`vision_tile_R`、`start_target_ZP`、`routes_preview_ZL`、`vision_image_center_ZP`、`uav_position_ZP`。
- 已更新 `config/supermap_services.local.json`：`services.map.status=verified`，并补充 `resource_url` 与 `metadata_url`。
- 已复跑 `scripts/check_low_altitude_demo_publish_ready.ps1`：map/data 服务均为 `verified`，地图服务拥有 1 个地图资源，数据服务 8 个数据集齐全。
- 当前严格口径：项目自建 SuperMap map/data 服务已完成发布与 REST 验收；项目自建三维场景 `3D-low_altitude_demo` 尚未发布，前端三维底座仍使用官方 `3D-CBD`。