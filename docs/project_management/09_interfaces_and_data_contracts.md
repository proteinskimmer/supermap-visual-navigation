# 接口与数据协作约定

## 1. 通用约定

- 坐标统一使用 WGS84，经纬度顺序为 `[lon, lat, height]`。
- 距离单位统一为米。
- 面数据使用 GeoJSON Polygon 或 MultiPolygon。
- 线数据使用点数组或 GeoJSON LineString。
- 接口统一以 `/api` 开头。
- 所有接口返回 `success`、`data`、`message`。

## 2. 通用响应

后端所有业务接口使用统一响应结构，并已在 FastAPI 中挂接 Pydantic `response_model`。前端只读取 `data` 字段；当 `success=false` 时展示 `message`。

```json
{
  "success": true,
  "data": {},
  "message": "ok"
}
```

错误响应：

```json
{
  "success": false,
  "data": null,
  "message": "route planning failed: no path found"
}
```

统一异常处理约定：

- `HTTPException` 返回对应 HTTP 状态码，响应体仍为 `success/data/message`。
- 请求体验证失败返回 422，并在 `data.errors` 中保留 Pydantic 校验详情。
- 未捕获异常返回 500，`message` 只暴露异常类型，避免泄露内部细节。
- 前端 API 客户端优先展示后端返回的 `message`。

## 3. 核心数据结构

### Point3D

```json
[116.12, 39.34, 120.0]
```

### Task

```json
{
  "id": "task_001",
  "name": "低空巡检示范任务",
  "area": {
    "type": "Polygon",
    "coordinates": []
  },
  "start": [116.1, 39.1, 120],
  "target": [116.2, 39.2, 120],
  "params": {
    "min_height_m": 80,
    "max_height_m": 300,
    "safe_distance_m": 50,
    "max_distance_m": 12000
  }
}
```

### Route

```json
{
  "id": "route_balanced_001",
  "mode": "balanced",
  "name": "综合最优航线",
  "points": [
    [116.1, 39.1, 120],
    [116.15, 39.12, 130],
    [116.2, 39.2, 120]
  ],
  "distance_m": 4860,
  "estimated_time_s": 620,
  "score": 86,
  "risk_level": "low"
}
```

### RiskSegment

```json
{
  "segment_id": "seg_003",
  "start_index": 3,
  "end_index": 5,
  "risk_type": "near_obstacle",
  "risk_level": "medium",
  "reason": "航线距离建筑物低于安全缓冲距离",
  "deduct_score": 12
}
```

### SimulationEvent

```json
{
  "time_s": 125,
  "type": "risk_alert",
  "title": "检测到临时风险区",
  "description": "当前航线剩余段与临时禁飞区相交，触发局部重规划",
  "position": [116.16, 39.16, 130]
}
```

### VisionImage

```json
{
  "id": "demo_uav_001",
  "task_id": "task_001",
  "name": "河谷巡检视角 01",
  "query_image": "/demo/uav_view_001.jpg",
  "capture_time_s": 74,
  "resolution": [1280, 720],
  "camera": {
    "fov_deg": 74,
    "height_m": 125,
    "pitch_deg": -38
  },
  "scene_tags": ["road", "vegetation", "river"],
  "expected_center": [116.1755, 39.1635, 125]
}
```

### VisionTile

```json
{
  "tile_id": "tile_034",
  "task_id": "task_001",
  "name": "河谷道路瓦片",
  "center": [116.1755, 39.1635, 125],
  "bbox": [
    [116.167, 39.156],
    [116.184, 39.156],
    [116.184, 39.171],
    [116.167, 39.171]
  ],
  "source": "demo_remote_sensing_mosaic",
  "feature_count": 1540
}
```

### VisionMatchResult

```json
{
  "match_id": "match_demo_001",
  "task_id": "task_001",
  "image_id": "demo_uav_001",
  "query_image": "/demo/uav_view_001.jpg",
  "provider": "precomputed_demo",
  "status": "completed",
  "algorithm_trace": ["image_normalize", "tile_retrieve_top3", "local_feature_match", "ransac_verify"],
  "candidate_count": 3,
  "total_candidate_count": 3,
  "candidates": [
    {
      "rank": 1,
      "tile_id": "tile_034",
      "confidence": 0.87,
      "matched_points": 142,
      "inlier_ratio": 0.71,
      "bbox": [],
      "center": [116.1755, 39.1635, 125],
      "offset_m": [12.5, -8.2],
      "status": "best",
      "reason": "道路弯折、水体边界和植被纹理同时匹配"
    }
  ]
}
```

### VisionSummary

