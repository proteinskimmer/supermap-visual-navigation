# 项目任务看板

状态说明：

- `Todo`：未开始。
- `Doing`：进行中。
- `Mock Done`：mock 数据或代码初稿完成，未完成真实运行验收。
- `Runtime Verified`：依赖安装、测试、构建或页面运行已验证。
- `SuperMap Verified`：真实 SuperMap 服务和三维接入已验证。
- `Delivery Draft`：交付材料底稿完成，截图/PPT/视频未最终生成。
- `Delivery Ready`：提交材料和彩排已完成。
- `Blocked`：阻塞，需要协作解决。

## M1 环境与 SuperMap 底座

| ID | 任务 | 负责人 | 状态 | 依赖 | 验收标准 |
|---|---|---|---|---|---|
| M1-01 | 安装 iDesktopX 2025 | GIS | Runtime Verified | 无 | 已进入主界面，右下角显示本地试用许可剩余 90 天，`CBD` 样例工作空间和三维场景均已显示 |
| M1-02 | 安装 iServer 2025 | GIS | Runtime Verified | 无 | 已确认安装结构完整；从 `bin` 目录执行 `iserver.bat -start` 后，`8090` 端口监听，`/iserver`、服务列表、管理页和帮助页均返回 HTTP 200 |
| M1-03 | 选择任务区域 | GIS/统筹 | Todo | 无 | 输出任务边界和数据来源 |
| M1-04 | 整理影像、DEM、矢量图层 | GIS | Todo | M1-03 | iDesktopX 中可叠加显示 |
| M1-05 | 制作三维场景 | GIS | Todo | M1-04 | 场景视角和图层正确 |
| M1-06 | 发布 iServer 三维服务 | GIS | SuperMap Verified | M1-05 | 已确认官方 `3D-CBD` 与项目自建 `3D-low_altitude_demo` 三维服务均可访问；`3D-low_altitude_demo/rest/realspace/scenes.json` 返回项目场景标记 |
| M1-07 | 输出服务地址表 | GIS | Runtime Verified | M1-06 | 已记录项目自建 `3D-low_altitude_demo`、`map-low_altitude_demo`、`data-low_altitude_demo` 服务 URL、元数据 URL 和前端验收状态 |
| M1-08 | 完成 SuperMap 接入预案 | 统筹/前端/GIS | Mock Done | 无 | 有 iDesktopX、iServer、iClient3D 流程、服务模板和验收清单 |
| M1-09 | 预留 SuperMap 服务配置接口 | 后端 | Mock Done | M1-08 | `/api/supermap/config` 和 `/api/supermap/services` 可读取配置 |
| M1-10 | 核验 iClient3D 2025U1 本地 SDK | 统筹/前端 | SuperMap Verified | iClient3D 安装包 | 核心 JS/CSS、API 文档、示例和常用接口样例已记录；`supermap-minimal.html` 浏览器截图确认 WebGL2、Viewer 和 `scene.open` 成功 |
| M1-11 | 核验 iDesktopX 2025 本地安装 | 统筹/GIS | Runtime Verified | iDesktopX 安装包 | 主程序、启动脚本、自带 JRE、版本文件、帮助文档、样例数据、核心 GIS/三维组件均已核验 |
| M1-12 | 生成 iDesktopX demo GeoJSON 导入包 | 统筹/GIS | Runtime Verified | M1-11、demo 数据 | `demo_data/gis_export/` 已生成任务区、风险区、障碍物、视觉瓦片、起终点、预览航线、视觉中心点和无人机位置 GeoJSON，并通过解析检查 |
| M1-13 | 核验 iServer 2025U1A 本地安装与运行 | 统筹/GIS | Runtime Verified | iServer 安装包 | `scripts/check_supermap_iserver.ps1` 通过；内置 JRE、Objects Java、License Center、样例数据、iClient3D 资源存在；本机 HTTP 入口可访问；初始化向导已完成，文件管理根目录为 `E:\supermap_project\supermap_file_root` |
| M1-14 | 制作项目自建 `low_altitude_demo` 工作空间 | GIS | Runtime Verified | M1-12 | iDesktopX 已导入 `demo_data\gis_export` 并保存 `supermap_file_root\demo_workspace\low_altitude_demo.smwu` 与 `low_altitude_demo.udbx` |
| M1-15 | 发布项目自建 `low_altitude_demo` 服务 | GIS | SuperMap Verified | M1-14 | iServer 已发布 `map-low_altitude_demo`、`data-low_altitude_demo` 与 `3D-low_altitude_demo`；地图、8 个数据集和项目三维 scene REST 验收通过 |
| M1-16 | 前端从 `3D-CBD` 切换到项目自建服务 | 前端/GIS | SuperMap Verified | M1-15 | `config/supermap_services.local.json` 已切换到项目自建 scene/map/data 服务；后端 `/api/supermap/services` 返回三项 `verified` |
| M1-17 | 下发真实 / 半真实 demo 数据采集任务书 | 统筹/GIS | Runtime Verified | M1-03 | 已编写 `docs/project_management/14_real_data_collection_guide.md`，明确最低必交数据、字段、目录、来源说明和验收标准 |

