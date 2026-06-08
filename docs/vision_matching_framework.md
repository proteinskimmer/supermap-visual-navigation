# 视觉匹配模块需求与框架设计

## 1. 模块目标

视觉匹配模块用于低空任务仿真中的视觉地理配准辅助演示。输入固定无人机视角图像或模拟视角图，系统返回候选地理瓦片、置信度、匹配点数量、内点比例、偏移估计和解释原因，并在三维任务场景中高亮候选区域。

当前阶段优先完成“预计算结果 + 可解释展示”的稳定演示框架，不接真实飞控，不输出控制指令，不承诺真实无人机实时定位。

## 2. 当前实现范围

已完成的框架内容：

- 后端视觉服务层：`backend/app/services/vision_service.py`
- 后端视觉接口：`backend/app/api/vision.py`
- 请求模型扩展：`backend/app/models/schemas.py`
- 演示数据扩展：`demo_data/task_demo.json`
- 前端 API 封装：`frontend/src/services/api.js`
- 前端视觉样例选择和候选结果展示：`frontend/src/App.vue`
- 前端候选区域、候选详情和算法流程样式：`frontend/src/styles.css`

当前采用 `precomputed_demo` provider，从 demo JSON 中读取固定结果。后续接入 DINOv2、LoFTR、LightGlue 或 OpenCV RANSAC 时，优先替换服务层 provider，不改变前端展示接口。

## 3. 不做范围

- 不接真实无人机飞控。
- 不生成航点上传、姿态控制、速度控制等真实执行指令。
- 不把视觉匹配结果作为真实定位闭环。
- 当前不强制引入 PyTorch、OpenCV、LightGlue、LoFTR 等重依赖。
- 当前不处理大规模影像切片生产，只保留瓦片索引结构。

## 4. 数据结构

### 4.1 输入图像清单

字段位于 `demo_data/task_demo.json` 的 `vision_images`。

| 字段 | 说明 |
|---|---|
| id | 图像编号，如 `demo_uav_001` |
| task_id | 所属任务 |
| name | 前端展示名称 |
| query_image | 图像路径或资源 URL |
| capture_time_s | 仿真时间点 |
| resolution | 图像分辨率 |
| camera | 虚拟相机参数 |
| scene_tags | 场景标签 |
| expected_center | 预期中心点，供演示校验 |

### 4.2 候选瓦片索引

字段位于 `vision_tile_index`。

| 字段 | 说明 |
|---|---|
| tile_id | 瓦片编号 |
| task_id | 所属任务 |
| name | 瓦片名称 |
| center | 瓦片中心点，经度、纬度、高度 |
| bbox | 瓦片边界多边形 |
| source | 瓦片来源 |
| feature_count | 预计算特征数量或占位指标 |

### 4.3 匹配结果

字段位于 `vision_matches`。

| 字段 | 说明 |
|---|---|
| match_id | 匹配结果编号 |
| image_id | 输入图像编号 |
| provider | 结果提供者，当前为 `precomputed_demo` |
| status | 执行状态 |
| algorithm_trace | 可解释流程标签 |
| candidates | 候选区域列表 |

候选区域字段：

| 字段 | 说明 |
|---|---|
| tile_id | 匹配到的瓦片编号 |
| confidence | 置信度，0 到 1 |
| matched_points | 匹配点数量 |
| inlier_ratio | 几何验证内点比例 |
| bbox | 候选区域边界 |
| center | 候选中心点 |
| offset_m | 估计偏移，单位米 |
| status | `best`、`candidate` 或 `rejected` |
| reason | 候选解释原因 |

## 5. API 设计

### 5.1 获取输入图像清单

```http
GET /api/vision/images?task_id=task_001
```

返回当前任务可用于演示的无人机视角图像。

### 5.2 获取候选瓦片索引

```http
GET /api/vision/tiles?task_id=task_001
```

返回任务区域内的候选瓦片索引，用于前端调试或后续 SuperMap 图层联动。

### 5.3 执行视觉匹配

```http
POST /api/vision/match
Content-Type: application/json

{
  "task_id": "task_001",
  "image_id": "demo_uav_001",
  "top_k": 3,
  "algorithm_mode": "precomputed"
}
```

当前只支持 `precomputed` 模式。返回候选区域按置信度降序排列，并自动补充 `rank` 和 `candidate_count`。

### 5.4 查询匹配结果详情

```http
GET /api/vision/matches/match_demo_001
```

按 `match_id` 查询已有匹配结果。

## 6. 后续算法接入点

建议在 `backend/app/services/vision_service.py` 中引入 provider 分层：

```text
VisionProvider
  PrecomputedVisionProvider
  DinoRetrieverProvider
  LoftrMatcherProvider
  LightGlueMatcherProvider
```

接入真实算法时建议保持输出结构不变：

1. 图像预处理：归一化、尺寸调整、畸变校正。
2. 粗检索：DINOv2 或轻量 embedding 找出 Top-K 瓦片。
3. 局部匹配：LoFTR 或 LightGlue 输出匹配点。
4. 几何验证：OpenCV RANSAC 计算单应性或基础矩阵。
5. 结果解释：生成置信度、内点比例、偏移估计和失败原因。
6. 前端展示：沿用当前候选区域和候选详情面板。

## 7. 前端展示要求

- 左侧提供视觉样例选择。
- 中间地图高亮候选瓦片。
- 最优候选区域用更强样式展示。
- 被拒绝候选区域使用虚线或弱化样式。
- 右侧显示候选排名、置信度、匹配点、解释原因。
- 显示算法流程标签，答辩时用于说明模块链路。

## 8. 验收标准

- 至少 3 张固定输入图可选择。
- 每张输入图至少返回 3 个候选区域。
- 每个候选区域包含置信度、匹配点、内点比例、偏移估计和解释原因。
- 前端地图可高亮候选区域。
- 答辩口径明确：本模块是视觉定位辅助和仿真验证，不是飞控控制。
- 后续接真实模型时不需要修改前端接口。

## 9. 日志和状态更新要求

视觉模块每次完成实质性工作后，需要同步更新：

- `docs/project_management/12_project_status_log.md`：记录推进内容、验证情况、阻塞和关键决策。
- `docs/project_management/08_task_board.md`：更新 M5 相关任务状态。
- `docs/project_management/10_acceptance_checklist.md`：只勾选已经验证过的条目，真实运行和真实图片不得提前勾选。
- `docs/project_management/09_interfaces_and_data_contracts.md`：接口字段新增、删除或语义变化时必须同步。

当前未完成项必须保留为阻塞或待验收：

- 真实输入图片文件尚未放入仓库。
- 前端依赖尚未安装，`npm run build` 未完成。
- 真实模型推理尚未接入。

## 10. 当前演示数据

当前已准备：

- `demo_uav_001`：河谷巡检视角。
- `demo_uav_002`：居民区边缘视角。
- `demo_uav_003`：起飞区回看视角。
- `tile_018`、`tile_021`、`tile_034`、`tile_041`、`tile_052` 五个候选瓦片。