```json
{
  "image_count": 4,
  "matched_image_count": 4,
  "best_tile_id": "tile_034",
  "best_confidence": 0.87,
  "average_matched_points": 107.0,
  "geometry_verified": false,
  "needs_review_count": 1,
  "summary": "已汇总 4 张视觉样例，最高置信候选为 tile_034 (87%)。其中 1 张需要人工复核。"
}
```

### SyntheticViewResponse

用于 v0.4 合成视图候选生成。当前合成图是正射瓦片代理图，真实相机渲染器留到 v0.5 替换。

```json
{
  "task_id": "task_001",
  "image_id": "demo_uav_001",
  "query_image": "/demo/uav_view_001.jpg",
  "initial_pose": {"lon": 114.3655, "lat": 30.5373, "altitude_m": 125, "yaw_deg": 32, "pitch_deg": -38, "roll_deg": 0},
  "route_prior_pose": {"lon": 114.3651, "lat": 30.5373, "altitude_m": 125, "yaw_deg": 32, "pitch_deg": -38, "roll_deg": 0},
  "candidate_count": 3,
  "synthetic_views": [
    {
      "view_id": "syn_demo_uav_001_luojia_tile_r03_c05",
      "tile_id": "luojia_tile_r03_c05",
      "image_url": "/demo/vision_tiles/luojia_tile_r03_c05.png",
      "pose": {"lon": 114.3651, "lat": 30.5373, "altitude_m": 125, "yaw_deg": 258.5, "pitch_deg": -38, "roll_deg": 0},
      "terrain_height_m": 61.2,
      "building_count": 7,
      "render_source": {"mode": "v0.4_ortho_tile_proxy_with_dem_building_context"},
      "score_prior": 0.92,
      "rank": 1
    }
  ],
  "pipeline": ["route_prior_pose", "candidate_tile_retrieval", "dem_ortho_building_synthetic_view", "image_to_synthetic_view_match", "pose_back_projection", "navigation_observation"]
}
```

### VisualLocalizationResult

用于把合成视图匹配结果转成导航观测。

```json
{
  "localization_id": "loc_demo_uav_001_synthetic_v04",
  "task_id": "task_001",
  "image_id": "demo_uav_001",
  "provider": "synthetic_view_v04_precomputed_proxy",
  "status": "localized",
  "best_estimated_pose": {"lon": 114.3651, "lat": 30.5373, "altitude_m": 125, "yaw_deg": 258.5, "pitch_deg": -38, "roll_deg": 0},
  "confidence": 0.87,
  "error_radius_m": 22.5,
  "matched_points": 142,
  "inlier_ratio": 0.71,
  "correction_vector_m": [-42.4, -8.6, 0.0],
  "matches": [
    {
      "view_id": "syn_demo_uav_001_luojia_tile_r03_c05",
      "tile_id": "luojia_tile_r03_c05",
      "confidence": 0.87,
      "error_radius_m": 22.5,
      "estimated_pose": {"lon": 114.3651, "lat": 30.5373, "altitude_m": 125, "yaw_deg": 258.5, "pitch_deg": -38, "roll_deg": 0},
      "status": "best",
      "rank": 1
    }
  ],
  "navigation_effect": "visual observation can correct the simulated navigation state toward the estimated pose",
  "failure_reason": ""
}
```

### NavigationStateFrame

后端视觉自主导航状态帧。前端播放时只根据该状态展示 UAV、遥测、视觉帧和事件，不在前端自行计算主导航状态。

```json
{
  "session_id": "nav_task_001_route_balanced_001",
  "time_s": 92,
  "reference_position": {"lon": 116.17, "lat": 39.16, "altitude_m": 125},
  "visual_position": {
    "lon": 116.1755,
    "lat": 39.1635,
    "altitude_m": 125,
    "confidence": 0.87,
    "tile_id": "tile_034",
    "match_id": "match_demo_001",
    "image_id": "demo_uav_001",
    "reason": "道路弯折、水体边界和植被纹理同时匹配"
  },
  "fused_position": {"lon": 116.1748, "lat": 39.1631, "altitude_m": 125},
  "deviation_m": 420.5,
  "navigation_mode": "autonomous",
  "telemetry": {
    "uav_id": "UAV-011",
    "speed_mps": 8.5,
    "heading_deg": 42,
    "pitch_deg": -7,
    "roll_deg": 3.1,
    "yaw_deg": 42,
    "battery_pct": 78,
    "signal": "nominal",
    "flight_time": "01:32",
    "location_source": "visual_fusion"
  },
  "visual_frame": {
    "image_id": "demo_uav_001",
    "name": "河谷巡检视角 01",
    "query_image": "/demo/uav_view_001.jpg",
    "capture_time_s": 74,
    "confidence": 0.87,
    "matched_points": 142,
    "inlier_ratio": 0.71,
    "tile_id": "tile_034",
    "status": "completed",
    "reason": "道路弯折、水体边界和植被纹理同时匹配"
  },
  "active_frame_id": "demo_uav_001",
  "active_route_id": "route_balanced_001",
  "active_event": {
    "time_s": 74,
    "type": "vision_localized",
    "title": "视觉定位更新",
    "description": "后端按 autonomous 模式更新导航状态。",
    "position": [116.1755, 39.1635, 125]
  },
  "events": []
}
```

