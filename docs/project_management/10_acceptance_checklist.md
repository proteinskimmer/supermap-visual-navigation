# 阶段验收与最终提交清单

更新日期：2026-06-09

## 总验收原则

本项目验收主线是视觉自主导航软件仿真闭环。只有当 UAV 位置、遥测、视觉帧、置信度、事件流和重规划都由同一条后端导航时间线驱动时，才可以称为“视觉自主导航演示闭环”。

当前不能把前端动画、视觉候选区高亮或航线播放单独包装成完整闭环。

## 当前已通过证据

- [x] iDesktopX 2025 本机安装、许可状态和样例三维场景已验收。
- [x] iServer 2025U1A 本机安装、8090 端口、管理页、服务列表和帮助页已验收。
- [x] iClient3D SDK、WebGL2、Viewer 创建和 `scene.open(sceneUrl)` 已验收。
- [x] 项目自建 `low_altitude_demo.smwu` 工作空间已保存。
- [x] 项目自建 `map-low_altitude_demo` 地图服务已发布。
- [x] 项目自建 `data-low_altitude_demo` 数据服务已发布 8 个业务数据集。
- [x] 项目自建 `3D-low_altitude_demo` 三维服务已发布，`scenes.json` 可访问并包含 `low_altitude_demo` 场景标记。
- [x] 前端/后端 SuperMap 配置已切换为项目自建 scene/map/data 服务。
- [x] `/api/supermap/services` 三项状态为 `verified`。
- [x] 珞珈山 `map-luojia_mountain_demo`、`data-luojia_mountain_demo`、`3D-luojia_mountain_demo` 已发布并通过 REST 门禁。
- [x] 前端/后端 SuperMap 配置已切换为珞珈山 scene/map/data 服务。
- [x] `scripts/check_supermap_goal_evidence.ps1 -Strict` 通过。
- [x] `scripts/check_project_runtime.ps1` 曾通过，包含前端 build、后端测试和增强 smoke。
- [x] 一键启动/停止脚本已建立。
- [x] 指挥舱 UI 初稿已完成并通过 `npm run build`。

## 当前完成与禁止夸大边界

- [x] 后端权威视觉自主导航状态机已完成 R2 mock/runtime 版本。
- [x] UAV 三维位置已由后端 `fused_position` 驱动。
- [x] 遥测、视觉帧、事件流已由后端统一时间线驱动。
- [ ] 视觉输入仍主要是演示占位或预计算数据，不是真实在线视觉模型。
- [ ] 真实 UAV 图像、DOM/DEM、真实视觉定位数据尚未全部入库。
- [ ] PPT、演示视频、最终提交包和 3 次完整彩排尚未完成。

## R0 主线纠偏验收

- [x] 项目定位改为“视觉自主导航仿真系统”。
- [x] 航线规划、风险校验、重规划定位为支撑服务。
- [x] 视觉辅助导航作为降级/扩展模式保留。
- [x] 材料口径禁止暗示真实飞控或真实无人机控制。
- [x] 新增重规划总纲并写入项目管理文档。

## R1 SuperMap/GIS 底座验收

- [x] iDesktopX 可用。
- [x] iServer 可用。
- [x] iClient3D SDK 可用。
- [x] 项目自建 map/data/scene 服务可访问。
- [x] 前端读取项目自建 SuperMap 服务。
- [x] 服务地址和截图证据已归档。
- [x] 真实或半真实 DOM/DEM/建筑/地物数据替换完成。
- [ ] 材料中清楚说明当前三维建筑效果是演示级表达。

## R2 后端视觉自主导航状态机验收

- [x] 已定义导航状态模型。
- [x] 状态模型包含 `reference_position`。
- [x] 状态模型包含 `visual_position`。
- [x] 状态模型包含 `fused_position`。
- [x] 状态模型包含 `telemetry`。
- [x] 状态模型包含 `navigation_mode`。
- [x] 状态模型包含 `active_frame_id`、`active_route_id`、`active_event`。
- [x] `POST /api/navigation/start` 可创建导航会话。
- [x] `GET /api/navigation/state` 可按时间返回单帧状态。
- [x] `GET /api/navigation/timeline` 可返回完整时间线。
- [x] 视觉匹配结果可转换为视觉定位结果。
- [x] 高置信视觉定位可驱动 `autonomous` 状态。
- [x] 低置信视觉定位可驱动 `assisted` 或 `review` 状态。
- [x] 后端能输出偏差距离 `deviation_m`。
- [x] 后端能生成遥测数据。
- [x] 后端能生成视觉定位、风险、重规划待命等事件。
- [x] pytest 覆盖高置信、低置信、偏差修正、风险事件和重规划触发。

## R3 视觉定位与数据验收

