# 珞珈山三维场景数据包

整理日期：2026-06-09

## 来源目录

本目录为项目内整理副本，原始文件来自：

- `D:\prote\desktop\GIS_intern\GIS_intern\2026302131026xzh\题目4_三维场景`
- `D:\prote\desktop\GIS_intern\GIS_intern\2026GISTestData\4三维场景`

项目内副本：

```text
data_sources/luojia_mountain/
  raw_student_output/
  raw_test_data/
```

共 46 个文件，约 69.7 MB。整理过程只复制文件，不修改 D 盘原始数据。

## 坐标系统

主要矢量和栅格数据使用：

```text
CGCS2000 / 3-degree Gauss-Kruger CM 114E
EPSG:4547
单位：米
```

部分 `.prj` 中地理基准写法可能显示为 WGS84/CGCS2000 混合命名，但投影参数一致：

- Central Meridian: 114E
- False Easting: 500000
- Latitude of Origin: 0
- Unit: Meter

导入 SuperMap 时应统一检查并保持该投影坐标系。

## 推荐使用文件

| 类型 | 推荐文件 | 用途 | 备注 |
|---|---|---|---|
| 正射影像/遥感底图 | `raw_test_data/珞珈山影像.tif` | 三维场景贴图、视觉匹配参考底图 | 0.2 m 像元，单波段 uint8 |
| DEM | `raw_student_output/珞珈山DEM.tif` | 地形、高程剖面、安全高度约束 | float32，约 6.12 m 像元 |
| 地形点 | `raw_student_output/区域地形点.shp` | DEM/TIN 备份、高程点展示 | PointZ，139193 个点 |
| 建筑面/高度 | `raw_student_output/珞珈山周边建筑3D.shp` | 三维建筑拉伸 | 169 个建筑面，含 `HEIGHT_M` 字段 |
| 原始建筑面 | `raw_test_data/珞珈山周边建筑.shp` | 建筑面备份 | 字段较少，不优先 |
| ArcGIS TIN | `raw_student_output/珞珈山TIN/` | 高程备份 | ArcGIS TIN 格式，不作为 SuperMap 主链路优先输入 |
| 原始地形点 CSV | `raw_test_data/区域地形点.csv` | 地形点备份 | 如需重新生成点/DEM 可使用 |

## 已盘点元数据

### 正射影像

```text
file: raw_test_data/珞珈山影像.tif
size: 7701 x 4201
bands: 1
dtype: uint8
pixel size: 0.2 m
bounds: 534169.851, 3379309.826, 535710.051, 3380150.026
crs: EPSG:4547
```

### DEM

```text
file: raw_student_output/珞珈山DEM.tif
size: 249 x 127
bands: 1
dtype: float32
pixel size: 6.118956 m
bounds: 534175.630, 3379341.750, 535699.250, 3380118.857
elevation: 5.766 m - 104.810 m
```

### 地形点

```text
file: raw_student_output/区域地形点.shp
shape type: PointZ
features: 139193
bounds: 534175.630, 3379341.750, 535699.250, 3380120.750
z range: 5.75 m - 104.96 m
fields: X, Y, Z
```

### 建筑面

```text
file: raw_student_output/珞珈山周边建筑3D.shp
shape type: Polygon
features: 169
bounds: 534206.387, 3379346.931, 535671.289, 3380085.093
important field: HEIGHT_M
```

部分中文字段名在 DBF 编码中可能显示乱码，不影响 `HEIGHT_M` 使用。导入 SuperMap 后建议手动或脚本重命名重要图层，而不是依赖原始中文字段名。

## 在项目中的定位

这批数据适合作为项目的真实/半真实三维场景底座，用来替换当前演示级建筑体块和占位底图。

它能够支持：

- SuperMap iDesktopX 制作珞珈山三维场景。
- iServer 发布项目自建 `3D-luojia_mountain_demo` 服务。
- iClient3D 加载真实地形/影像/建筑拉伸效果。
- 视觉自主导航演示中的参考底图和空间验证环境。

它暂时不能单独完成：

- UAV 实时影像输入。
- 真实视觉匹配模型推理。
- 相机姿态、时间戳、飞行轨迹真值。

这些仍需视觉组补充 UAV 视角图像或视频帧。
