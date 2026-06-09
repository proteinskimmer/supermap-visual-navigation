# 系统设计说明

## 1. 系统定位

本系统是基于 SuperMap GIS 底座的无人机视觉自主导航仿真平台，主线是利用 UAV 影像与地理场景/候选瓦片匹配结果更新导航状态，并在三维态势中展示视觉定位、参考航线、安全约束和动态重规划过程。

低空航线规划、风险校验和动态重规划在本系统中作为视觉自主导航的支撑服务：航线提供任务目标和参考轨迹，风险校验提供安全约束，重规划用于视觉定位偏差、临时风险或任务环境变化后的接续导航。

系统不接入真实无人机飞控，不生成真实飞行控制指令。

系统保留视觉辅助导航模式。在低置信度匹配、GNSS 可用、人工作业复核或演示降级场景下，视觉结果可只作为定位参考和风险提示，不直接修正导航状态。

## 2. 当前实现状态

当前阶段为 mock 工程原型：

- 使用固定 demo 数据模拟任务区域、风险区、障碍物、参考航线、UAV 影像帧、视觉定位候选和导航状态修正。
- 后端提供 FastAPI 接口。
- 前端提供 Vue 工作台。
- 前端主界面已调整为视觉导航态势指挥舱，中央使用 SuperMap iClient3D 场景作为第一视觉中心，右侧展示 UAV 影像帧、遥测、视觉定位状态和航线安全摘要。

## 3. 后端模块

| 模块 | 文件 | 说明 |
|---|---|---|
| API 装配 | `backend/app/main.py` | 创建 FastAPI 应用并注册路由 |
| 任务/图层 | `backend/app/api/tasks.py` | 返回任务、风险区、障碍物、图层 |
| 航线 | `backend/app/api/routes.py` | 规划和重规划接口 |
| 风险 | `backend/app/api/risks.py` | 航线风险校验 |
| 仿真 | `backend/app/api/simulations.py` | 仿真启动和临时风险区 |
| 视觉 | `backend/app/api/vision.py` | 预计算视觉匹配结果 |
| 报告 | `backend/app/api/reports.py` | 任务报告摘要 |
| 算法 | `backend/app/services/planning_service.py` | A* 航线规划 |
| 风险服务 | `backend/app/services/risk_service.py` | 风险评分、高程剖面、事件 |
| 视觉服务 | `backend/app/services/vision_service.py` | 视觉样例、瓦片索引、候选结果查询 |

## 4. 前端模块

| 模块 | 文件 | 说明 |
|---|---|---|
| 主页面 | `frontend/src/App.vue` | 视觉导航指挥舱、态势图、遥测、视觉定位、控制、报告 |
| API 客户端 | `frontend/src/services/api.js` | 统一封装后端请求 |
| 样式 | `frontend/src/styles.css` | 页面布局和可视化样式 |

## 5. 演示主流程

1. 打开视觉导航态势指挥舱。
2. 自动加载示范任务、SuperMap 场景、参考航线和 UAV 影像帧。
3. 系统执行视觉匹配，得到候选瓦片、置信度和估计偏移。
4. 在视觉自主模式下，匹配结果用于修正 UAV 导航状态；在辅助导航模式下，匹配结果只作为参考提示。
5. 播放任务推演，查看 UAV 影像、遥测、视觉定位状态、参考航线偏差和实时事件流。
6. 触发临时风险区后，系统进行接续重规划，并在三维场景中显示新旧轨迹。
7. 点击“报告”，生成任务摘要。

## 6. SuperMap 后续接入

SuperMap 接入不改变后端业务接口，主要替换数据来源和地图渲染：

- GIS 负责人使用 iDesktopX 制作数据和三维场景。
- 使用 iServer 发布三维服务、地图服务和数据服务。
- 前端将 SVG 态势图替换为 iClient3D for WebGL 场景。
- 后端从 iServer 或导出的 GeoJSON 读取真实任务区、风险区和障碍物。

## 7. 视觉匹配框架

视觉匹配当前采用预计算演示路线，数据来源为 `demo_data/task_demo.json` 中的 `vision_images`、`vision_tile_index` 和 `vision_matches`。前端将匹配结果解释为视觉定位状态：高置信结果可在视觉自主模式中修正 UAV 导航位置，低置信结果降级为辅助导航/人工复核提示。

已提供接口：

- `GET /api/vision/images`
- `GET /api/vision/tiles`
- `POST /api/vision/match`
- `GET /api/vision/matches/{match_id}`

详细需求、数据结构和后续算法接入方式见 `docs/vision_matching_framework.md`。