- [x] 至少已有 3 张示例输入图元数据。
- [x] 至少已有 1 张低置信度/需人工复核样例。
- [x] 已有候选瓦片索引。
- [x] 已有预计算匹配结果。
- [x] 结果包含置信度、匹配点或可解释指标。
- [ ] 至少 4 张真实或半真实 UAV 视角图文件入库。
- [x] 每张图能对应到一个 `time_s`。
- [x] 每张图能对应到一个视觉估计位置。
- [x] 每张图能对应到一个导航状态。
- [ ] 数据中包含高置信、正常置信、偏差修正、低置信复核四类样例。
- [ ] 数据来源说明完整，包括来源、坐标系、用途和限制。

## R4 前端指挥舱验收

- [x] 指挥舱 UI 初稿可构建。
- [x] 三维场景标准视角按钮可用。
- [x] 滚轮缩放和三维交互体验已优化。
- [x] 演示级 3D 建筑和空中 UAV 效果已加入。
- [x] 播放控制读取后端导航时间线。
- [x] UAV 三维位置绑定 `fused_position`。
- [x] 遥测面板数据来自后端状态。
- [x] UAV 影像帧与时间线同步。
- [x] 视觉定位面板显示参考位置、视觉位置和融合位置关系。
- [x] 播放时 UAV 位置由前端帧间插值连续推进，不再只按后端离散帧跳变。
- [x] 三维场景和 fallback 地图均能展示参考轨迹与融合实际轨迹对比。
- [x] iServer 未启动或 scene 打开超时时，前端仍能加载本地 Luojia DEM/正射影像/建筑仿真底座。
- [x] 事件流由后端事件驱动。
- [x] 低置信帧进入辅助/复核状态时前端有明确提示。
- [x] 用户能从界面看懂“仿真播放是在回放视觉自主导航状态链路”。

## R5 航线规划、风险与重规划验收

- [x] 已有候选航线 mock/演示数据。
- [x] 已有风险评分和高程剖面 mock/演示数据。
- [x] 已有临时风险区和重规划演示框架。
- [x] 风险判断基于当前 `fused_position` 或视觉定位位置生成导航事件。
- [x] `/api/navigation/replan` 可从当前 `fused_position` 接续。
- [x] 后端导航事件流包含风险和重规划待命事件；实际重规划按钮调用 `/api/navigation/replan` 生成事件。
- [ ] 前端能展示参考航线、受影响航段和新航线。
- [ ] 报告能解释风险触发原因和重规划结果。

## R6 数据准备验收

- [x] 真实或半真实任务区域已确定。
- [x] DOM/遥感底图已准备。
- [x] DEM/高程数据已准备。
- [ ] 建筑矢量已准备；道路、水系、风险区仍需按任务剧情补充。
- [ ] UAV 视角图或视频帧已准备。
- [ ] 相机高度、视角、时间戳或近似拍摄参数已准备。
- [ ] 数据目录、命名、字段说明符合 `14_real_data_collection_guide.md`。
- [x] 数据可导入 iDesktopX 或被后端读取。
- [x] 珞珈山数据已导入 SuperMap 工作空间并由 iServer 发布。

## R7 交付材料验收

- [ ] 系统设计文档已按视觉自主导航主线更新。
- [ ] 接口和数据契约已包含导航状态接口。
- [ ] 部署说明可指导新环境启动。
- [ ] 截图按清单命名并归档。
- [x] 报告页摘要截图已命名归档：`docs/delivery/screenshots/v05_report_page_summary_route_risk_profile.png`。
- [ ] PPT 完成。
- [ ] 演示视频完成。
- [ ] 最终提交包完成。
- [ ] 所有截图、视频、PPT 使用同一套稳定 demo 数据。
- [ ] 连续 3 次完整彩排成功。

## 最终 Demo 必过流程

1. 打开系统并加载项目自建 SuperMap 三维场景。
2. 选择视觉自主导航演示任务。
3. 启动导航会话，后端返回 `session_id`。
4. 前端读取导航时间线。
5. 展示参考航线和任务区域。
6. 开始播放，UAV 按 `fused_position` 连续运动。
7. UAV 影像帧、遥测、视觉置信度和事件流同步变化。
8. 高置信帧中系统显示视觉自主定位成功。
9. 偏差帧中系统显示视觉定位修正导航状态。
10. 低置信帧中系统进入辅助/复核模式。
11. 临时风险区触发安全判断。
12. 系统从当前融合位置重规划。
13. 三维场景展示参考航线、受影响航段和新航线。
14. 生成任务报告。
15. 答辩说明当前是软件仿真，不接真实飞控。

## 一票否决风险

- [ ] 演示时 SuperMap 三维场景无法加载。
- [ ] UAV 位置与后端导航状态不一致。
- [ ] 遥测、影像帧、事件流互相不同步。
- [ ] 视觉结果只在地图上高亮，不能进入导航状态。
- [ ] 重规划不是从当前融合位置接续。
- [ ] 前后端启动步骤只有开发者本人知道。
- [ ] PPT 中承诺了系统没有实现的功能。
- [ ] 材料暗示真实飞控或真实执行能力。
## 2026-06-09 自动视觉瓦片验收补充