## 4. API 草案

### GET /api/health

用途：后端健康检查。

返回：

```json
{
  "success": true,
  "data": {
    "status": "ok"
  },
  "message": "ok"
}
```

### GET /api/tasks

用途：获取任务列表。

返回：`Task[]` 简化列表。

### GET /api/tasks/{task_id}

用途：获取任务详情。

返回：完整 `Task`。

### GET /api/layers

用途：获取图层配置。

返回示例：

```json
[
  {
    "id": "risk_zone",
    "name": "风险区",
    "type": "polygon",
    "service_url": "http://localhost:8090/iserver/services/...",
    "visible": true
  }
]
```

### POST /api/routes/plan

用途：生成候选航线。

请求：

```json
{
  "task_id": "task_001",
  "start": [116.1, 39.1, 120],
  "target": [116.2, 39.2, 120],
  "modes": ["shortest", "safest", "balanced"]
}
```

返回：`Route[]`。

### POST /api/risks/analyze

用途：分析航线风险。

请求：

```json
{
  "task_id": "task_001",
  "route": {}
}
```

返回：

```json
{
  "score": 86,
  "risk_level": "low",
  "segments": [],
  "profile": [
    {
      "distance_m": 0,
      "terrain_height_m": 45,
      "flight_height_m": 120
    }
  ]
}
```

### POST /api/simulations/start

用途：启动仿真。

请求：

```json
{
  "task_id": "task_001",
  "route_id": "route_balanced_001"
}
```

返回：仿真 ID、初始事件、飞行轨迹。

### POST /api/navigation/start

用途：创建后端权威视觉自主导航会话，并返回完整时间线。

请求：

```json
{
  "task_id": "task_001",
  "route": {},
  "mode": "autonomous",
  "matcher_mode": "opencv_orb"
}
```

说明：

- `mode` 支持 `autonomous`、`assisted`。
- `matcher_mode` 默认 `synthetic_v04`，用于保留 v0.4 稳定链路。
- v0.5a 主线演示使用 `opencv_orb`，ORB 成功时写入 `visual_position/fused_position`。
- ORB 不可用、失败或未形成导航级位姿时，后端显式回退到 v0.4 `precomputed_proxy`。

返回：`NavigationSession`，包含 `session_id`、`matcher_mode`、`duration_s`、`timeline` 和后端事件流。

### GET /api/navigation/state

用途：按 `session_id` 和 `time_s` 获取最近的后端导航状态帧。

查询参数：

```text
session_id=nav_task_001_route_balanced_001
time_s=92
```

返回：`NavigationStateFrame`。

### GET /api/navigation/timeline

用途：获取导航会话完整时间线，供前端播放控制回放。

查询参数：

```text
session_id=nav_task_001_route_balanced_001
```

返回：`NavigationSession`。

### POST /api/navigation/localize

用途：将已有视觉匹配结果转换成导航可消费的视觉帧。

请求：

```json
{
  "task_id": "task_001",
  "image_id": "demo_uav_001"
}
```

返回：`NavigationVisualFrame`。

### POST /api/navigation/replan

用途：从指定时间的 `fused_position` 触发接续重规划。

请求：

```json
{
  "session_id": "nav_task_001_route_balanced_001",
  "time_s": 92,
  "temporary_risks": []
}
```

返回：新 `Route` 和后端重规划事件。

### POST /api/simulations/{simulation_id}/temporary-risk

用途：添加临时风险区。

请求：

```json
{
  "type": "no_fly",
  "level": 5,
  "polygon": {
    "type": "Polygon",
    "coordinates": []
  }
}
```

返回：风险区对象和是否影响当前航线。

### POST /api/routes/replan

用途：从当前位置重规划。

请求：

```json
{
  "task_id": "task_001",
  "current_position": [116.16, 39.16, 130],
  "target": [116.2, 39.2, 120],
  "temporary_risks": []
}
```

返回：新 `Route` 和事件说明。

### POST /api/vision/match

用途：执行视觉匹配或返回预计算匹配结果。

请求：

```json
{
  "task_id": "task_001",
  "image_id": "demo_uav_001",
  "top_k": 3,
  "algorithm_mode": "precomputed"
}
```