## M2 平台基础功能

| ID | 任务 | 负责人 | 状态 | 依赖 | 验收标准 |
|---|---|---|---|---|---|
| M2-01 | 创建 Vue + Vite 项目 | 前端 | Runtime Verified | 无 | `npm run build` 已通过；浏览器演示截图仍待 M2-07 |
| M2-02 | 创建 FastAPI 项目 | 后端 | Runtime Verified | 无 | `pytest backend/tests` 和增强 smoke 已通过 |
| M2-03 | 实现三维场景加载 | 前端 | SuperMap Verified | M1-06 | iClient3D 承载层、SDK 加载、Viewer 初始化、项目自建 `3D-low_altitude_demo` 配置读取、业务图形叠加和错误回退均已完成；官方 `3D-CBD` 截图作为早期链路证据保留 |
| M2-04 | 实现图层控制面板 | 前端 | Mock Done | M1-07 | 可开关风险区/道路/水系 |
| M2-05 | 实现任务列表接口 | 后端 | Mock Done | M1-07 | 前端可读取任务 |
| M2-06 | 实现航线 mock 数据 | 后端 | Mock Done | M2-02 | 前端可显示路线 |
| M2-07 | 前后端联调任务和航线 | 前端/后端 | Runtime Verified | M2-03/M2-06 | 浏览器工作台已显示接口已连接、候选航线、风险校验、高程剖面和 SuperMap 三维场景；完整流程截图仍需归档 |

## M3 航线规划与风险校验

| ID | 任务 | 负责人 | 状态 | 依赖 | 验收标准 |
|---|---|---|---|---|---|
| M3-01 | 实现任务区域栅格化 | 规划 | Mock Done | M1-07 | 可生成规划栅格 |
| M3-02 | 实现 A* 最短航线 | 规划 | Mock Done | M3-01 | 返回一条可显示航线 |
| M3-03 | 实现风险代价地图 | 规划/GIS | Mock Done | M3-01 | 风险区影响路径代价 |
| M3-04 | 实现三种规划模式 | 规划 | Mock Done | M3-02/M3-03 | 返回最短/安全/综合三条航线 |
| M3-05 | 实现风险校验接口 | 后端/规划 | Mock Done | M3-04 | 返回评分和风险段 |
| M3-06 | 实现高程剖面数据 | 规划/GIS | Mock Done | M3-04 | 返回剖面数组 |
| M3-07 | 前端展示评分和剖面 | 前端 | Mock Done | M3-05/M3-06 | 右侧面板和图表可用 |

## M4 动态重规划与仿真

| ID | 任务 | 负责人 | 状态 | 依赖 | 验收标准 |
|---|---|---|---|---|---|
| M4-01 | 实现仿真时间轴 | 前端 | Mock Done | M2-07 | 支持播放/暂停/重置 |
| M4-02 | 实现航迹动态推进 | 前端 | Mock Done | M4-01 | 航迹随时间移动 |
| M4-03 | 实现事件日志接口 | 后端 | Mock Done | M4-01 | 返回事件列表 |
| M4-04 | 实现临时风险区创建 | 前端/后端 | Mock Done | M3-05 | 地图显示临时风险区 |
| M4-05 | 实现重规划算法 | 规划 | Mock Done | M4-04 | 新航线从当前位置接续 |
| M4-06 | 展示旧航线风险段和新航线 | 前端 | Mock Done | M4-05 | 重规划前后对比清晰 |

