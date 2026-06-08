# 项目推进状态日志

本日志是项目推进的总记录，用于跨对话、跨成员、跨阶段同步项目状态。每次完成阶段性工作、遇到阻塞、做出关键决策或进入新阶段时，都应更新本文件。

## 使用规则

- 每次新对话开始，优先阅读本文件，再阅读 `08_task_board.md`。
- 每次完成实质性工作后，在“推进记录”中新增一条。
- 每次出现环境、数据、软件、接口阻塞时，在“当前阻塞”中更新。
- 每次阶段通过验收后，将对应里程碑状态改为 `Done`。
- 日志只记录项目事实，不写闲聊内容。

## 当前状态快照

| 项目项 | 状态 | 说明 |
|---|---|---|
| 项目规划 | Done | 已形成原始规划和项目管理文档体系 |
| 分工与看板 | Review | 已拆分角色、任务、接口和验收标准，等待团队真实负责人填入 |
| 后端 mock 原型 | Runtime Verified | FastAPI 路由、统一异常处理、Pydantic 请求/响应模型、规划/风险/仿真/视觉/报告接口已完成；`pytest backend/tests` 通过 |
| 前端 mock 原型 | Mock Done | Vue 工作台已拆分为侧栏、地图、检查器、高程剖面、时间轴、报告页等组件；`npm run build` 通过，但浏览器演示流程尚未截图验收 |
| demo 数据 | Review | 已有固定任务区、风险区、障碍物、3 张视觉样例、5 个瓦片索引、3 组预计算匹配结果 |
| 环境配置 | Runtime Verified | 已创建 `supermap_nav` Conda 环境，后端依赖、pytest、前端依赖已安装；后端测试和前端构建通过 |
| SuperMap 软件 | Todo | iDesktopX、iServer、iClient3D 尚未完成安装和服务发布 |
| SuperMap 三维接入 | Review | 已拆出 `SuperMapScene.vue` 接入边界和 `MockMissionMap.vue` 备用演示图；真实 iClient3D 场景待 iServer 服务发布后接入 |
| SuperMap 接入预案 | Review | 已完成 iDesktopX、iServer、iClient3D 操作流程、服务地址记录模板、验收清单和服务配置读取接口 |
| 官方文档本地化 | Todo | 已预留 `docs/vendor/supermap_official/`，下载动作已暂停，目录当前无文档文件 |
| 比赛材料 | Review | 已有系统设计、部署说明、数据说明、源码结构说明、PPT 初稿、答辩讲稿、演示视频脚本、截图清单、真实数据清单和提交包模板；PPT 文件、截图和视频未实际生成 |

## 里程碑状态

| 里程碑 | 状态 | 当前说明 |
|---|---|---|
| M1 环境与 SuperMap 底座 | Todo | 需要安装 SuperMap 软件、制作数据、发布 iServer 服务 |
| M2 平台基础功能 | Review | 前后端代码初稿已完成，待安装依赖后真实启动联调 |
| M3 航线规划与风险校验 | Review | mock 算法和风险评分已完成，待真实运行和 GIS 数据接入 |
| M4 动态重规划与仿真 | Review | mock 仿真、事件、临时风险区、重规划已完成，待前端运行验收 |
| M5 视觉匹配 | Review | 预计算演示框架已扩展完成：图片清单、瓦片索引、Top-K 候选排序、结果详情和前端解释展示；真实图片和算法模型待后置 |
| M6 比赛材料 | Todo | 基础文档已有，PPT、视频、最终提交包未完成 |

## 当前阻塞

| 编号 | 阻塞项 | 影响范围 | 当前处理建议 |
|---|---|---|---|
| B-001 | SuperMap 软件尚未安装完成 | M1、三维接入、真实 GIS 服务 | 继续先完成 mock 工程和环境联调；软件安装后进入 M1 |
| B-003 | 未确定真实任务区域和 GIS 数据源 | M1、M3、M5 | 先使用 demo 数据演示；后续由 GIS 负责人选择区域并输出服务地址 |
| B-004 | 官方 SuperMap 文档尚未本地下载 | SuperMap 接入 | 已暂停下载动作，仅保留空目录；后续需经确认后再从官方来源下载/整理 |
| B-005 | 视觉样例真实航拍图片尚未入库 | M5、演示视频、PPT 截图 | 已补 3 张可显示 jpg 演示占位图；若需真实航拍效果，后续替换同名文件或公开图片 URL |
| B-006 | 前端浏览器演示流程尚未截图验收 | M2、M4、M6 | `npm run build` 已通过；仍需启动前后端，在浏览器完成一次 mock 演示闭环并截图 |

