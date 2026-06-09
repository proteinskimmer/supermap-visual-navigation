# 阶段验收与最终提交清单

## 2026-06-09 监督复核状态

当前已通过并可作为阶段证据：

- [x] iDesktopX 2025 本机安装、许可状态和 `CBD` 样例三维场景截图已归档。
- [x] iServer 2025U1A 本机安装、8090 端口、管理页、服务列表和帮助页已验收。
- [x] iClient3D SDK、`supermap-minimal.html`、WebGL2、Viewer 创建和官方 `3D-CBD` 的 `scene.open(sceneUrl)` 已截图验收。
- [x] 前端项目工作台已在 SuperMap 三维场景上叠加候选航线、风险区、视觉候选区、起终点等业务图形。
- [x] `low_altitude_demo.smwu` 工作空间已保存。
- [x] 项目自建 `map-low_altitude_demo` 地图服务已发布并返回 `low_altitude_demo_map`。
- [x] 项目自建 `data-low_altitude_demo` 数据服务已发布 8 个业务数据集。
- [x] 项目自建 `3D-low_altitude_demo` 三维服务已发布，`scenes.json` 可访问并包含 `low_altitude_demo` 场景标记。
- [x] 前端/后端 SuperMap 配置已切换为项目自建 scene/map/data 服务，`/api/supermap/services` 三项状态为 `verified`。
- [x] `scripts/check_low_altitude_demo_publish_ready.ps1` 通过。
- [x] `scripts/check_low_altitude_3d_gate.ps1` 通过。
- [x] `scripts/check_supermap_delivery_gate.ps1` 通过。
- [x] `scripts/check_project_runtime.ps1` 通过，包含前端 build、后端测试和增强 smoke。
- [x] `scripts/check_supermap_goal_evidence.ps1 -Strict` 通过，SuperMap 目标证据完整。
- [x] `scripts/prepare_submission_package.ps1` 通过，已生成 `release/low_altitude_demo_submission/` 阶段证据包，版本为 `v0.3-supermap-verified`。
- [x] `scripts/check_git_artifact_policy.ps1` 通过，已建立源码/证据文档入 Git、release/本地二进制/临时产物不入 Git 的归属策略。

当前仍未通过，禁止在材料中写成已完成：

- [ ] 完整演示闭环截图尚未按清单命名和说明。
- [ ] PPT、演示视频和最终比赛提交包尚未完成；当前 release 只能作为阶段证据包和答辩材料整理基线。
- [ ] 视觉输入仍是演示占位图，不是真实航拍图。

## M1 环境与 SuperMap 底座验收

- [ ] iDesktopX 2025 安装完成。
- [ ] iServer 2025 安装完成并可访问管理页面。
- [ ] 任务区域确定，范围适合演示。
- [ ] 影像、DEM、矢量、风险区数据可在 iDesktopX 叠加。
- [ ] 三维场景制作完成。
- [ ] iServer 发布三维服务。
- [ ] 输出服务 URL、图层列表和字段说明。
- [ ] 保留服务发布截图。

## M2 平台基础功能验收

- [ ] Vue 前端可以启动。
- [ ] FastAPI 后端可以启动。
- [ ] `/api/health` 正常返回。
- [ ] 前端可以加载 SuperMap 三维场景。
- [ ] 前端可以展示任务区域。
- [ ] 前端可以展示 mock 航线。
- [ ] 图层控制可用。
- [ ] 前后端完成至少一次联调。

## M3 航线规划与风险校验验收

- [ ] A* 可以生成可显示航线。
- [ ] 可以生成最短、最安全、综合最优三种航线。
- [ ] 航线不会明显穿越禁入区。
- [ ] 风险校验可以输出评分。
- [ ] 风险校验可以输出风险原因。
- [ ] 风险航段可以在前端高亮。
- [ ] 高程剖面可以在前端展示。

## M4 动态重规划与仿真验收

- [ ] 仿真时间轴可播放、暂停、重置。
- [ ] 飞行点或航迹可以动态推进。
- [ ] 事件日志随时间更新。
- [ ] 可以添加临时风险区。
- [ ] 系统能判断临时风险区是否影响当前航线。
- [ ] 可以触发局部重规划。
- [ ] 新旧航线在三维场景中对比清晰。

## M5 视觉匹配验收

- [x] 至少准备 3 张示例输入图元数据。
- [x] 至少准备 1 张低置信度/需人工复核样例。
- [ ] 至少准备 3 张真实示例输入图文件。
- [x] 每张图有候选匹配区域。
- [x] 结果包含置信度。
- [x] 结果包含匹配点数量或可解释指标。
- [x] 前端可以显示输入图占位小窗。
- [ ] 前端可以显示真实输入图。
- [x] 前端可以切换 Top 1、Top 2、Top 3 候选。
- [x] 前端可以在 mock 三维/二维场景高亮候选区域。
- [x] 视觉匹配事件可以写入底部事件日志。
- [x] 任务报告包含视觉匹配摘要。
- [x] 后端保留 provider 抽象接入点。
- [ ] 前端在安装依赖后完成真实运行验收。
- [x] 答辩口径明确：视觉定位辅助，不是飞控控制。

## M6 比赛材料验收

- [ ] 系统介绍文档完成。
- [ ] 部署说明完成。
- [ ] 数据说明完成。
- [ ] 源代码目录说明完成。
- [ ] PPT 完成。
- [ ] 演示视频完成。
- [ ] 至少完成 3 次完整演示彩排。
- [ ] 所有截图和视频使用同一套稳定 demo 数据。

## 最终 Demo 必过流程

1. 打开系统首页。
2. 加载 SuperMap 三维任务区域。
3. 打开风险区、道路、建筑、地形图层。
4. 选择示范任务。
5. 输入或选择起点、终点。
6. 生成三条候选航线。
7. 查看航线评分和风险原因。
8. 选择综合最优航线。
9. 开始仿真播放。
10. 中途添加临时风险区。
11. 触发重规划。
12. 展示新旧航线对比和事件日志。
13. 执行视觉匹配演示。
14. 高亮候选区域和置信度。
15. 生成任务报告。

## 最终提交包建议

```text
submission/
  README.md
  deploy_guide.md
  system_design.md
  data_description.md
  source_code_structure.md
  frontend/
  backend/
  demo_data/
  screenshots/
  video/
  ppt/
```

## 一票否决风险

- [ ] 演示时 SuperMap 三维场景无法加载。
- [ ] 航线和风险区坐标错位。
- [ ] 动态重规划无法触发。
- [ ] 前后端启动步骤只有开发者本人知道。
- [ ] PPT 中承诺了系统没有实现的功能。
- [ ] 材料暗示真实飞控或真实执行能力。
