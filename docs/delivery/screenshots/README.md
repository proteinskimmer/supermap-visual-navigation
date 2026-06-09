# 截图验收说明

本目录保存当前阶段的 SuperMap、iServer、iClient3D 和项目工作台截图证据。截图原始文件名暂时保留为 QQ 时间戳，后续制作 PPT 或提交包时建议复制并重命名为可读文件名。

## 已有截图

### 正式命名截图

| 文件 | 验收内容 | 当前结论 |
|---|---|---|
| `frontend_supermap_workspace.png` | 项目工作台读取项目自建 scene/map/data 服务，SuperMap Services 面板显示三项 `verified`，8 个业务图层 verified，业务航线、风险区和视觉瓦片已叠加 | 可作为项目服务配置和业务叠加证据；该截图中的无头浏览器 WebGL2 回退不等同于真实三维渲染证据 |
| `iserver_services_list.png` | iServer 公共服务列表页可访问，可见已发布服务目录 | 可作为无登录态下的服务发布目录证据 |
| `iserver_map_low_altitude_demo_map.png` | `map-low_altitude_demo` 地图服务页面可访问 | 可作为项目自建地图服务 REST 页面证据 |
| `iserver_map_low_altitude_demo_map_json.png` | `low_altitude_demo_map.json` 可访问并返回地图元数据 | 可作为项目地图对象元数据证据 |
| `iserver_data_low_altitude_demo_datasets.png` | `data-low_altitude_demo` 数据服务返回项目数据集列表 | 可作为 8 个业务数据集发布证据 |
| `iserver_3d_low_altitude_demo_scenes.png` | 项目自建 `3D-low_altitude_demo` scenes JSON 可访问并包含 `low_altitude_demo` | 可作为项目自建三维服务 REST 证据 |
| `iserver_3d_cbd_scenes.png` | 官方样例 `3D-CBD` scenes JSON 可访问 | 作为早期三维链路证据保留；当前项目自建 3D 已由脚本门禁验证 |
| `low_altitude_demo_map_iobjectspy_preview.png` | iObjectSpy 渲染项目地图预览，显示项目面、线、点、瓦片等图层 | 可作为项目地图图层显示的脚本化证据 |
| `iserver_publish_services_admin_attempt.png` | iServer 管理入口截图 | 只可证明管理入口可访问，不能作为发布成功证据 |

### 原始时间戳截图

| 文件 | 验收内容 | 当前结论 |
|---|---|---|
| `QQ20260609-023149.png` | 项目工作台加载 SuperMap 场景，显示任务、候选航线、风险校验、高程剖面和业务图形叠加 | 可作为前端 SuperMap 工作台运行证据 |
| `QQ20260609-023246.png` | `supermap-minimal.html` 加载 iClient3D SDK，WebGL2 可用，Viewer 创建成功，`scene.open(sceneUrl)` 成功并显示 `3D-CBD` | 可作为 iClient3D 最小验证证据 |
| `QQ20260609-023408.png` | iServer `3D-CBD` 三维服务根节点页面，包含 `datas`、`scenes`、`symbols` 子资源 | 可作为三维服务 REST 根节点证据 |
| `QQ20260609-023420.png` | iServer 初始化向导完成页，显示首页和服务管理器入口 | 可作为 iServer 初始化完成证据 |
| `QQ20260609-023456.png` | iServer 系统环境检查页，Objects Java 和 JRE 检查通过，JVM 配置有建议项 | 可作为运行环境检查证据，JVM 配置建议后续可优化 |
| `QQ20260609-023530.png` | iDesktopX 2025 打开 `CBD` 三维场景，建筑、道路和地形可见 | 可作为 iDesktopX 三维样例场景证据 |
| `QQ20260609-023547.png` | iDesktopX 2025 主界面，左侧已加载 `CBD` 工作空间和数据源 | 可作为 iDesktopX 主界面/工作空间证据 |

## 仍需补齐

- 项目自建 `3D-low_altitude_demo` 在真实浏览器 WebGL2 环境中的最终渲染截图。
- 前端完整演示流程截图：规划、仿真、临时风险区、重规划、视觉匹配、报告。
- 若截图脚本仍使用无头浏览器，需明确标注 WebGL2 回退，不得冒充真实三维渲染。

## 建议重命名

后续制作提交包时，建议把当前截图复制到提交目录并重命名，例如：

```text
01_iserver_initialization_complete.png
02_iserver_3d_cbd_rest_root.png
03_iclient3d_minimal_scene_open_success.png
04_project_workbench_supermap_overlay.png
05_idesktopx_cbd_workspace.png
06_idesktopx_cbd_3d_scene.png
```
