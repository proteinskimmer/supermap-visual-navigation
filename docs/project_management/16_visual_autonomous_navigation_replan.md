# 视觉自主导航项目重规划总纲

更新日期：2026-06-09

## 1. 最终目标

本项目的最终目标是形成一个基于 SuperMap GIS 三维底座的无人机视觉自主导航仿真系统。系统主线不是“做一段航线动画”，也不是“视觉匹配结果辅助人工判断”，而是：

> 输入 UAV 视角影像帧，通过视觉地理重定位得到当前位置估计，再由后端生成权威导航状态，驱动三维无人机、遥测面板、事件流、风险判断和必要时的重规划。

当前比赛阶段的交付边界是软件仿真与演示验证，不接真实飞控，不下发真实无人机控制指令，不宣称真实自主飞行已经实现。

## 2. 演示主线

演示必须围绕下面这条链路组织：

```text
任务加载
 -> 参考航线生成
 -> UAV 视觉帧进入
 -> 视觉地理重定位
 -> 后端融合生成导航状态
 -> 三维无人机按 fused_position 连续飞行
 -> 遥测、置信度、偏差、事件流实时更新
 -> 低置信度或风险触发辅助/复核/重规划
 -> 输出任务报告
```

航线规划、风险校验、临时风险区、动态重规划仍然保留，但它们的定位是视觉自主导航任务的支撑服务，不再作为系统第一主线。

## 3. 严格口径

可以对外表述：

- 已完成 SuperMap scene/map/data 接口级闭环。
- 已完成项目自建 `low_altitude_demo` 服务发布和前端接入。
- 已形成视觉自主导航指挥舱界面初稿。
- 当前正在建设后端权威导航状态机。
- 当前视觉定位采用预计算演示 provider，后续可替换为 DINOv2、LoFTR、LightGlue 或 OpenCV/RANSAC。

禁止对外表述：

- 已接入真实飞控。
- 已实现真实无人机自主控制。
- 已接入真实倾斜摄影或精细三维城市模型。
- 当前动画就是完整视觉自主导航闭环。
- 当前视觉匹配已经是真实模型在线推理结果。

## 4. 总体架构

```text
demo_data/task_demo.json
  |-- reference_routes
  |-- visual_localization_frames
  |-- navigation_timeline
  |-- telemetry_profile

FastAPI backend
  |-- MissionService
  |-- PlanningService
  |-- RiskService
  |-- VisionService
  |-- VisualNavigationService
  |-- ReportService

Vue frontend cockpit
  |-- SuperMapScene
  |-- UAV frame viewer
  |-- telemetry panel
  |-- visual localization panel
  |-- route/risk panel
  |-- event stream
```

后端必须成为导航状态权威源。前端不得自行决定 UAV 当前状态，只能根据后端返回的状态进行展示、播放和交互。

## 5. 核心数据结构

后端导航状态至少包含：

```text
session_id
time_s
reference_position: lon, lat, altitude_m
visual_position: lon, lat, altitude_m, confidence
fused_position: lon, lat, altitude_m
deviation_m
navigation_mode: autonomous | assisted | review
telemetry: speed_mps, heading_deg, pitch_deg, roll_deg, yaw_deg, battery_pct, signal
active_frame_id
active_route_id
active_event
```

其中：

- `reference_position` 来自参考航线。
- `visual_position` 来自视觉定位结果。
- `fused_position` 是无人机三维显示和状态面板的唯一权威位置。
- `navigation_mode` 根据视觉置信度和偏差自动切换。

## 6. 推荐接口

必须新增或重构的接口：

```text
POST /api/navigation/start
GET  /api/navigation/state?session_id=...&time_s=...
GET  /api/navigation/timeline?session_id=...
POST /api/navigation/localize
POST /api/navigation/replan
```

现有视觉接口可保留：

```text
GET  /api/vision/images
GET  /api/vision/tiles
POST /api/vision/match
GET  /api/vision/matches/{match_id}
```

但视觉接口输出必须能被 `VisualNavigationService` 消费，不能只服务于前端展示。

## 7. 分工模块

### A. 后端视觉自主导航

目标：建立后端权威导航状态机。

任务：

- 新增 `VisualNavigationService`。
- 定义导航会话、时间轴、状态帧、遥测帧和事件帧。
- 将视觉匹配结果转换为 `visual_position`。
- 根据置信度和偏差生成 `fused_position`。
- 支持 `autonomous`、`assisted`、`review` 三种模式。
- 生成可回放的 `navigation_timeline`。
- 为前端提供单帧状态和完整时间线接口。

验收：

- UAV 三维位置由 `/api/navigation/state` 或 `/api/navigation/timeline` 驱动。
- 播放时无人机严格沿 `fused_position` 连续移动。
- 遥测、置信度、偏差和事件来自后端。
- 低置信度样例自动进入 `review` 或 `assisted`。

### B. 视觉定位与数据