返回：`VisionMatchResult`。

当前只支持 `algorithm_mode=precomputed`。`candidate_count` 表示本次返回的候选数量，`total_candidate_count` 表示该输入图原始预计算候选总数。

### POST /api/vision/synthetic-views

用途：根据 UAV 图像、先验位姿和候选瓦片生成 v0.4 合成视图候选。

请求：

```json
{
  "task_id": "task_001",
  "image_id": "demo_uav_001",
  "top_k_tiles": 3
}
```

返回：`SyntheticViewResponse`。

### POST /api/vision/localize

用途：执行 v0.4 合成视图视觉定位，输出导航可消费的视觉观测。

请求：

```json
{
  "task_id": "task_001",
  "image_id": "demo_uav_001",
  "top_k_tiles": 3,
  "matcher_mode": "synthetic_v04"
}
```

返回：`VisualLocalizationResult`。

当前 `matcher_mode` 支持 `synthetic_v04`、`precomputed`、`precomputed_proxy`、`opencv_orb`、`opencv_sift`、`external_deep_matcher`。其中 `opencv_orb` 已作为 v0.5a 真实匹配 provider 接入，`opencv_sift` 和 `external_deep_matcher` 仍为预留/不可用 provider。

### GET /api/vision/localizations/{image_id}

用途：按 UAV 图像编号查询单帧 v0.4 视觉定位结果。

查询参数：

```text
task_id=task_001
```

返回：`VisualLocalizationResult`。

### GET /api/vision/images

用途：获取某个任务可选的视觉匹配输入图。

查询参数：

```text
task_id=task_001
```

返回：`VisionImage[]`。

### GET /api/vision/tiles

用途：获取某个任务的候选瓦片索引。

查询参数：

```text
task_id=task_001
```

返回：`VisionTile[]`。

### GET /api/vision/matches/{match_id}

用途：按匹配结果编号查询预计算结果详情。

返回：`VisionMatchResult`。

### GET /api/reports/{task_id}

用途：获取任务报告。

返回：任务摘要、航线、风险、事件、视觉匹配结果、`VisionSummary` 视觉摘要和 `navigation_quality` 导航质量统计。

`navigation_quality` 当前字段：

```text
matcher_mode
frame_count
visual_observation_count
provider_counts
navigation_mode_counts
location_source_counts
fallback_count
review_frame_count
confidence.average/min/max/low_confidence_count/navigation_grade_count/autonomous_grade_count
visual_error.average_m/max_m/average_error_radius_m/max_error_radius_m
fused_trajectory.average_deviation_m/max_deviation_m/final_error_m/max_step_mps/smoothness_passed
quality_grade
summary
```

v0.5a 报告默认使用 `opencv_orb` 生成导航质量统计；UAV 帧仍为半真实演示帧时，报告口径必须说明这是软件仿真验证结果，不是真实飞行测试结果。

## 5. 联调规则

- 前端需要字段变更时，先在本文件修改草案，再通知后端。
- 后端字段变更必须兼容前端已有展示，至少保留旧字段到当前里程碑结束。
- GIS 坐标系或图层名变更必须同步给前端、后端和规划算法。
- 算法输出的路线点不得使用屏幕坐标或局部坐标，必须能回到三维地图叠加。

## 6. 后端契约与测试

当前后端已为核心接口补充 Pydantic 响应模型：

- `ApiResponse[HealthData]`
- `ApiResponse[list[TaskSummary]]`
- `ApiResponse[TaskDetailData]`
- `ApiResponse[list[LayerConfig]]`
- `ApiResponse[list[Route]]`
- `ApiResponse[RiskAnalysis]`
- `ApiResponse[SimulationStartData]`
- `ApiResponse[TemporaryRiskData]`
- `ApiResponse[ReplanData]`
- `ApiResponse[list[VisionImage]]`
- `ApiResponse[list[VisionTile]]`
- `ApiResponse[VisionMatchResult]`
- `ApiResponse[SyntheticViewResponse]`
- `ApiResponse[VisualLocalizationResult]`
- `ApiResponse[ReportData]`
- `ApiResponse[NavigationSession]`
- `ApiResponse[NavigationStateFrame]`
- `ApiResponse[NavigationVisualFrame]`
- `ApiResponse[ReplanData]` for `/api/navigation/replan`

测试与 smoke：

```powershell
.\scripts\check_backend_smoke.ps1
.\scripts\check_backend_smoke_full.ps1
cd backend
pytest
```

`check_backend_smoke.ps1` 是轻量服务层检查；`check_backend_smoke_full.ps1` 会额外检查 FastAPI TestClient API 契约，要求当前 Python 环境已安装 `backend/requirements.txt`。
