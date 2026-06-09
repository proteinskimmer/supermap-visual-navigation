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

返回：任务摘要、航线、风险、事件、视觉匹配结果和 `VisionSummary` 视觉摘要。

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
- `ApiResponse[ReportData]`

测试与 smoke：

```powershell
.\scripts\check_backend_smoke.ps1
.\scripts\check_backend_smoke_full.ps1
cd backend
pytest
```

`check_backend_smoke.ps1` 是轻量服务层检查；`check_backend_smoke_full.ps1` 会额外检查 FastAPI TestClient API 契约，要求当前 Python 环境已安装 `backend/requirements.txt`。
