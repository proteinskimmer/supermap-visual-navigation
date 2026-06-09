# 项目任务看板

更新日期：2026-06-09

## 状态说明

- `Todo`：未开始。
- `Doing`：进行中。
- `Mock Done`：mock 数据或代码初稿完成，未完成真实运行验收。
- `Runtime Verified`：依赖安装、测试、构建或页面运行已验证。
- `SuperMap Verified`：真实 SuperMap 服务和三维接入已验证。
- `Delivery Draft`：交付材料底稿完成，截图/PPT/视频未最终生成。
- `Delivery Ready`：提交材料和彩排已完成。
- `Blocked`：阻塞，需要协作解决。

## 当前总目标

项目重新定位为：基于 SuperMap GIS 三维底座的无人机视觉自主导航仿真系统。系统必须以“UAV 视觉帧 -> 视觉地理重定位 -> 后端融合导航状态 -> 三维无人机与遥测同步推进 -> 风险/重规划/报告”为主线。

当前严格状态：

- SuperMap scene/map/data 接口级闭环：`SuperMap Verified`。
- 指挥舱 UI 初稿：`Mock Done`。
- 视觉匹配预计算演示：`Mock Done`。
- 后端权威视觉自主导航状态机：`Runtime Verified`。
- 真实 UAV 图像、DOM/DEM、真实视觉模型：`Todo`。
- PPT、视频、最终彩排：`Todo`。

## R0 主线纠偏与范围冻结

| ID | 任务 | 负责人 | 状态 | 依赖 | 验收标准 |
|---|---|---|---|---|---|
| R0-01 | 冻结项目主线为视觉自主导航 | 统筹 | Done | 无 | 文档明确主线不是航线动画，也不是单纯视觉辅助展示 |
| R0-02 | 保留视觉辅助导航作为降级/扩展模式 | 统筹/视觉/前端 | Done | R0-01 | 低置信、人工复核、GNSS 对照、演示兜底均归入辅助模式 |
| R0-03 | 建立严格答辩口径 | 统筹/材料 | Done | R0-01 | 不宣称真实飞控、真实自主控制、真实精细三维模型 |
| R0-04 | 新增重规划总纲 | 统筹 | Done | R0-01 | `docs/project_management/16_visual_autonomous_navigation_replan.md` 已创建 |

## R1 SuperMap/GIS 底座

| ID | 任务 | 负责人 | 状态 | 依赖 | 验收标准 |
|---|---|---|---|---|---|
| R1-01 | iDesktopX 2025 安装验收 | GIS/统筹 | Runtime Verified | 无 | 主程序、许可、样例工作空间和三维场景已验收 |
| R1-02 | iServer 2025U1A 安装验收 | GIS/统筹 | Runtime Verified | 无 | `8090`、管理页、服务列表、帮助页 HTTP 验收通过 |
| R1-03 | iClient3D SDK 验收 | 前端/统筹 | SuperMap Verified | 无 | WebGL2、Viewer、`scene.open` 和本地 SDK 资源验收通过 |
| R1-04 | 生成 demo GeoJSON 数据包 | GIS/统筹 | Runtime Verified | demo 数据 | `demo_data/gis_export/` 已生成并可导入 |
| R1-05 | 制作 `low_altitude_demo` 工作空间 | GIS | Runtime Verified | R1-04 | `low_altitude_demo.smwu` 和 `low_altitude_demo.udbx` 已保存 |
| R1-06 | 发布项目自建 map/data/scene 服务 | GIS | SuperMap Verified | R1-05 | `map-low_altitude_demo`、`data-low_altitude_demo`、`3D-low_altitude_demo` REST 验收通过 |
| R1-07 | 前端读取项目自建 SuperMap 服务 | 前端/后端 | SuperMap Verified | R1-06 | `/api/supermap/services` 返回 scene/map/data 三项 `verified` |
| R1-08 | 维护 SuperMap 服务 URL 与截图证据 | 统筹/GIS | SuperMap Verified | R1-06 | `check_supermap_goal_evidence.ps1 -Strict` 通过 |
| R1-09 | 替换真实/半真实 DOM、DEM、建筑与地物数据 | GIS | SuperMap Verified | 数据采集 | 珞珈山正射影像、DEM、地形点和建筑面已导入 `luojia_mountain_demo.smwu`，并发布 map/data/3D 服务 |

## R2 后端视觉自主导航状态机

