# 最终提交包模板

本模板用于比赛最终提交前整理文件。实际提交要求以比赛官方通知为准。

## 1. 推荐目录结构

```text
submission/
  README.md
  project_book.md
  deploy_guide.md
  system_design.md
  data_description.md
  source_code_structure.md
  ppt/
    final_presentation.pptx
  video/
    demo_video.mp4
  screenshots/
    S-01_idesktopx_workspace.png
    S-03_iserver_publish.png
    S-06_dashboard_overview.png
    S-09_candidate_routes.png
    S-15_replanning_compare.png
    S-17_vision_candidates.png
  source/
    backend/
    frontend/
    demo_data/
    config/
    scripts/
  docs/
    project_management/
    supermap_integration/
    delivery/
```

## 2. README 建议内容

最终提交包 `README.md` 应包含：

- 项目名称。
- 一句话定位。
- 技术栈。
- SuperMap 使用说明。
- 启动方式。
- 演示流程。
- 项目边界说明。

## 3. 提交前检查

### 代码

- [ ] 后端可启动。
- [ ] 前端可启动。
- [ ] 无全局环境依赖说明缺失。
- [ ] 无绝对路径依赖，或已在部署说明中解释。
- [ ] 不提交 `node_modules`。
- [ ] 不提交 `.venv` 或 Conda 环境目录。
- [ ] 不提交 `__pycache__`。

### 文档

- [ ] 项目书完成。
- [ ] 系统设计说明完成。
- [ ] 部署说明完成。
- [ ] 数据说明完成。
- [ ] 源码结构说明完成。
- [ ] SuperMap 接入说明完成。
- [ ] 项目边界说明明确。

### 数据

- [ ] demo 数据可解析。
- [ ] 真实数据来源可说明。
- [ ] 服务 URL 已记录。
- [ ] 视觉图片或占位策略已说明。

### 材料

- [ ] PPT 完成。
- [ ] 演示视频完成。
- [ ] 截图素材齐全。
- [ ] 视频和 PPT 展示的是同一套系统流程。

## 4. 不应提交内容

- `frontend/node_modules/`
- `backend/.venv/`
- Conda 环境目录。
- `__pycache__/`
- `.env`、本地账号密码、授权文件。
- 未脱敏的个人信息。
- 无法说明来源的数据。

## 5. 最终演示必过流程

1. 打开系统。
2. 加载任务区域。
3. 展示风险区和障碍物。
4. 点击规划生成三条候选航线。
5. 展示风险评分和高程剖面。
6. 启动仿真。
7. 添加临时风险区。
8. 触发动态重规划。
9. 展示视觉匹配候选区域。
10. 生成任务报告。

## 6. 提交前口径检查

必须避免：

- 暗示系统能直接控制真实无人机。
- 暗示视觉匹配已经是真实实时定位闭环。
- 暗示系统已完成真实飞控安全验证。

推荐表述：

> 本项目聚焦低空任务的软件仿真验证和辅助规划，基于 SuperMap GIS 底座完成三维环境构建、航线规划、风险校验、动态重规划和视觉定位辅助展示。