## 关键决策

| 编号 | 日期 | 决策 | 原因 |
|---|---|---|---|
| D-001 | 2026-06-08 | 使用 SuperMap 2025 正式版，不优先使用 2026 Beta | 比赛交付稳定性优先，2025 满足最低版本要求 |
| D-002 | 2026-06-08 | 当前阶段不安装 SuperMap iObjects | 初期可通过 iDesktopX + iServer + iClient3D 跑通主流程，iObjects 后置 |
| D-003 | 2026-06-08 | 先做 mock 工程，再接 SuperMap 三维服务 | 软件未装好时避免空等，先完成前后端和算法主流程 |
| D-004 | 2026-06-08 | 后端使用独立 Conda 环境 `supermap_nav` | 避免污染系统 Python、Anaconda base 和已有环境 |
| D-005 | 2026-06-08 | 当前项目边界为软件仿真，不接真实飞控 | 降低安全和工程复杂度，符合比赛演示主线 |
| D-006 | 2026-06-08 | 前端三维区域采用 `SuperMapScene.vue` 作为统一接入边界，保留 `MockMissionMap.vue` 作为备用演示图 | SuperMap 环境未完成时保证 mock 演示闭环可推进，环境完成后减少替换范围 |
| D-007 | 2026-06-08 | 视觉匹配优先采用预计算 provider，真实模型后置 | 保证比赛演示稳定，后续可在服务层替换 DINOv2、LoFTR、LightGlue 或 OpenCV RANSAC |

## 推进记录

### 2026-06-08 当前项目体检

- 项目结构检查通过：
  - 根目录包含 `backend/`、`frontend/`、`demo_data/`、`docs/`、`scripts/`。
  - 当前目录不是 Git 仓库，仍不能使用 `git status` 或 `git diff` 做版本差异检查。
- 后端检查通过：
  - `backend/app` 下 21 个 Python 文件 AST 语法解析通过。
  - 规划、风险、视觉 smoke test 通过。
  - A* 返回 3 条航线，首尾点与任务起终点一致。
  - 视觉服务返回 3 张图、5 个瓦片，`top_k=2` 时返回 `candidate_count=2`、`total_candidate_count=3`。
- 数据检查通过：
  - `demo_data/task_demo.json` 可解析。
  - 当前 demo 数据包含 1 个任务、3 张视觉样例、5 个瓦片、3 组视觉匹配结果。
- 前端静态检查部分通过：
  - `frontend/src/services/api.js` Node 语法检查通过。
  - 前端组件已拆分为 `App.vue`、`SuperMapScene.vue`、`MockMissionMap.vue`。
  - 未运行 Vue 构建，原因仍是 `frontend/node_modules` 不存在。
- 清理项：
  - 已清理后端验证产生的 `__pycache__` 目录。
- 当前主要遗留：
  - 依赖环境未安装，前后端尚未真实启动联调。
  - SuperMap 软件和 iServer 服务尚未接入。
  - 官方文档本地化目录为空。
  - 视觉真实图片文件仍未放入仓库。

### 2026-06-08 SuperMap 接入预案

- 新增 SuperMap 接入预案目录：`docs/supermap_integration/`。
- 完成 iDesktopX 操作流程：
  - 数据输入清单。
  - 图层命名规范。
  - `risk_zone` 和 `obstacle` 字段规范。
  - 三维场景制作步骤。
- 完成 iServer 发布流程：
  - 三维服务、地图服务、数据服务、空间分析服务发布顺序。
  - 服务 URL 记录要求。
  - 发布验收标准和常见问题。