| ID | 任务 | 负责人 | 状态 | 依赖 | 验收标准 |
|---|---|---|---|---|---|
| R2-01 | 定义导航状态数据模型 | 后端/统筹 | Runtime Verified | R0 | 已新增 `NavigationStateFrame`，包含 `reference_position`、`visual_position`、`fused_position`、`telemetry`、`navigation_mode`、`active_event` |
| R2-02 | 新增 `VisualNavigationService` | 后端 | Runtime Verified | R2-01 | 已可根据时间返回后端权威 UAV 状态 |
| R2-03 | 新增导航会话接口 | 后端 | Runtime Verified | R2-02 | `POST /api/navigation/start` 可创建 session 并返回时间线 |
| R2-04 | 新增单帧状态接口 | 后端 | Runtime Verified | R2-02 | `GET /api/navigation/state` 可按 `session_id` 和 `time_s` 返回状态 |
| R2-05 | 新增完整时间线接口 | 后端 | Runtime Verified | R2-02 | `GET /api/navigation/timeline` 返回连续状态序列 |
| R2-06 | 接入视觉定位结果 | 后端/视觉 | Runtime Verified | R2-02/R3 | 预计算视觉匹配 Top1 已转换为 `visual_position` 和视觉帧 |
| R2-07 | 实现状态融合规则 | 后端/视觉 | Runtime Verified | R2-06 | 高置信进入自主融合，中置信进入辅助，低置信进入复核 |
| R2-08 | 后端生成遥测与事件流 | 后端 | Runtime Verified | R2-02 | 速度、高度、航向、姿态、电量、定位源和事件均由后端时间线生成 |
| R2-09 | 后端导航状态测试 | 后端 | Runtime Verified | R2-01 至 R2-08 | pytest 已覆盖高置信、偏差修正、低置信复核、风险事件和重规划触发 |

## R3 视觉定位与演示数据

| ID | 任务 | 负责人 | 状态 | 依赖 | 验收标准 |
|---|---|---|---|---|---|
| R3-01 | 整理 UAV 视觉帧元数据 | 视觉 | Mock Done | 无 | 已有占位图元数据，需升级为导航时间线输入 |
| R3-02 | 补真实或半真实 UAV 图像文件 | 视觉/数据 | Todo | 数据采集 | 至少 4 帧：高置信、正常、偏差修正、低置信 |
| R3-03 | 建立正射影像/瓦片索引 | 视觉/GIS | Mock Done | R1 | 每个瓦片有边界、中心、特征数量、来源说明 |
| R3-04 | 输出预计算视觉定位结果 | 视觉 | Mock Done | R3-01/R3-03 | 结果包含位置、置信度、匹配点、内点率、偏差 |
| R3-05 | 新增 `visual_localization_frames` 数据段 | 后端/视觉 | Runtime Verified | R3-01/R3-04 | 已由 `VisualLocalizationResult` + `NavigationVisualFrame` 承载，每帧可映射到导航时间、图像、视觉位置和解释 |
| R3-06 | 保留真实模型 provider 接口 | 视觉/后端 | Mock Done | R3-04 | DINOv2、LoFTR、LightGlue、OpenCV/RANSAC 可后续替换 |
| R3-07 | 视觉定位入链验收 | 视觉/后端 | Runtime Verified | R2/R3 | 合成视图视觉定位结果已写入 `visual_position`、`visual_frame` 和 `fused_position`，可驱动后端导航状态 |

## R4 前端指挥舱状态消费端

| ID | 任务 | 负责人 | 状态 | 依赖 | 验收标准 |
|---|---|---|---|---|---|
| R4-01 | 指挥舱布局初稿 | 前端 | Mock Done | R1 | 已转为视觉自主导航指挥舱风格，`npm run build` 通过 |
| R4-02 | 播放逻辑改为读取后端时间线 | 前端/后端 | Runtime Verified | R2-05 | 前端播放光标消费 `/api/navigation/start` 返回的 timeline，不再自行推算 UAV 主状态 |
| R4-03 | 三维无人机绑定 `fused_position` | 前端 | Runtime Verified | R2-04 | `SuperMapScene` 的 `currentPoint` 已来自后端 `fused_position` |
| R4-04 | 遥测面板绑定后端状态 | 前端 | Runtime Verified | R2-08 | 高度、速度、航向、姿态、电量等来自后端 `telemetry` |
| R4-05 | UAV 实时影像帧与时间同步 | 前端/视觉 | Runtime Verified | R3-05 | 播放到对应时间时按 `active_frame_id` 显示对应 UAV frame |
| R4-06 | 展示参考/视觉/融合位置关系 | 前端 | Runtime Verified | R2-04 | 视觉定位面板展示参考、视觉、融合三组坐标和偏差 |
| R4-07 | 事件流绑定后端事件 | 前端/后端 | Runtime Verified | R2-08 | 视觉定位、风险、复核、重规划待命事件来自后端时间线 |
| R4-08 | 标准视角与三维交互体验 | 前端 | Runtime Verified | R1 | 已有标准视角、滚轮灵敏度优化和演示级建筑/UAV 效果 |
| R4-09 | 连续飞行与轨迹对比 | 前端/后端 | Runtime Verified | R2-05/R4-03 | 前端播放已从最近帧跳变改为帧间插值；3D 和 fallback 地图均展示参考轨迹与融合实际轨迹 |
| R4-10 | iServer 不可用时本地底座兜底 | 前端/GIS | Runtime Verified | R1/R6 | 前端先绘制本地 Luojia DEM/正射影像/建筑底座，再异步尝试打开 iServer scene；DOM/截图门禁通过 |

