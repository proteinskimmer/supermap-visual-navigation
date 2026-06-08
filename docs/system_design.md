# 系统设计说明

## 1. 系统定位

本系统是基于 SuperMap GIS 底座的低空任务智能规划与三维仿真平台，聚焦软件仿真验证、航线规划、风险校验、动态重规划和视觉定位辅助展示。

系统不接入真实无人机飞控，不生成真实飞行控制指令。

## 2. 当前实现状态

当前阶段为 mock 工程原型：

- 使用固定 demo 数据模拟任务区域、风险区、障碍物和视觉匹配结果。
- 后端提供 FastAPI 接口。
- 前端提供 Vue 工作台。
- 中间地图区域暂用 SVG 态势图，后续替换为 SuperMap iClient3D for WebGL。

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
| 主页面 | `frontend/src/App.vue` | 工作台、态势图、控制、报告 |
| API 客户端 | `frontend/src/services/api.js` | 统一封装后端请求 |
| 样式 | `frontend/src/styles.css` | 页面布局和可视化样式 |

## 5. 演示主流程

1. 打开前端工作台。
2. 自动加载示范任务、图层和视觉匹配结果。
3. 点击“规划”，生成三条候选航线。
4. 查看右侧航线评分、风险校验和高程剖面。
5. 点击“仿真”并“播放”。
6. 点击“重规划”，添加临时风险区并生成新航线。
7. 查看视觉匹配候选区域。
8. 点击“报告”，生成任务摘要。

## 6. SuperMap 后续接入

SuperMap 接入不改变后端业务接口，主要替换数据来源和地图渲染：

- GIS 负责人使用 iDesktopX 制作数据和三维场景。
- 使用 iServer 发布三维服务、地图服务和数据服务。
- 前端将 SVG 态势图替换为 iClient3D for WebGL 场景。
- 后端从 iServer 或导出的 GeoJSON 读取真实任务区、风险区和障碍物。

## 7. 视觉匹配框架

视觉匹配当前采用预计算演示路线，数据来源为 `demo_data/task_demo.json` 中的 `vision_images`、`vision_tile_index` 和 `vision_matches`。

已提供接口：

- `GET /api/vision/images`
- `GET /api/vision/tiles`
- `POST /api/vision/match`
- `GET /api/vision/matches/{match_id}`

详细需求、数据结构和后续算法接入方式见 `docs/vision_matching_framework.md`。