- 完成 iClient3D 接入步骤：
  - 前端接入入口固定为 `frontend/src/components/SuperMapScene.vue`。
  - 保留 `MockMissionMap.vue` 作为备用视图。
  - 明确服务配置、三维加载、图层叠加和仿真联动顺序。
- 新增服务地址记录模板：
  - `docs/supermap_integration/04_service_url_registry_template.md`。
- 新增 SuperMap 接入验收清单：
  - `docs/supermap_integration/05_supermap_acceptance_checklist.md`。
- 新增服务配置模板：
  - `config/supermap_services.example.json`。
  - 正式联调时复制为 `config/supermap_services.local.json`。
- 新增后端配置读取接口：
  - `GET /api/supermap/config`
  - `GET /api/supermap/services`

### 2026-06-08 比赛交付材料补齐

- 新增比赛交付材料目录：`docs/delivery/`。
- 完成 PPT 初稿结构：`docs/delivery/ppt_outline.md`。
  - 包含 12 页建议结构、每页标题、讲述重点和配图建议。
- 完成答辩讲稿：`docs/delivery/defense_script.md`。
  - 包含开场、背景、架构、功能、SuperMap 使用口径、边界说明、总结和常见问答。
- 完成演示视频分镜脚本：`docs/delivery/demo_video_script.md`。
  - 包含 6 到 8 分钟完整版和 5 分钟压缩版。
- 完成截图素材清单：`docs/delivery/screenshot_shotlist.md`。
  - 覆盖 iDesktopX、iServer、系统工作台、航线规划、风险校验、动态重规划、视觉匹配和任务报告。
- 完成真实数据工作清单：`docs/delivery/real_data_worklist.md`。
  - 包含任务区域选择标准、数据来源建议、字段检查、坐标检查、视觉数据检查和最小真实数据版本。
- 完成最终提交包模板：`docs/delivery/submission_package_template.md`。
  - 包含推荐提交目录、README 内容、提交前检查、不应提交内容和最终演示必过流程。

### 2026-06-08

- 建立项目管理文档体系：总控计划、各分工执行细则、任务看板、接口约定、验收清单、进度跟踪模板。
- 创建 mock 工程目录：`backend/`、`frontend/`、`demo_data/`、`scripts/`、`docs/`。
- 完成后端 FastAPI 初稿：
  - 任务和图层接口。
  - 航线规划接口。
  - 风险校验接口。
  - 仿真启动接口。
  - 临时风险区接口。
  - 动态重规划接口。
  - 视觉匹配接口。
  - 报告接口。
- 完成后端结构拆分：
  - `backend/app/api/`
  - `backend/app/models/schemas.py`
  - `backend/app/services/`
- 完成 demo 算法初稿：
  - A* 栅格规划。
  - 最短、最安全、综合最优三种航线。
  - 风险评分。
  - 高程剖面。
  - 临时风险区和接续重规划。
- 完成前端 Vue mock 工作台初稿：
  - 任务和图层面板。
  - 二维任务态势图。
  - 航线展示。
  - 风险区、障碍物、视觉候选区域展示。
  - 风险评分和高程剖面。
  - 仿真播放、暂停、推进、重置。
  - 临时风险区和重规划展示。
  - 任务报告面板。
- 完成环境和交付材料：
  - `environment.yml`
  - `scripts/start_backend.ps1`
  - `scripts/start_frontend.ps1`
  - `scripts/check_backend_smoke.ps1`
  - `docs/deploy_guide.md`
  - `docs/system_design.md`
  - `docs/data_description.md`
  - `docs/source_code_structure.md`
- 完成轻量验证：
  - Python 语法检查通过。
  - demo 数据 JSON 可解析。
  - 前端 `package.json` 可解析。
  - 后端算法 smoke test 通过。
  - 未保留 `__pycache__` 缓存文件。

### 2026-06-08 视觉模块扩展

- 视觉模块按“预计算演示 + 后续算法可替换”路线扩展完成。
- 新增后端视觉服务层：`backend/app/services/vision_service.py`。
- 扩展视觉 API：
  - `GET /api/vision/images`
  - `GET /api/vision/tiles`
  - `POST /api/vision/match`
  - `GET /api/vision/matches/{match_id}`