## R5 航线规划、风险与重规划支撑服务

| ID | 任务 | 负责人 | 状态 | 依赖 | 验收标准 |
|---|---|---|---|---|---|
| R5-01 | 参考航线生成 | 规划/后端 | Mock Done | R1 | 可生成最短、安全、综合三条候选航线 |
| R5-02 | 风险评分与高程剖面 | 规划/后端 | Mock Done | R1 | 可输出评分、风险段、原因和剖面 |
| R5-03 | 从 `fused_position` 判断风险 | 后端/规划 | Mock Done | R2 | 导航时间线已基于 `fused_position`/视觉位置生成风险事件，仍需扩展真实安全策略 |
| R5-04 | 临时风险区触发重规划 | 后端/规划 | Mock Done | R5-01 | 需升级为从当前融合位置接续 |
| R5-05 | 重规划结果写入导航事件 | 后端 | Mock Done | R2/R5-04 | 导航时间线已输出 `replan_ready`，`/api/navigation/replan` 可从当前融合位置生成接续航线 |
| R5-06 | 新旧航线三维对比 | 前端 | Mock Done | R4/R5 | 三维场景能区分参考航线、受影响航段和新航线 |

## R6 数据准备

| ID | 任务 | 负责人 | 状态 | 依赖 | 验收标准 |
|---|---|---|---|---|---|
| R6-01 | 确定真实或半真实任务区域 | GIS/统筹 | Runtime Verified | 无 | 已采用珞珈山区域，坐标系为 EPSG:4547 |
| R6-02 | 准备 DOM/遥感底图 | GIS/数据 | SuperMap Verified | R6-01 | `luojia_ortho` 已导入并发布 |
| R6-03 | 准备 DEM/高程数据 | GIS/数据 | SuperMap Verified | R6-01 | `luojia_dem` 已导入、作为 terrain 写入三维场景并发布 |
| R6-04 | 准备道路、水系、建筑、风险区矢量 | GIS/数据 | Runtime Verified | R6-01 | 已准备建筑面 `luojia_buildings_3d` 和地形点 `luojia_terrain_points`；道路/水系/风险区仍需按任务补充 |
| R6-05 | 准备 UAV 视角图或视频帧 | 视觉/数据 | Todo | R6-01 | 文件入库，命名与 `visual_localization_frames` 对应 |
| R6-06 | 准备数据来源说明 | 数据/材料 | Todo | R6-02 至 R6-05 | 每份数据有来源、时间、坐标系、用途和限制说明 |

## R7 交付材料与最终彩排

| ID | 任务 | 负责人 | 状态 | 依赖 | 验收标准 |
|---|---|---|---|---|---|
| R7-01 | 更新系统设计文档 | 材料/统筹 | Delivery Draft | R0 | 主线改为视觉自主导航，规划/风险为支撑服务 |
| R7-02 | 更新接口和数据契约 | 后端/材料 | Runtime Verified | R2/R3 | `09_interfaces_and_data_contracts.md` 已补导航接口、状态字段和时间线字段 |
| R7-03 | 更新部署说明 | 后端/前端/材料 | Delivery Draft | R1 | 一键启动脚本和依赖说明清楚 |
| R7-04 | 制作完整演示截图 | 全体 | Todo | R2 至 R5 | 按截图清单命名并归档 |
| R7-05 | 制作 PPT | 材料/统筹 | Todo | R7-01/R7-04 | 不夸大真实能力，突出视觉自主导航链路 |
| R7-06 | 录制演示视频 | 材料/全体 | Todo | R2 至 R5 | 视频围绕视觉导航状态闭环，不以单纯动画为主 |
| R7-07 | 最终提交包 | 统筹/材料 | Todo | R7-05/R7-06 | 代码、文档、截图、视频、PPT、复验脚本齐全 |
| R7-08 | 三次完整彩排 | 全体 | Todo | R7-07 | 连续 3 次按脚本演示成功 |

## 立即执行优先级

1. `R2` 后端视觉自主导航状态机。
2. `R3-05` 补导航时间线与视觉帧数据。
3. `R4-02` 至 `R4-07` 前端改为消费后端状态。
4. `R5-03` 和 `R5-05` 风险/重规划接入融合位置与事件流。
5. `R6` 真实或半真实数据替换。
6. `R7` 截图、PPT、视频、彩排。
