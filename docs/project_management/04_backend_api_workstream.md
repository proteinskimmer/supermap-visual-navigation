# 分工细化：后端与平台接口

## 1. 角色目标

使用 FastAPI 构建平台服务层，统一管理任务、航线、风险分析、仿真事件、视觉匹配结果和报告数据，为前端和算法模块提供稳定接口。

## 2. 技术栈

- Python 3.11。
- FastAPI。
- SQLite，后期可切 PostgreSQL。
- Pydantic。
- Shapely / NetworkX / NumPy。
- OpenCV / PyTorch，可由视觉模块按需引入。

## 3. 核心模块

| 模块 | 说明 |
|---|---|
| task | 任务管理、任务区域、起终点、参数 |
| layer | 图层和 GIS 服务配置 |
| route | 航线生成、航线详情、候选航线 |
| risk | 风险校验、评分、风险原因 |
| simulation | 仿真状态、事件日志、重规划触发 |
| vision | 视觉匹配任务、结果查询 |
| report | 任务报告生成 |

## 4. 推荐目录结构

```text
backend/
  app/
    main.py
    api/
      tasks.py
      routes.py
      risks.py
      simulations.py
      vision.py
      reports.py
    core/
      config.py
      gis_client.py
    models/
      schemas.py
    services/
      task_service.py
      route_service.py
      risk_service.py
      simulation_service.py
      vision_service.py
      report_service.py
    algorithms/
      astar.py
      risk_score.py
      replanner.py
    data/
      demo_seed.json
```

## 5. API 优先级

### 第一批：平台骨架

- `GET /api/health`
- `GET /api/tasks`
- `GET /api/tasks/{task_id}`
- `GET /api/layers`

### 第二批：航线和风险

- `POST /api/routes/plan`
- `GET /api/routes/{route_id}`
- `POST /api/risks/analyze`

### 第三批：仿真和重规划

- `POST /api/simulations/start`
- `GET /api/simulations/{simulation_id}/events`
- `POST /api/simulations/{simulation_id}/temporary-risk`
- `POST /api/routes/replan`

### 第四批：视觉和报告

- `POST /api/vision/match`
- `GET /api/vision/{match_id}`
- `GET /api/reports/{task_id}`

## 6. 执行步骤

### 第 1 步：搭建服务

- 创建 FastAPI 项目。
- 完成健康检查接口。
- 配置跨域。
- 准备 demo 数据。

### 第 2 步：统一数据模型

- 定义任务、点、航线、风险区、事件、视觉结果模型。
- 所有坐标统一使用 `[lon, lat, height]`。
- 所有距离统一使用米。

### 第 3 步：接入算法

- 先用 mock 算法返回固定航线。
- 再接入 A* 真实计算。
- 风险校验先根据多边形相交和距离判断。

### 第 4 步：接入 GIS

- 保存 iServer 服务配置。
- 能够查询或加载任务区、风险区、障碍物数据。
- 如果 iServer 联调困难，先使用导出的 GeoJSON 保证主流程。

### 第 5 步：支撑演示

- 固化一套 demo 数据。
- 提供重置接口。
- 保证演示过程中接口响应稳定。

## 7. 验收标准

- 前端可以通过 API 获取任务、图层、航线、风险、事件、视觉结果。
- 所有接口有稳定示例输入输出。
- 算法失败时返回可解释错误，不导致前端崩溃。
- 演示数据可一键恢复。