- 扩展请求模型：`VisionMatchRequest` 支持 `top_k` 和 `algorithm_mode`。
- 扩展 demo 数据：
  - 3 张视觉样例图元数据。
  - 5 个候选瓦片索引。
  - 3 组预计算匹配结果，每组 3 个候选区。
- 前端接入：
  - 视觉样例选择。
  - 瓦片索引显示。
  - 候选区高亮。
  - 候选排名、置信度、匹配点、内点比例和解释原因展示。
  - `SuperMapScene.vue` 作为未来 iClient3D 接入点，当前回退到 `MockMissionMap.vue`。
- 补充文档：`docs/vision_matching_framework.md`。
- 本次复核修正：
  - `candidate_count` 改为表示本次返回数量。
  - 新增 `total_candidate_count` 表示原始候选总数。
- 验证情况：
  - 视觉服务链路校验通过：3 张图、5 个瓦片、Top-K 候选排序正常。
  - 前端 API 文件语法检查通过。
  - 未运行 `npm run build`，因为 `frontend/node_modules` 尚未安装。
  - 当前目录不是 Git 仓库，不能使用 `git diff`。
  - 真实图片文件尚未放入仓库，`/demo/uav_view_001.jpg` 等仍为路径占位。
  - 官方文档下载动作已暂停，仅留下空目录 `docs/vendor/supermap_official/`。

### 2026-06-08 mock 演示闭环与 SuperMap 接入边界补强

- 前端场景结构调整：
  - 新增 `frontend/src/components/MockMissionMap.vue`，承载当前二维态势图、航线、风险区、障碍物、视觉瓦片、临时风险区和重规划结果展示。
  - 新增 `frontend/src/components/SuperMapScene.vue`，作为未来 iClient3D / Cesium 场景挂载点。
  - `SuperMapScene.vue` 支持通过 `VITE_SCENE_PROVIDER=supermap` 切换到 SuperMap 接入占位模式。
  - 当 `layers[].service_url` 为空或 SuperMap 环境未就绪时，页面继续保留 mock 态势图作为备用演示图。
- 前端演示流程补强：
  - 简化 `frontend/src/App.vue`，将地图绘制逻辑迁出，保留任务、航线、风险、仿真、重规划、视觉和报告流程编排。
  - 增加“演示闭环”状态清单，记录任务图层、候选航线、风险评分、仿真时间轴、临时风险区、动态重规划、视觉候选区域和任务报告的完成状态。
  - 增加控制按钮前置状态约束，避免未选择航线、未启动仿真时触发无效操作。
- 文档补充：
  - 更新 `docs/deploy_guide.md`，记录 SuperMap 场景接入位置、mock 备用图和环境变量切换方式。
  - 更新 `docs/source_code_structure.md`，记录新增前端组件目录和组件职责。
- 验证情况：
  - `scripts/check_backend_smoke.ps1` 通过，输出三种航线、风险评分和路线点数量。
  - `npm run build` 未通过，原因是 `frontend/node_modules` 不存在，`vite` 命令未安装；该问题归入 B-002 环境依赖阻塞。
  - 当前目录不是 Git 仓库，不能使用 `git diff`。

### 2026-06-08 日志与接口文档补全

- 按项目日志要求补全状态记录：
  - 当前阻塞新增 `B-005`，记录视觉样例真实图片文件尚未入库。
  - 关键决策新增 `D-007`，记录视觉匹配优先采用预计算 provider、真实模型后置。
- 补全 `docs/project_management/09_interfaces_and_data_contracts.md`：
  - 新增 `VisionImage`、`VisionTile`、`VisionMatchResult` 数据结构。
  - 补充 `GET /api/vision/images`、`GET /api/vision/tiles`、`GET /api/vision/matches/{match_id}`。
  - 明确 `POST /api/vision/match` 的 `top_k`、`algorithm_mode`、`candidate_count`、`total_candidate_count` 语义。
