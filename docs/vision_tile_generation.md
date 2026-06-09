# 视觉瓦片自动生成说明

更新日期：2026-06-09

## 目的

当前主线是视觉自主导航。视觉瓦片不是辅助展示块，而是视觉定位的参考库单元：UAV 视觉帧经过候选检索和几何验证后，返回匹配瓦片、置信度和估计位置，并由后端导航状态机用于自主导航状态更新。

## 输入

- 正射影像：`data_sources/luojia_mountain/raw_test_data/珞珈山影像.tif`
- 地理参考：`data_sources/luojia_mountain/raw_test_data/珞珈山影像.tfw`
- 坐标系统：EPSG:4547，脚本内反算到 WGS84 经纬度。
- 默认任务：`demo_data/task_demo.json` 中的 `task_001`

## 生成流程

脚本：`scripts/generate_luojia_vision_tiles.py`

默认执行：

```powershell
& "E:\anaconda\envs\supermap_nav\python.exe" scripts\generate_luojia_vision_tiles.py --update-demo --update-matches
```

或使用包装脚本：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\generate_luojia_vision_tiles.ps1
```

流程如下：

1. 读取 TIFF 元数据，确认影像宽高、内部瓦片结构和调色板。
2. 读取 TFW，得到像素到 EPSG:4547 投影坐标的映射。
3. 按默认 `1024px` 目标尺寸生成 5x8 网格，共 40 个视觉参考瓦片。
4. 对每个瓦片计算投影范围、WGS84 `bbox`、`center` 和像素窗口 `pixel_bbox`。
5. 从真实 TIFF 像素采样生成 PNG 缩略图，输出到 `frontend/public/demo/vision_tiles/`。
6. 根据缩略图亮度方差和边缘强度生成 `feature_count` 代理指标。
7. 输出完整索引到 `demo_data/generated/luojia_vision_tiles.json`。
8. 使用 `--update-demo` 时替换 `demo_data/task_demo.json` 的 `vision_tile_index`。
9. 使用 `--update-matches` 时，将预计算匹配候选重新绑定到最近的自动瓦片。

## 输出字段

`vision_tile_index` 现在由脚本生成，核心字段仍兼容原接口：

- `tile_id`
- `task_id`
- `name`
- `center`
- `bbox`
- `source`
- `feature_count`

新增可追溯字段：

- `tile_image`：前端可访问的瓦片缩略图路径。
- `pixel_bbox`：瓦片在源 TIFF 中的像素窗口 `[x0, y0, x1, y1]`。
- `grid`：行列号与网格规模。
- `source_image`：源影像路径。
- `feature_count_method`：当前特征数量指标的生成方法。
- `preview_stats`：缩略图亮度和边缘统计。

## 当前边界

已经完成的是“从真实正射影像自动生成视觉参考瓦片库”。当前还没有接入真实 DINOv2、LoFTR、LightGlue 或 OpenCV RANSAC 在线推理；`vision_matches` 仍是预计算演示结果，但候选瓦片已经绑定到自动生成的真实影像瓦片索引。
