# Screenshot Evidence Registry

更新时间：2026-06-09

## 已保存的正式截图

目录：

```text
E:\supermap_project\docs\delivery\screenshots
```

当前可用证据：

| 文件 | 证明内容 | 结论 |
| --- | --- | --- |
| `frontend_supermap_workspace.png` | 前端工作台可打开，后端接口已连接，业务航线、风险区、视觉瓦片叠加，SuperMap Services 显示 scene/map/data runtime verified 和 8 business layers verified | 可作为前端工作台与真实 map/data 状态验收截图；无头浏览器 WebGL 回退不等同于真实三维渲染证据 |
| `iserver_services_list.png` | iServer 公共服务列表页可访问，用于证明已发布服务在服务目录中注册 | 可作为无登录态下的 iServer 发布成功替代证据 |
| `iserver_publish_success_admin.png` | iServer 已登录后台/发布管理页面截图，由用户在真实交互桌面补证 | 可作为 iServer 发布/管理 GUI 原始证据 |
| `iserver_map_low_altitude_demo_map.png` | `map-low_altitude_demo` 地图服务页面可访问 | 可作为地图服务 REST 页面证据 |
| `iserver_map_low_altitude_demo_map_json.png` | `low_altitude_demo_map.json` 可访问，包含地图元数据 | 可作为地图对象元数据证据 |
| `iserver_data_low_altitude_demo_datasets.png` | `data-low_altitude_demo` 数据集列表 JSON 可访问 | 可作为 8 个业务数据集服务证据 |
| `iserver_3d_low_altitude_demo_scenes.png` | 项目自建 `3D-low_altitude_demo` scenes JSON 可访问，包含 `low_altitude_demo` | 可作为项目自建三维服务 REST 证据 |
| `iserver_3d_cbd_scenes.png` | 官方样例 `3D-CBD` scenes JSON 可访问 | 作为早期三维链路证据保留；当前项目自建 `3D-low_altitude_demo` 已另由脚本门禁验证 |
| `low_altitude_demo_map_iobjectspy_preview.png` | iObjectSpy 从正式工作空间渲染 `low_altitude_demo_map`，可见项目面、线、点、瓦片等图层 | 可作为项目地图图层显示的脚本化证据 |
| `idesktopx_low_altitude_demo_map_layers.png` | iDesktopX 打开的 `low_altitude_demo_map` 项目地图 GUI 截图，由用户在真实交互桌面补证 | 可作为 iDesktopX 项目地图图层显示原始证据 |
| `QQ20260609-023420.png` | iServer 初始化完成页 | 可作为 iServer 环境初始化完成证据 |
| `QQ20260609-023530.png` | iDesktopX 打开官方 CBD 三维场景 | 只能证明 iDesktopX 官方样例三维显示能力 |
| `QQ20260609-023547.png` | iDesktopX 主界面与官方 CBD 工作空间 | 只能证明 iDesktopX 可运行和官方样例工作空间 |

## 兼容性截图

目录：

```text
E:\supermap_project\docs\delivery\screenshots\compat_cbd
```

该目录用于证明前端仍可通过 `VITE_SUPERMAP_SCENE_URL` 覆盖为官方 `3D-CBD` 服务。当前主验收截图仍以项目自建 `3D-low_altitude_demo` 为准，`compat_cbd/frontend_supermap_workspace.png` 只作为 CBD 备用底座兼容证据。

## 需要严格标注的截图

| 文件 | 当前问题 | 处理方式 |
| --- | --- | --- |
| `iserver_publish_services_admin_attempt.png` | 自动截图命中 iServer 登录页，不是发布成功页 | 只能作为管理入口可访问证据；不能作为发布成功证据 |

## 仍缺的截图

| 需求 | 当前状态 | 建议 |
| --- | --- | --- |
| 更精细的 iDesktopX 三维场景 GUI 效果图 | 当前已有 REST 与前端工作台证据，但不是精细建模展示 | 如 PPT 需要视觉冲击，可在 iDesktopX 中微调 `demo_workspace_3d_auto` 后补图 |

## 自动截图脚本

已新增完整验收脚本：

```powershell
powershell -ExecutionPolicy Bypass -File E:\supermap_project\scripts\run_supermap_browser_acceptance.ps1
```

该脚本会临时启动后端、检查前端与 iServer、执行 REST 交付门禁，并调用无头 Chrome 保存截图。

## 交互式 GUI 取证脚本

Codex 当前运行上下文无法直接捕获真实桌面 GUI，会得到黑屏截图。需要用户在普通 PowerShell 中运行：

```powershell
powershell -ExecutionPolicy Bypass -File E:\supermap_project\scripts\capture_interactive_gui_evidence.ps1 -Name iserver_publish_success_admin.png
powershell -ExecutionPolicy Bypass -File E:\supermap_project\scripts\capture_interactive_gui_evidence.ps1 -Name idesktopx_low_altitude_demo_map_layers.png
```

运行前分别把以下窗口置于前台：

1. iServer 已登录后台的服务发布/服务管理成功页面。
2. iDesktopX 打开的 `low_altitude_demo_map` 地图窗口，左侧或图层树可见 8 个业务图层。

为减少查找路径，可先运行：

```powershell
powershell -ExecutionPolicy Bypass -File E:\supermap_project\scripts\open_supermap_gui_evidence_targets.ps1
```

## 严格汇报口径

可以说：

```text
项目已有前端工作台、iServer map/data REST、项目自建 3D-low_altitude_demo REST、iObjectSpy 项目地图预览等截图证据；scene/map/data 服务已通过脚本门禁验收。
```

不能说：

```text
项目三维场景已经完成精细建模或真实倾斜摄影级效果。
```