- 补全 `docs/project_management/10_acceptance_checklist.md`：
  - 区分视觉样例元数据已完成、真实图片文件待补充。
  - 区分 mock 场景候选区高亮已完成、安装依赖后的前端真实运行验收待完成。
- 补充 `docs/vision_matching_framework.md` 的日志和状态更新要求。
- 验证情况：
  - 状态日志可检索到 `B-005` 和 `D-007`。
  - 接口文档可检索到新增视觉接口和数据结构。
  - demo JSON 可解析。
  - 视觉 Top-K 服务链路校验通过。

### 2026-06-08 前端拆分、后端契约和测试补强

- 前端源码继续拆分：
  - 新增 `EmptyState.vue`，统一空状态展示。
  - 新增 `TaskSidebar.vue`，承载任务、图层、视觉样例、流程控制和演示闭环清单。
  - 新增 `InspectorPanel.vue`，承载候选航线、风险校验、视觉匹配结果。
  - 新增 `ElevationProfile.vue`，展示飞行高度、地形高程、图例和采样统计。
  - 新增 `TimelinePanel.vue`，承载仿真进度和事件日志。
  - 新增 `ReportPage.vue`，作为工作台内独立任务报告视图。
  - `App.vue` 已重建为状态编排容器，保留流程动作和异常处理，不再直接承载大段面板 UI。
  - 前端 API 客户端已改为优先展示后端统一错误响应中的 `message`。
- 后端工程补强：
  - `backend/app/models/schemas.py` 已扩展为请求/响应模型集合，核心接口挂接 `response_model`。
  - 新增 `backend/app/api/errors.py`，统一处理 HTTPException、请求校验错误和未捕获异常。
  - `backend/app/api/responses.py` 补充类型标注。
  - 报告接口改为通过视觉服务获取带排名和候选数量的规范视觉结果。
  - `supermap` 配置接口也补充响应模型。
- 测试和 smoke：
  - 新增 `backend/tests/test_mock_api.py`，覆盖健康检查、任务、规划、风险、仿真、临时风险区、重规划、视觉 Top-K、报告和错误格式。
  - 新增 `scripts/check_backend_smoke_full.ps1`，检查 JSON、Python AST、服务层和 FastAPI TestClient API 契约。
  - `environment.yml` 和 `backend/requirements.txt` 已加入 `pytest>=8.0.0`。
- 文档同步：
  - `docs/project_management/09_interfaces_and_data_contracts.md` 补充统一异常处理、响应模型清单、测试和 smoke 命令。
  - `docs/deploy_guide.md` 补充增强 smoke 和 pytest 运行方式。
  - `docs/source_code_structure.md` 补充新增前端组件、后端测试和增强 smoke 脚本。
- 验证情况：
  - Python AST 检查通过：`backend/app` 和 `backend/tests`。
  - 轻量 smoke `scripts/check_backend_smoke.ps1` 通过。
  - 前端 API 文件 `node --check frontend/src/services/api.js` 通过。
  - 前端构建未运行：`frontend/node_modules` 和 `frontend/node_modules/.bin/vite.cmd` 不存在。
  - `pytest` 未运行：当前环境未安装 `pytest` 命令。
  - 增强 smoke 已执行到服务层并通过，但 FastAPI API 契约部分阻塞：当前 Python 环境缺少 `fastapi`。

## 下一步建议

优先进入 M2 真实运行验收：

1. 使用 Anaconda 创建 `supermap_nav` 环境。
2. 安装后端依赖。
3. 安装前端依赖。
4. 启动后端并访问 `/api/health`。
5. 启动前端并打开工作台页面。
6. 修复运行中暴露的问题。
7. 使用当前 mock 场景完成一次从任务加载到报告生成的演示彩排。
8. SuperMap 服务发布后，在 `demo_data/task_demo.json` 的 `layers[].service_url` 填入服务地址，并在 `SuperMapScene.vue` 中接入真实 iClient3D 场景。
9. 将通过项从 `Review` 更新为 `Done`。
10. 补充视觉样例真实图片文件或可公开图片 URL，使三张视觉样例可以在前端直接展示。
