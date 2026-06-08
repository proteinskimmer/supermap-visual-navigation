# 项目计划管理文档索引

本目录用于把《基于 SuperMap GIS 底座的低空视觉自主导航与三维仿真规划系统》从概念规划拆成可执行、可分工、可验收、可跟进的项目管理材料。

## 使用方式

- 每周例会先看 `00_project_execution_plan.md` 和 `08_task_board.md`。
- 每个成员领取任务前，先看自己对应的分工文档。
- 前后端、GIS、算法联调前，统一看 `09_interfaces_and_data_contracts.md`。
- 阶段验收、比赛提交前，统一看 `10_acceptance_checklist.md`。

## 文档列表

| 文件 | 用途 |
|---|---|
| `00_project_execution_plan.md` | 总体目标、边界、里程碑、团队协作机制 |
| `01_project_owner_and_architecture.md` | 项目统筹/架构负责人执行细则 |
| `02_gis_supermap_workstream.md` | SuperMap/GIS 数据负责人执行细则 |
| `03_frontend_3d_workstream.md` | 前端三维平台负责人执行细则 |
| `04_backend_api_workstream.md` | 后端与平台接口负责人执行细则 |
| `05_planning_risk_workstream.md` | 航线规划、风险校验、动态重规划负责人执行细则 |
| `06_vision_matching_workstream.md` | 视觉匹配模块负责人执行细则 |
| `07_delivery_materials_workstream.md` | 比赛材料、演示视频、答辩文档执行细则 |
| `08_task_board.md` | 可跟进任务看板 |
| `09_interfaces_and_data_contracts.md` | 模块接口、数据结构、联调约定 |
| `10_acceptance_checklist.md` | 阶段验收清单和最终提交清单 |
| `11_progress_tracking_template.md` | 日报、周会、阻塞和决策记录模板 |
| `12_project_status_log.md` | 项目推进状态日志，跨对话同步当前进度 |

## 外部专题文档

| 路径 | 用途 |
|---|---|
| `../supermap_integration/README.md` | SuperMap 接入预案入口 |
| `../supermap_integration/01_idesktopx_workflow.md` | iDesktopX 操作流程 |
| `../supermap_integration/02_iserver_publish_workflow.md` | iServer 发布流程 |
| `../supermap_integration/03_iclient3d_integration_workflow.md` | iClient3D 前端接入步骤 |
| `../supermap_integration/04_service_url_registry_template.md` | 服务地址记录模板 |
| `../supermap_integration/05_supermap_acceptance_checklist.md` | SuperMap 接入验收清单 |
| `../delivery/README.md` | 比赛交付材料入口 |
| `../delivery/ppt_outline.md` | PPT 初稿结构 |
| `../delivery/defense_script.md` | 答辩讲稿和问答口径 |
| `../delivery/demo_video_script.md` | 演示视频分镜脚本 |
| `../delivery/screenshot_shotlist.md` | 截图素材清单 |
| `../delivery/real_data_worklist.md` | 真实数据准备工作清单 |
| `../delivery/submission_package_template.md` | 最终提交包模板 |

## 当前推荐团队配置

| 角色 | 人数 | 可合并方式 |
|---|---:|---|
| 项目统筹/架构 | 1 | 可由后端或队长兼任 |
| SuperMap/GIS 数据 | 1 | 不建议与前端完全合并，容易阻塞 |
| 前端三维平台 | 1 | 可兼部分可视化报告 |
| 后端与平台接口 | 1 | 可兼任务管理和报告接口 |
| 航线规划/风险校验 | 1 | 可与后端合并 |
| 视觉匹配 | 1 | 可后置或兼职 |
| 比赛材料/演示 | 1 | 可由统筹兼任，但最后两周要集中投入 |

## 跟进节奏建议

| 节奏 | 动作 |
|---|---|
| 每日 | 每人更新今日完成、明日计划、阻塞问题 |
| 每周 | 按里程碑验收可运行成果，更新任务看板 |
| 联调前 | 检查接口文档是否已同步 |
| 阶段结束 | 对照验收清单逐项打勾 |

## 新对话启动规则

每次开始新的开发或管理对话时，先读取：

1. `12_project_status_log.md`
2. `08_task_board.md`
3. 当前任务对应的分工文档

这样可以避免重复解释项目背景，也能保证任务状态连续。
