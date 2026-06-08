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
| M1-01 | 安装 iDesktopX 2025 | GIS | Todo | 无 | 能正常启动并打开样例数据 |
| M1-02 | 安装 iServer 2025 | GIS | Todo | 无 | 能访问 iServer 管理页面 |
| M1-03 | 选择任务区域 | GIS/统筹 | Todo | 无 | 输出任务边界和数据来源 |
| M1-04 | 整理影像、DEM、矢量图层 | GIS | Todo | M1-03 | iDesktopX 中可叠加显示 |
| M1-05 | 制作三维场景 | GIS | Todo | M1-04 | 场景视角和图层正确 |
| M1-06 | 发布 iServer 三维服务 | GIS | Todo | M1-05 | 前端可访问服务 URL |
| M1-07 | 输出服务地址表 | GIS | Todo | M1-06 | 包含图层名、字段和示例 |
| M1-08 | 完成 SuperMap 接入预案 | 统筹/前端/GIS | Mock Done | 无 | 有 iDesktopX、iServer、iClient3D 流程、服务模板和验收清单 |
| M1-09 | 预留 SuperMap 服务配置接口 | 后端 | Mock Done | M1-08 | `/api/supermap/config` 和 `/api/supermap/services` 可读取配置 |

## M2 平台基础功能

| ID | 任务 | 负责人 | 状态 | 依赖 | 验收标准 |
|---|---|---|---|---|---|
| M2-01 | 创建 Vue + Vite 项目 | 前端 | Runtime Verified | 无 | `npm run build` 已通过；浏览器演示截图仍待 M2-07 |
| M2-02 | 创建 FastAPI 项目 | 后端 | Runtime Verified | 无 | `pytest backend/tests` 和增强 smoke 已通过 |
| M2-03 | 实现三维场景加载 | 前端 | Blocked | M1-06 | 页面显示 SuperMap 三维场景；当前已完成 `SuperMapScene.vue` 接入边界和 mock 备用图，真实场景等待 iServer 三维服务 |
| M2-04 | 实现图层控制面板 | 前端 | Mock Done | M1-07 | 可开关风险区/道路/水系 |
| M2-05 | 实现任务列表接口 | 后端 | Mock Done | M1-07 | 前端可读取任务 |
| M2-06 | 实现航线 mock 数据 | 后端 | Mock Done | M2-02 | 前端可显示路线 |
| M2-07 | 前后端联调任务和航线 | 前端/后端 | Blocked | M2-03/M2-06 | 依赖和构建已通过；仍需启动前后端并完成浏览器演示截图 |

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