## M5 视觉匹配

| ID | 任务 | 负责人 | 状态 | 依赖 | 验收标准 |
|---|---|---|---|---|---|
| M5-01 | 准备示例无人机视角图 | 视觉/GIS | Mock Done | M1-03 | 已补 3 张可显示 jpg 演示占位图；真实航拍图后续替换 |
| M5-02 | 准备候选瓦片索引 | 视觉/GIS | Mock Done | M1-04 | 每个瓦片有边界和中心点 |
| M5-03 | 整理预计算匹配结果 | 视觉 | Mock Done | M5-01/M5-02 | 每张图有候选区和置信度 |
| M5-04 | 实现视觉匹配接口 | 后端/视觉 | Mock Done | M5-03 | 前端可请求结果 |
| M5-05 | 前端展示视觉候选区 | 前端 | Mock Done | M5-04 | 地图高亮候选区域 |

## M6 比赛材料

| ID | 任务 | 负责人 | 状态 | 依赖 | 验收标准 |
|---|---|---|---|---|---|
| M6-01 | 编写系统介绍文档 | 材料/统筹 | Delivery Draft | M4/M5 | 技术路线和功能完整 |
| M6-02 | 编写部署说明 | 后端/前端/GIS | Delivery Draft | M4/M5 | 新电脑可按文档启动 |
| M6-03 | 编写数据说明 | GIS | Delivery Draft | M1 | 图层和字段清楚 |
| M6-04 | 制作 PPT | 材料/统筹 | Delivery Draft | M6-01 | 已有 `docs/delivery/ppt_outline.md`，待按截图制作 PPT 文件 |
| M6-05 | 录制演示视频 | 材料/全体 | Delivery Draft | M4/M5 | 已有 `docs/delivery/demo_video_script.md`，待系统运行后录制视频 |
| M6-06 | 最终彩排 | 全体 | Todo | M6-04/M6-05 | 连续 3 次演示成功 |
| M6-07 | 准备答辩讲稿 | 材料/统筹 | Delivery Draft | M6-01 | 已有 `docs/delivery/defense_script.md` |
| M6-08 | 准备截图清单 | 材料/全体 | Delivery Draft | M4/M5 | 已有 `docs/delivery/screenshot_shotlist.md` |
| M6-09 | 准备最终提交包模板 | 材料/统筹 | Delivery Draft | M6-01 | 已有 `docs/delivery/submission_package_template.md` |

## 补充记录

