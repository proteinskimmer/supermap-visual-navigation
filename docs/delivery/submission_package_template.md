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
    S-01_luojia_cockpit_overview.png
    S-02_supermap_scene_services.png
    S-03_orb_visual_localization.png
    S-04_reference_vs_fused_track.png
    S-05_navigation_quality_report.png
    S-06_risk_replanning_support.png
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
- 一句话定位：基于 SuperMap GIS 的低空视觉自主导航软件仿真系统。
- 技术栈：SuperMap iDesktopX / iServer / iClient3D、FastAPI、Vue、OpenCV ORB。
- SuperMap 使用说明。
- 启动方式。
- 演示流程。
- v0.5a 验收结果。
- 项目边界说明。

## 3. 提交前检查

### 代码

- [ ] 后端可启动。
- [ ] 前端可启动。
- [ ] v0.5 一键门禁通过。
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
- [ ] v0.5a ORB 视觉定位和导航质量口径明确。
- [ ] 项目边界说明明确。

### 数据

- [ ] demo 数据可解析。
- [ ] 珞珈山 scene/map/data 服务 URL 已记录。
- [ ] 半真实 UAV 帧来源和生成方式已说明。
- [ ] ORB 匹配证据和导航质量报告已归档。
- [ ] 真实 UAV 数据缺口已说明。

### 材料

- [ ] PPT 完成。
- [ ] 演示视频完成。
- [ ] 截图素材齐全。
- [ ] 视频和 PPT 展示的是同一套系统流程。
- [ ] 至少 3 次完整彩排记录已归档。

## 4. 不应提交内容

- `frontend/node_modules/`
- `backend/.venv/`
- Conda 环境目录。
- `__pycache__/`
- `.env`、本地账号密码、授权文件。
- 未脱敏的个人信息。
- 无法说明来源的数据。

## 5. 最终演示必过流程

1. 打开系统，进入视觉自主导航指挥舱。
2. 加载珞珈山 SuperMap 三维场景和任务数据。
3. 展示参考航线、风险区、建筑/地形和 UAV 初始状态。
4. 启动视觉自主模式。
5. 展示 UAV 影像帧和 ORB 视觉定位结果。
6. 展示三维无人机按 `fused_position` 连续飞行。
7. 展示参考轨迹与融合轨迹对比。
8. 展示风险告警或重规划支撑过程。
9. 打开任务报告，展示视觉导航质量指标。
10. 说明项目边界：软件仿真、不接真实飞控、半真实 UAV 帧。

## 6. 提交前口径检查

必须避免：

- 暗示系统能直接控制真实无人机。
- 暗示已完成真实飞行视觉自主导航。
- 暗示半真实 UAV 帧来自真实飞行相机。
- 暗示三维场景已达到精细倾斜摄影级效果。

推荐表述：

> 本项目聚焦低空视觉自主导航的软件仿真验证，基于 SuperMap GIS 三维底座完成珞珈山 scene/map/data 接入，并实现 ORB 半真实视觉定位、后端融合导航时间线、三维连续飞行、风险重规划支撑和导航质量报告输出。
