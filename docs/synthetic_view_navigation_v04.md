# 合成视图匹配视觉自主导航 v0.4

更新日期：2026-06-09

## 主线定位

本项目主线调整为：基于 DEM、正射影像和三维地理场景的合成视图匹配视觉自主导航仿真系统。

当前 v0.4 不接真实飞控，不输出飞控指令；只在软件仿真层生成视觉定位观测，并用该观测修正导航状态。

## v0.4 链路

```text
UAV 当前图像 + 初始位姿/航线先验
-> 自动瓦片索引粗检索
-> 基于 DEM + 正射影像 + 建筑上下文构造候选 UAV 合成视图
-> UAV 图像与合成视图匹配
-> 输出视觉估计位置、修正向量、置信度、误差半径、匹配点数和失败原因
-> 写入导航状态，驱动 fused_position 在仿真中向视觉估计位置收敛
```

## 已新增接口

### 生成候选合成视图

```http
POST /api/vision/synthetic-views
```

输入：

```json
{
  "task_id": "task_001",
  "image_id": "demo_uav_001",
  "top_k_tiles": 3
}
```

输出核心字段：

- `initial_pose`：带偏移的 UAV 初始位姿。
- `route_prior_pose`：航线/任务先验位姿。
- `synthetic_views`：候选合成视图。
- `render_source`：正射、DEM、建筑上下文来源。

### 合成视图视觉定位

```http
POST /api/vision/localize
```

输出核心字段：

- `best_estimated_pose`
- `confidence`
- `error_radius_m`
- `matched_points`
- `inlier_ratio`
- `correction_vector_m`
- `failure_reason`
- `matches`

### 查询单帧定位结果

```http
GET /api/vision/localizations/{image_id}?task_id=task_001
```

## v0.4 合成视图最小实现

当前合成视图使用确定性原型：

- 候选区域：来自 `vision_tile_index` 自动瓦片。
- 合成图像：使用瓦片缩略图作为正射纹理代理。
- DEM 上下文：从 `frontend/public/demo/luojia_terrain_preview.json` 采样候选视图地面高程。
- 建筑上下文：从 `frontend/public/demo/luojia_buildings_preview.json` 统计候选视图覆盖建筑数量。
- 相机姿态：由初始位姿、候选瓦片中心、UAV 相机 pitch 等参数确定。
- 匹配分数：v0.4 暂用预计算结果作为代理，接口形态已按真实匹配算法预留。

这不是最终真实渲染器。v0.5 可替换为 ORB/SIFT/LoFTR/LightGlue 之一，并把 `image_url` 替换为真实合成视图渲染结果。

## 导航接入

导航状态机现在读取 `/api/vision/localize` 同源服务输出：

- `visual_position` 使用 `best_estimated_pose`。
- `visual_position.error_radius_m` 记录视觉误差半径。
- `visual_position.correction_vector_m` 记录从初始偏移位姿到视觉估计位姿的修正向量。
- `visual_position.synthetic_view_id` 记录匹配到的合成视图。
- `visual_frame.synthetic_image` 指向最佳合成视图图像。

高置信结果进入 `autonomous` 模式并参与 `fused_position` 收敛；低置信结果进入 `review`，不直接修正仿真主状态。

## 前端展示

前端已在视觉定位卡片中展示：

- UAV 当前图像。
- 最佳候选合成视图。
- 置信度、匹配点、内点比例。
- 误差半径。
- 修正向量。
- 参考位置、视觉估计位置、融合位置。

## 自动视觉帧确定规则

2026-06-09 更新后，`/api/vision/images` 不再依赖手工固定 4 帧，而是由后端根据航线自动生成视觉帧元数据。

当前规则：

- 按距离间隔抽帧：约每 `280m` 生成一个视觉帧。
- 按关键变化抽帧：航向变化超过约 `24°` 时生成关键帧。
- 到达阶段抽帧：航线末端生成 `route_arrival` 帧，用于低置信/复核演示。
- 起点不触发视觉融合，导航先从参考航线状态开始。

自动帧字段：

- `frame_trigger`：`distance_interval`、`heading_change` 或 `route_arrival`。
- `route_distance_m`：该帧对应的航线累计距离。
- `source_tile_id`：该帧使用的正射瓦片来源。
- `source`：`auto_dem_ortho_route_sampler`。

当前 UAV 图像并非实飞数据，而是由路线位置选择正射瓦片作为可显示的仿真视觉帧代理；DEM 与建筑上下文在后续合成视图定位服务中参与候选视图和位姿估计。

## 验收命令

```powershell
$env:TEMP='E:\supermap_project\.tmp'
$env:TMP='E:\supermap_project\.tmp'
& 'E:\anaconda\envs\supermap_nav\python.exe' -m pytest backend\tests
& 'E:\supermap_project\scripts\check_backend_smoke_full.ps1' -PythonExe 'E:\anaconda\envs\supermap_nav\python.exe'
cd frontend
npm run build
```

当前验证结果：

- `backend/tests`：10 passed。
- backend full smoke：passed。
- frontend build：passed。