| 日期 | 记录 |
|---|---|
| 2026-06-08 | 已新增 `MockMissionMap.vue` 和 `SuperMapScene.vue`，将 mock 态势图与未来 SuperMap iClient3D 接入边界拆开。 |
| 2026-06-08 | 已在前端增加演示闭环状态清单和控制按钮前置状态约束。 |
| 2026-06-08 | 后端 smoke 通过；前端 `npm run build` 因 `frontend/node_modules` 不存在、`vite` 未安装失败，等待依赖安装后验收。 |
| 2026-06-08 | 已继续拆分前端组件，新增独立报告视图和高程剖面组件；后端已补统一异常处理、Pydantic 响应模型、mock API 测试和增强 smoke 脚本。 |
| 2026-06-08 | 严格状态门禁已建立；`supermap_nav` 环境、后端 pytest、增强 smoke、前端 npm build 均已通过；Git 基线提交 `fed8b4f` 已创建。 |
| 2026-06-08 | 已核验 `E:\supermap_software\supermap-iclient3d-for-webgl_webgpu-2025u1`：iClient3D SDK 包、API 文档、WebGL/Vue/WebGPU 示例和核心接口样例存在；真实浏览器渲染、许可状态和 iServer 服务接入仍待验收。 |
| 2026-06-08 | 已核验 `E:\supermap_software\SuperMap iDesktopX 2025`：安装结构、自带 JRE、版本文件、许可说明、帮助文档、样例数据和核心三维组件存在；启动后拉起 `javaw.exe` 与 License Center，仍需主界面和样例数据截图。 |
| 2026-06-08 | 用户截图确认 iDesktopX 已进入主界面，`CBD` 样例工作空间已加载，右下角显示“本地试用许可 剩余时间：90天”；`M1-01` 升级为 `Runtime Verified`。 |
| 2026-06-08 | 用户截图确认 iDesktopX 中 `CBD` 三维场景已成功渲染，建筑、道路、地形图层可见；iDesktopX 样例三维场景验收通过。 |
| 2026-06-08 | 已实现 iClient3D 前端承载层：动态加载 SDK/CSS、创建 Viewer、可选 `scene.open(sceneUrl)`、空球绘制 mock 航线/风险区/视觉候选区/无人机点、失败回退 mock；新增 `supermap-minimal.html` 和团队排错文档。 |
| 2026-06-08 | 已确认 `demo_data/task_demo.json` 可按 UTF-8 JSON 解析，并新增 `scripts/export_demo_geojson.ps1` 显式使用 UTF-8 读取；已生成 `demo_data/gis_export/`，供 iDesktopX 导入制作 demo 工作空间。 |
| 2026-06-08 | 监督复核确认 iClient3D SDK 本机包、iDesktopX 本机包和前端静态 SDK 资源均已准备；`npm run build`、后端 pytest 和增强 smoke 均通过。下一门禁为 iServer 发布真实三维服务、记录 `sceneUrl` 并完成浏览器截图验收。 |
| 2026-06-09 | 已补 `backend/tests/test_supermap_contracts.py` 和 `scripts/check_project_runtime.ps1`；综合 runtime 检查通过，覆盖 GeoJSON、SuperMap 静态资源、最小验证页标记、前端 build、后端 pytest 和增强 smoke。 |
| 2026-06-09 | 已明确 `3D-CBD` 是官方样例链路验证，不是项目自建服务；新增 `low_altitude_demo` 配置模板、工作空间目录说明和发布前检查脚本。 |
| 2026-06-09 | 已核验 `E:\supermap_software\supermap-iserver-2025u1a-windows-x64-all`：安装结构完整；正确启动方式为进入 `bin` 后执行 `iserver.bat -start`；`8090` 端口、`/iserver`、服务列表、管理页和帮助页均通过 HTTP 验收。 |
| 2026-06-09 | 用户已完成 iServer 初始化向导，服务管理器入口为 `http://localhost:8090/iserver/admin-ui/home`，文件管理根目录已设为 `E:\supermap_project\supermap_file_root`。 |
| 2026-06-09 | 已确认 iServer 内置 `3D-CBD` 三维服务根节点 `http://localhost:8090/iserver/services/3D-CBD/rest/realspace`；`scenes.json` 返回 `CBD`，`scenes/CBD.json` 返回场景和图层元数据；已写入 `config/supermap_services.local.json`。 |
| 2026-06-09 | 已新增 `scripts/start_frontend_supermap_cbd.ps1`，用于以 `3D-CBD` 场景服务启动前端 SuperMap 模式；`pytest backend/tests` 和 `npm run build` 已通过；浏览器 WebGL 截图已确认。 |
| 2026-06-09 | 用户截图确认 `supermap-minimal.html` 中 WebGL2、SDK、Viewer、实体点和 `scene.open(sceneUrl)` 均成功，且已渲染 `3D-CBD` 城市三维场景。 |
| 2026-06-09 | 用户截图确认项目工作台 `SuperMap 场景已就绪`，并在真实 `3D-CBD` 场景上叠加候选航线、风险区、视觉候选区、起终点和当前业务面板；`M2-03` 升级为 `SuperMap Verified`。 |
| 2026-06-09 | 已编写真实 / 半真实 demo 数据采集任务书 `14_real_data_collection_guide.md`，并新增 `data_sources/README.md` 作为组员提交目录说明。 |
