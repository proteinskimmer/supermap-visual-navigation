# 视觉匹配模块需求与框架设计

## 1. 模块目标

视觉匹配模块用于视觉自主导航仿真中的视觉地理重定位。输入固定无人机视角图像或模拟视角图，系统返回候选地理瓦片、置信度、匹配点数量、内点比例、偏移估计和解释原因，并在三维任务场景中更新视觉定位状态。

当前阶段优先完成“预计算结果 + 可解释导航状态”的稳定演示框架，不接真实飞控，不输出控制指令，不承诺真实无人机实时定位。视觉自主导航在本项目中体现为软件仿真中的定位状态更新和导航决策链路，而不是实际飞控闭环。

系统同时保留视觉辅助导航模式：当匹配置信度较低、需要人工复核或需要与 GNSS/参考航线对照时，视觉结果只作为定位参考，不直接修正 UAV 导航状态。

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
- 不把视觉匹配结果包装为真实无人机飞控定位闭环。
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
  LocalFeatureProvider
  RansacVerifier
```

接入真实算法时建议保持输出结构不变：

1. 图像预处理：归一化、尺寸调整、畸变校正。
2. 粗检索：DINOv2 或轻量 embedding 找出 Top-K 瓦片。
3. 局部匹配：LoFTR 或 LightGlue 输出匹配点。
4. 几何验证：OpenCV RANSAC 计算单应性或基础矩阵。
5. 结果解释：生成置信度、内点比例、偏移估计和失败原因。
6. 导航状态更新：高置信结果用于视觉自主模式下的位置修正，低置信结果进入辅助导航/人工复核状态。
7. 前端展示：沿用当前候选区域、视觉定位状态和遥测面板。

## 7. 前端展示要求

- 右侧提供 UAV 实时影像帧窗口；真实图片缺失时使用占位预览。
- 支持 Top-K 候选数量切换，地图与候选列表同步更新。
- 中间地图高亮候选瓦片。
- 最优候选区域用更强样式展示。
- 被拒绝候选区域使用虚线或弱化样式。
- 低置信候选显示“复核”状态，用于说明系统不会盲目输出高置信定位。
- 右侧显示视觉定位状态、候选排名、置信度条、匹配点、内点比例、偏移量、状态和解释原因。
- 遥测面板显示定位源、视觉偏差和导航模式。
- 界面保留“视觉自主 / 辅助导航”模式切换，用于说明二者关系。
- 显示算法流程时间线，答辩时用于说明模块链路。
- 显示瓦片索引调试信息，包括瓦片数量、来源和预计算特征数量。
- 视觉匹配完成后写入仿真事件日志。
- 任务报告展示视觉匹配摘要，包括输入图数量、最高置信候选、平均匹配点、几何验证状态和复核数量。

## 8. 验收标准

- 至少 3 张固定输入图可选择。
- 每张输入图至少返回 3 个候选区域。
- 每个候选区域包含置信度、匹配点、内点比例、偏移估计和解释原因。
- 至少包含 1 个低置信度/需人工复核样例。
- 前端可切换 Top 1、Top 2、Top 3 候选显示。
- 视觉匹配事件能出现在仿真事件日志。
- 任务报告包含视觉匹配摘要。
- 前端地图可高亮候选区域。
- 答辩口径明确：本模块是软件仿真中的视觉自主导航状态更新，不是实际飞控控制；辅助导航是低置信或降级场景下的扩展能力。
- 后续接真实模型时不需要修改前端接口。

## 9. 日志和状态更新要求

视觉模块每次完成实质性工作后，需要同步更新：

- `docs/project_management/12_project_status_log.md`：记录推进内容、验证情况、阻塞和关键决策。
- `docs/project_management/08_task_board.md`：更新 M5 相关任务状态。
- `docs/project_management/10_acceptance_checklist.md`：只勾选已经验证过的条目，真实运行和真实图片不得提前勾选。
- `docs/project_management/09_interfaces_and_data_contracts.md`：接口字段新增、删除或语义变化时必须同步。

当前未完成项必须保留为阻塞或待验收：

- 真实模型推理尚未接入。

## 10. 当前演示数据

当前已准备：

- `demo_uav_001`：河谷巡检视角。
- `demo_uav_002`：居民区边缘视角。
- `demo_uav_003`：起飞区回看视角。
- `demo_uav_004`：烟雾遮挡低置信视角，用于演示人工复核。
- `tile_018`、`tile_021`、`tile_034`、`tile_041`、`tile_052` 五个候选瓦片。
## 2026-06-09 Luojia 自动瓦片生成更新

`vision_tile_index` 现在由 `scripts/generate_luojia_vision_tiles.py` 从真实珞珈山正射影像自动生成，不再以 5 个手写瓦片作为当前主数据。

当前生成结果：

- 源影像：`data_sources/luojia_mountain/raw_test_data/珞珈山影像.tif`
- 地理参考：`data_sources/luojia_mountain/raw_test_data/珞珈山影像.tfw`
- 网格规模：5 行 x 8 列
- 瓦片数量：40
- 索引输出：`demo_data/generated/luojia_vision_tiles.json`
- 前端缩略图：`frontend/public/demo/vision_tiles/*.png`
- demo 接入：`demo_data/task_demo.json` 的 `vision_tile_index`

这些瓦片是视觉自主导航定位参考库的当前空间单元。预计算 `vision_matches` 已重新绑定到自动生成瓦片 ID；真实在线视觉模型推理仍属于后续接入项。

## 2026-06-09 合成视图匹配 v0.4 更新

视觉模块主线已经从“瓦片匹配展示”推进为“合成视图匹配视觉自主导航仿真”。

新增链路：

- UAV 当前图像与初始位姿/航线先验进入视觉模块。
- 自动瓦片只作为候选区域粗检索和调试索引。
- 系统基于候选瓦片、DEM 高程、正射影像纹理和建筑上下文生成候选 UAV 合成视图。
- v0.4 暂以预计算匹配作为代理分数，输出视觉估计位姿、修正向量、置信度、误差半径、匹配点数和失败原因。
- 导航状态机读取视觉定位观测并更新 `visual_position` 与 `fused_position`。

新增接口：

- `POST /api/vision/synthetic-views`
- `POST /api/vision/localize`
- `GET /api/vision/localizations/{image_id}`

当前边界：

- 不接真实飞控。
- 不输出真实飞控指令。
- UAV 影像当前仍为仿真/演示图像。
- v0.4 合成视图为正射瓦片代理图 + DEM/建筑上下文元数据；v0.5 再接入 ORB/SIFT/LoFTR/LightGlue 等真实匹配算法。

## 11. 主线升级：合成视图匹配视觉地理重定位

视觉模块后续主线不再停留于“最相似瓦片 + 偏移量”的演示口径，而应升级为：

> DEM/正射影像/三维场景驱动的合成视图匹配视觉地理重定位。

推荐链路：

```text
UAV 当前图像 + 初始位姿先验
-> 候选瓦片/候选区域粗检索
-> 对每个候选位姿渲染合成 UAV 视图
-> 将真实/仿真 UAV 图像与合成视图做特征或光度匹配
-> 几何验证与位置优化
-> 输出视觉位置、偏移量、置信度、误差半径和失败解释
-> 写入导航状态，用于仿真平台验证轨迹修正
```

瓦片索引仍然保留，但定位为粗检索和可视化调试层。最终成果应体现“合成视图匹配如何反推 UAV 位置”，而不是只展示一个匹配瓦片。

阶段目标：

- v0.3：保留预计算瓦片匹配，作为候选区域检索框架。
- v0.4：增加 DEM + 正射影像生成候选 UAV 合成视图。
- v0.5：接入 ORB/SIFT/LoFTR/LightGlue 等真实匹配算法，输出位置估计和误差半径。
- v0.6：将视觉定位结果写入融合导航状态，演示无人机从偏移状态回到正确航线。