- [x] 珞珈山真实正射影像已作为视觉参考瓦片生成源。
- [x] `scripts/generate_luojia_vision_tiles.py` 可重复生成瓦片索引。
- [x] `vision_tile_index` 已由自动生成的 40 个瓦片替换原 5 个手写瓦片。
- [x] 每个瓦片包含 WGS84 `bbox`、`center`、源影像 `pixel_bbox` 和前端 PNG 缩略图。
- [x] 预计算视觉匹配候选已重新绑定到自动生成瓦片。
- [x] `/api/vision/tiles?task_id=task_001` 返回自动瓦片元数据。
- [x] `vision_tile.geojson` 已按自动瓦片重导出。
- [ ] 真实在线视觉模型推理尚未接入，当前仍为预计算匹配结果。

## 2026-06-09 合成视图视觉自主导航 v0.4 验收补充

- [x] 瓦片已降级为候选区域粗检索和调试索引。
- [x] 已新增 `POST /api/vision/synthetic-views`。
- [x] 已新增 `POST /api/vision/localize`。
- [x] 已新增 `GET /api/vision/localizations/{image_id}`。
- [x] 合成视图候选包含相机位姿、DEM 高程、正射影像来源和建筑上下文。
- [x] 视觉定位结果包含估计位姿、置信度、误差半径、修正向量、匹配点数和失败原因。
- [x] 导航时间线已读取合成视图定位结果并写入 `visual_position`。
- [x] 前端已展示 UAV 图像、最佳合成视图、误差半径和修正向量。
- [x] `backend/tests` 通过 10 条测试。
- [x] backend full smoke 通过。
- [x] frontend build 通过。
- [ ] v0.4 合成图仍为正射瓦片代理图，不是最终真实相机渲染图。
- [x] v0.4 默认链路仍保留；v0.5a 可通过 `matcher_mode=opencv_orb` 驱动主导航时间线。

## 2026-06-09 自动视觉帧验收补充

- [x] 视觉帧数量已由后端按航线自动确定。
- [x] 自动抽帧综合距离间隔和航向关键变化。
- [x] 自动帧携带 `frame_trigger`、`route_distance_m`、`source_tile_id`。
- [x] UAV 当前影像帧绑定到正射瓦片派生图像，页面可显示。
- [x] 导航时间线按所选航线生成自动视觉帧。
- [x] 前端帧按钮支持可变数量。

## 2026-06-09 v0.5a ORB 视觉定位验收补充

- [x] `supermap_nav` 环境已安装并可导入 `opencv-python-headless 4.13.0`。
- [x] `cv2.ORB_create` 可用，`cv2.SIFT_create` 可检测但暂未作为正式 provider 接入。
- [x] `POST /api/vision/localize` 支持 `matcher_mode=opencv_orb`。
- [x] ORB provider 可输出 `provider=opencv_orb`、`status`、`matched_points`、`inlier_ratio`、`confidence`、`error_radius_m` 和 `best_estimated_pose`。
- [x] `scripts/generate_v05_match_evidence.py --task-id task_001 --top-k-tiles 2 --limit 6` 已验证 6/6 帧 localized。
- [x] `demo_data/generated/v05_match_evidence/` 已生成匹配连线、RANSAC 内点、UAV 图、合成视图和 JSON 结果证据。
- [x] 前端视觉定位面板已请求 `matcher_mode=opencv_orb` 并读取 `matches[0].evidence.urls`。
- [x] `POST /api/navigation/start` 支持 `matcher_mode=opencv_orb`，ORB 结果可进入导航时间线并写入 `visual_position`、`visual_frame` 和 `fused_position`。
- [x] `E:\anaconda\envs\supermap_nav\python.exe -m pytest backend\tests --basetemp E:\supermap_project\.tmp\pytest` 通过：12 passed。
- [x] `test_visual_navigation_timeline_can_be_orb_driven` 已覆盖 ORB 驱动导航时间线。
- [x] `npm run build` 通过。
- [x] `scripts/check_backend_smoke_full.ps1` 通过。
- [x] `scripts/check_project_runtime.ps1` 已修正并通过。
- [x] v0.5 轨迹误差报告字段已建立：`navigation_quality` 包含平均置信度、平均误差半径、融合轨迹偏差、终点误差、provider 统计、回退帧和平滑性。
- [ ] UAV 帧仍为基于正射影像/航线上下文生成的半真实演示帧，不是真实飞行相机数据。
- [x] v0.5 DOM/截图总门禁已形成：`scripts/check_v05_navigation_gate.ps1` 可一键覆盖 runtime、build、pytest、ORB 证据、导航时间线、报告字段、DOM 和截图。
- [x] 2026-06-10 完整 v0.5 门禁通过：`quality_grade=demo_verified`、`visual_observation_count=27`、`provider_counts={"opencv_orb":27}`、平均置信度 `0.775`、平均融合偏差 `2.1m`、终点误差 `8.6m`、SuperMap canvas `864x594`。
- [ ] 尚未形成完整彩排视频证据。
