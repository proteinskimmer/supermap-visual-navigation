# SuperMap 服务地址记录模板

本模板用于记录 iServer 发布结果。每次发布或变更服务地址后，都应更新本文件，并同步到 `config/supermap_services.local.json`。

## 1. 基础信息

| 项目 | 内容 |
|---|---|
| iServer 根地址 | `http://localhost:8090/iserver` |
| iServer 管理地址 | `http://localhost:8090/iserver/manager` |
| 工作空间路径 | 待填写 |
| 数据源名称 | `low_altitude_demo` |
| 坐标系 | 待填写 |
| 发布日期 | 待填写 |
| 发布负责人 | 待填写 |

## 2. 服务清单

| 服务类型 | 服务名称 | URL | 状态 | 前端接入 | 后端接入 | 备注 |
|---|---|---|---|---|---|---|
| 三维服务 | 待填写 | 待填写 | Todo | Todo | 不需要 | 前端 iClient3D 加载 |
| 地图服务 | 待填写 | 待填写 | Todo | Todo | 可选 | 备用底图 |
| 数据服务 | 待填写 | 待填写 | Todo | 可选 | Todo | 风险区、障碍物、任务区 |
| 空间分析服务 | 待填写 | 待填写 | Optional | 不需要 | Optional | 缓冲区/叠加分析 |

状态可选：

- `Todo`：未发布。
- `Published`：已发布但未验证。
- `Verified`：浏览器可访问。
- `Integrated`：已接入项目。
- `Failed`：发布失败。
- `Optional`：可选项。

## 3. 图层/数据集记录

| 数据集 | 服务来源 | 几何类型 | 字段 | 用途 | 验证状态 |
|---|---|---|---|---|---|
| `task_area` | 数据服务 | Polygon | `id,name` | 规划范围 | Todo |
| `risk_zone` | 数据服务 | Polygon | `id,name,type,level,buffer_m,active` | 风险校验和展示 | Todo |
| `obstacle` | 数据服务 | Point/Polygon | `id,name,type,height_m,buffer_m` | 障碍物校验 | Todo |
| `road` | 数据服务/地图服务 | LineString | 待填写 | 场景表达 | Todo |
| `water` | 数据服务/地图服务 | Polygon/LineString | 待填写 | 场景表达 | Todo |
| `building` | 数据服务/三维服务 | Polygon/Model | 待填写 | 场景表达/障碍 | Todo |

## 4. 验证记录

| 日期 | 服务/图层 | 验证方式 | 结果 | 问题 |
|---|---|---|---|---|
| 待填写 | 待填写 | 浏览器打开 URL | 待填写 | 待填写 |

## 5. 截图记录

| 截图 | 路径 | 用途 |
|---|---|---|
| iServer 管理页面 | 待填写 | 部署说明 |
| 三维服务发布成功 | 待填写 | PPT/答辩 |
| 前端加载三维场景 | 待填写 | 演示材料 |

