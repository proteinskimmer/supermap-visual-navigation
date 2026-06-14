# 截图素材清单

本清单用于 PPT、系统介绍文档和演示视频封面。截图应尽量使用同一套珞珈山 demo 数据，保持口径统一。

## 1. 核心截图

| 编号 | 截图 | 用途 | 状态 |
|---|---|---|---|
| S-01 | 前端视觉自主导航指挥舱全景 | PPT 首页/系统总览 | Done：`frontend_luojia_scene_headless.png` |
| S-02 | SuperMap scene/map/data 服务状态 | 证明 GIS 底座接入 | Done：工作台截图和 iServer REST 截图已归档 |
| S-03 | iServer 珞珈山服务或服务列表 | 证明服务发布 | Done：`iserver_services_list.png` 等 |
| S-04 | ORB 视觉定位证据面板 | 展示特征匹配和定位质量 | Partial：指挥舱截图可覆盖，建议补局部特写 |
| S-05 | 参考轨迹与融合轨迹对比 | 展示视觉导航主线 | Partial：指挥舱截图可覆盖，建议补播放中截图 |
| S-06 | 导航遥测和事件流 | 展示后端权威状态消费 | Partial：指挥舱截图可覆盖，建议补局部特写 |
| S-07 | 任务报告与视觉导航质量 | 展示报告输出 | Done：`v05_report_page_summary_route_risk_profile.png` |
| S-08 | 风险告警或重规划支撑 | 展示安全支撑服务 | Todo：完整彩排时补 |

## 2. SuperMap / 数据证据

| 编号 | 截图 | 用途 | 状态 |
|---|---|---|---|
| S-09 | iDesktopX 工作空间/地图图层 | 证明数据制作 | Done：`idesktopx_low_altitude_demo_map_layers.png`，珞珈山 GUI 图可后补 |
| S-10 | iServer 3D 服务 scenes JSON | 证明三维服务可访问 | Done：已有 low_altitude 与 Luojia 门禁证据 |
| S-11 | iServer data datasets JSON | 证明业务数据集发布 | Done：已有数据服务截图 |
| S-12 | iObjectSpy 地图预览 | 证明脚本化数据渲染 | Done：`low_altitude_demo_map_iobjectspy_preview.png` |

## 3. 可选截图

| 编号 | 截图 | 用途 | 状态 |
|---|---|---|---|
| S-13 | v0.5 一键门禁命令行输出 | 展示工程可复验 | Optional |
| S-14 | ORB 匹配连线证据图片 | 展示算法细节 | Optional |
| S-15 | API 文档页面 | 展示后端接口 | Optional |
| S-16 | 项目目录结构 | 部署说明/答辩备选 | Optional |

## 4. 截图规范

- 分辨率建议 1920x1080。
- 浏览器缩放 100%。
- 使用同一套珞珈山 demo 数据。
- 截图前关闭控制台、下载栏、通知弹窗。
- 文件命名建议：

```text
screenshots/S-01_luojia_cockpit_overview.png
screenshots/S-03_orb_visual_localization.png
screenshots/S-05_navigation_quality_report.png
```

## 5. PPT 推荐用图映射

| PPT 页 | 推荐截图 |
|---|---|
| 第 1 页 | S-01 |
| 第 5 页 | S-01、S-02、S-03 |
| 第 6 页 | S-04 或 ORB 匹配证据图 |
| 第 8 页 | S-01、S-05、S-06 |
| 第 9 页 | S-07、S-08 |
| 第 10 页 | v0.5 门禁输出或质量报告截图 |
