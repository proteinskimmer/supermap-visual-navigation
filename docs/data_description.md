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

当前前端已提供 3 张可显示演示占位图：

- `frontend/public/demo/uav_view_001.jpg`
- `frontend/public/demo/uav_view_002.jpg`
- `frontend/public/demo/uav_view_003.jpg`

这些图片用于保证前端演示路径可访问，不代表真实航拍数据。后续如获得真实图片，可保持文件名不变直接替换。

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
## 2026-06-09 Luojia 自动视觉瓦片数据

当前 `vision_tile_index` 由 `scripts/generate_luojia_vision_tiles.py` 从真实珞珈山正射影像自动生成，不再手写固定 5 个瓦片。

生成输入：

- `data_sources/luojia_mountain/raw_test_data/珞珈山影像.tif`
- `data_sources/luojia_mountain/raw_test_data/珞珈山影像.tfw`

生成输出：

- `demo_data/generated/luojia_vision_tiles.json`
- `frontend/public/demo/vision_tiles/*.png`
- `demo_data/task_demo.json` 中的 `vision_tile_index`
- `demo_data/gis_export/vision_tile.geojson`

自动瓦片新增字段：

- `tile_image`：瓦片缩略图。
- `pixel_bbox`：源影像像素窗口。
- `grid`：瓦片行列号。
- `source_image`：源 TIFF 路径。
- `feature_count_method`：特征数量代理指标的来源。
- `preview_stats`：缩略图采样统计。