目标：让视觉模块从“候选区展示”升级为“导航状态输入”。

任务：

- 补齐真实或半真实 UAV 视角图。
- 建立 UAV 帧与时间轴、相机高度、参考位置的对应关系。
- 建立正射影像/瓦片索引与候选区。
- 输出预计算定位结果：位置、置信度、匹配点、内点率、偏差。
- 保留真实算法 provider 替换口。

验收：

- 至少 4 帧可演示：高置信、正常置信、偏差修正、低置信复核。
- 每帧都能映射到一个导航状态。
- 能解释“为什么 UAV 位置发生修正或降级”。

### C. SuperMap/GIS 底座

目标：提供三维空间底座和真实服务接入证据。

任务：

- 保持 `3D-low_altitude_demo`、`map-low_altitude_demo`、`data-low_altitude_demo` 可访问。
- 维护服务 URL 记录。
- 后续替换真实 DOM、DEM、建筑/地物数据。
- 保留发布、截图、REST 门禁证据。

验收：

- `scripts/check_supermap_goal_evidence.ps1 -Strict` 通过。
- 前端能加载项目自建 scene/map/data 服务。
- 材料中明确当前 3D 建筑为演示级表达，不包装为真实精细建模。

### D. 前端指挥舱

目标：成为后端导航状态的可视化消费端。

任务：

- 播放控制调用导航时间线，不再自行拼接 UAV 轨迹。
- 三维无人机位置绑定 `fused_position`。
- 右侧显示 UAV 实时影像帧、遥测、视觉定位、偏差和导航模式。
- 显示参考位置、视觉位置、融合位置三者关系。
- 事件流显示视觉定位、低置信度、风险触发、重规划等后端事件。
- 保留“视觉辅助导航”作为降级模式入口。

验收：

- 开始播放后，UAV、遥测、视觉帧、事件流同步推进。
- 切换到低置信帧时，界面明显进入复核/辅助状态。
- 用户能看懂仿真播放的意义：它是在回放视觉自主导航状态链路，而不是单纯动画。

### E. 航线规划、风险与重规划

目标：为视觉自主导航提供参考路径和安全约束。

任务：

- 生成参考航线。
- 计算风险评分和高程剖面。
- 判断当前 `fused_position` 是否接近风险区或偏离航线。
- 在临时风险区出现时，从当前融合位置触发重规划。
- 将重规划结果写入导航事件。

验收：

- 重规划从当前 `fused_position` 接续，而不是从旧航线固定点开始。
- 风险告警和重规划原因可解释。
- 新旧航线在三维场景中对比清晰。

### F. 交付材料与项目管理

目标：形成可答辩、可复验、可跟进的交付体系。

任务：

- 更新系统设计、接口文档、数据说明、答辩稿。
- 输出完整演示脚本。
- 录制演示视频。
- 完成 PPT。
- 做至少 3 次完整彩排。
- 所有截图、视频、文档使用同一套 demo 数据。

验收：

- 材料不夸大真实能力。
- 每个演示步骤都有截图或视频证据。
- 最终提交包可在本机一键启动并复验核心流程。

## 8. 里程碑

| 里程碑 | 目标 | 当前状态 | 过关条件 |
|---|---|---|---|
| R0 主线纠偏 | 冻结“视觉自主导航”目标 | Done | 文档、日志、看板同步完成 |
| R1 SuperMap 底座 | 项目自建 GIS 服务可用 | SuperMap Verified | REST、截图、前端服务状态通过 |
| R2 后端导航状态机 | 后端输出权威 UAV 状态 | Runtime Verified | 导航接口、测试、时间线通过 |
| R3 视觉定位入链 | 视觉结果驱动导航状态 | Todo | 4 帧样例能更新状态 |
| R4 前端状态消费 | 指挥舱播放后端时间线 | Runtime Verified | UAV、遥测、影像、事件同步 |
| R5 风险重规划入链 | 从融合位置触发安全服务 | Mock Done | 风险事件和导航重规划接口已接入，真实安全策略仍需扩展 |
| R6 真实/半真实数据 | 替换占位影像与关键数据 | Todo | 数据来源、文件、字段验收 |
| R7 交付彩排 | PPT、视频、提交包完成 | Todo | 3 次完整彩排通过 |

## 9. 下一步执行顺序

1. 补真实或半真实 UAV 图像。
2. 按 R2 当前服务输出整理 `navigation_timeline`、`visual_localization_frames`、`telemetry_profile` 数据说明。
3. 扩展风险/重规划真实安全策略。
4. 做完整演示截图和视频。
5. 更新 PPT 和答辩材料，完成彩排。

## 10. 当前监督结论

当前项目已有较好的 SuperMap 底座、mock 原型和指挥舱 UI 初稿，但还没有完成视觉自主导航的核心后端闭环。下一阶段优先级不再是继续美化界面，而是建立后端权威导航状态，让无人机、遥测、视觉帧、事件和重规划全部围绕同一条时间线运转。
