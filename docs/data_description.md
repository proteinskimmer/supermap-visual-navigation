# 数据说明

当前使用 `demo_data/task_demo.json` 作为固定演示数据。

## 1. task

任务基础信息：

- `id`：任务编号。
- `display_name`：中文展示名称。
- `area`：任务区域 GeoJSON Polygon。
- `start`：起点 `[lon, lat, height]`。
- `target`：目标点 `[lon, lat, height]`。
- `params`：高度、安全距离、最大航程等参数。

## 2. layers

前端图层配置：

- `terrain`：地形 DEM。
- `imagery`：遥感影像。
- `risk_zone`：风险区。
- `obstacle`：障碍物。

`service_url` 当前为空，后续填入 iServer 服务地址。

## 3. risk_zones

风险区数据：

- `type`：`fire`、`landslide`、`no_fly` 等。
- `level`：1 到 5。
- `buffer_m`：安全缓冲距离。
- `polygon`：风险区边界。

## 4. obstacles

障碍物数据：

- `type`：`tower`、`building` 等。
- `position`：障碍物位置。
- `height_m`：高度。
- `buffer_m`：安全缓冲距离。

## 5. vision_images

视觉匹配输入图像清单：

- `id`：输入图像编号。
- `query_image`：图像路径或资源 URL。
- `capture_time_s`：仿真时间点。
- `resolution`：图像分辨率。
- `camera`：虚拟相机参数。
- `scene_tags`：场景标签。
- `expected_center`：预期匹配中心点。

## 6. vision_tile_index

视觉匹配候选瓦片索引：

- `tile_id`：瓦片编号。
- `center`：瓦片中心点。
- `bbox`：瓦片边界。
- `source`：瓦片来源。
- `feature_count`：预计算特征数量或占位指标。

## 7. vision_matches

视觉匹配预计算结果：

- `image_id`：输入图片编号。
- `provider`：结果来源，当前为 `precomputed_demo`。
- `algorithm_trace`：演示流程标签。
- `candidates`：候选瓦片列表。
- `confidence`：置信度。
- `matched_points`：匹配点数量。
- `inlier_ratio`：几何验证内点比例。
- `bbox`：候选区域边界。
- `center`：候选区域中心。
- `offset_m`：估计偏移。
- `status`：候选状态，包含 `best`、`candidate`、`rejected`。
- `reason`：候选解释原因。
