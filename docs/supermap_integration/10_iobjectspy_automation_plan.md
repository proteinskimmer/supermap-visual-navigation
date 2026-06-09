# SuperMap 自动化接口路线

更新时间：2026-06-09

## 结论

SuperMap 有类似 ArcPy 的自动化路线。当前项目优先使用 iDesktopX 2025 自带的 Python 环境和 iObjectSpy 包，把重复的 GIS 数据导入、工作空间生成、地图对象创建和验收检查脚本化。

严格口径：

- iObjectSpy 可以替代大量 iDesktopX GUI 操作。
- iServer 发布后的服务验收可以用 REST 脚本完成。
- iClient3D 前端接入使用 JavaScript SDK。
- 项目自建三维场景 `3D-low_altitude_demo` 已通过 Java iObjects / iServer XML 路线完成最小场景发布与 REST 验收；精细三维效果仍需后续素材或 GUI 调整。

## 本机已确认的接口

### 1. iObjectSpy Python

本机路径：

```text
E:\supermap_software\SuperMap iDesktopX 2025\support\python\python.exe
E:\supermap_software\SuperMap iDesktopX 2025\bin_python\iobjectspy\iobjectspy-py38_64
```

已验证能力：

- 读取 `demo_data/gis_export/*.geojson`
- 创建 `.smwu` 工作空间
- 创建 `.udbx` 数据源
- 导入 GeoJSON 为 SuperMap 数据集
- 创建地图对象 `low_altitude_demo_map`
- 保存工作空间
- 输出构建摘要 `build_summary.json`

当前脚本：

```powershell
powershell -ExecutionPolicy Bypass -File E:\supermap_project\scripts\build_low_altitude_workspace.ps1 -Overwrite
```

当前输出目标：

```text
E:\supermap_project\supermap_file_root\demo_workspace_auto\low_altitude_demo.smwu
E:\supermap_project\supermap_file_root\demo_workspace_auto\low_altitude_demo.udbx
E:\supermap_project\supermap_file_root\demo_workspace_auto\build_summary.json
```

注意事项：

- 脚本需要从 iDesktopX 安装根目录启动，因为 iObjectSpy 依赖相对路径下的 `bin`、`jre` 等运行库。
- 运行时出现 `numpy` 相关 warning 不影响当前 GIS 工作空间构建；该 warning 主要影响机器学习扩展能力。
- 自动生成目录使用 `demo_workspace_auto`，避免覆盖当前已人工发布并验收的 `demo_workspace`。

### 2. iServer REST

适用范围：

- 验证服务是否存在
- 验证 map/data/3D REST 地址是否可访问
- 检查地图列表、地图元数据、图层列表
- 检查数据源和数据集列表
- 作为前端 `/api/supermap/config` 的真实服务来源

当前已验收的项目服务：

```text
map-low_altitude_demo
data-low_altitude_demo
```

早期作为官方样例底座的服务：

```text
3D-CBD
```

当前已完成 REST 门禁的项目自建三维服务：

```text
3D-low_altitude_demo
```

### 3. iClient3D JavaScript SDK

适用范围：

- 浏览器加载三维场景
- 调用 `scene.open(sceneUrl)`
- 在三维场景上叠加航线、风险区、候选区、无人机当前位置等业务实体

当前状态：

- iClient3D SDK 包已验收。
- 前端承载层已实现。
- 项目自建 map/data 状态已能在前端展示。
- 当前前端配置已指向项目自建 `3D-low_altitude_demo`；官方 `3D-CBD` 仅作为早期链路验证证据保留。

## 可以脚本化的事项

| 事项 | 自动化状态 | 负责人建议 |
| --- | --- | --- |
| 导出 demo GeoJSON | 已脚本化 | Codex |
| 校验 GeoJSON 格式 | 已脚本化 | Codex |
| 创建项目工作空间 `.smwu` | 已脚本化 | Codex |
| 创建项目数据源 `.udbx` | 已脚本化 | Codex |
| 导入 GeoJSON 数据集 | 已脚本化 | Codex |
| 创建二维地图对象 | 已脚本化 | Codex |
| 验证 map/data REST 服务 | 已脚本化 | Codex |
| 前端读取 SuperMap 配置 | 已实现 | Codex |
| 浏览器截图验收 | 已脚本化，真实 WebGL 渲染截图仍建议人工补充 | Codex + 用户 |
| iServer map/data 服务发布 | 已通过现有服务与 REST 门禁验收；新增/替换发布仍保留 Admin/API/XML 路线 | Codex |
| 项目最小三维场景制作 | 已用 Java iObjects 路线完成 | Codex |
| 项目三维精细效果制作 | 待真实素材或 GUI 调整 | 用户 + Codex |

## 暂时仍可能需要 GUI 的事项

1. iServer 首次管理员初始化、登录、许可确认。
2. iServer 新增/替换服务时，如 REST/Admin API 尚未稳定封装，仍由 GUI 或 XML 兜底。
3. iDesktopX 中三维场景的可视化编辑、图层样式微调、场景截图确认。
4. 项目自建 `3D-low_altitude_demo` 的最终视觉效果确认。

## 下一步自动化攻关

优先级从高到低：

1. 把 `demo_workspace_auto` 发布为 iServer 服务的流程继续压缩，研究是否可通过 iServer 管理 REST API 稳定新增/替换发布。
2. 生成 iServer map/data 服务配置片段，作为 Admin API 暂不稳定时的可审计兜底路线。
3. 增加脚本参数，允许在确认后把自动工作空间输出到正式目录 `supermap_file_root/demo_workspace/`。
4. 增加自动验收脚本，对比正式工作空间和自动工作空间的数据集、地图名、图层数量和 bounds。
5. 在真实素材到位后，扩展 Java iObjects 三维场景生成脚本，加入更丰富的三维图层、样式和相机视角。

已新增 iServer 发布自动化路线文档：

```text
docs/supermap_integration/11_iserver_publish_automation_route.md
```

## 对外汇报口径

可以说：

```text
项目已接入 SuperMap 自动化接口路线，使用 iObjectSpy 完成项目 GIS 数据导入、工作空间生成和地图对象创建；使用 Java iObjects 生成最小项目三维场景；使用 iServer REST 完成 scene/map/data 服务级验收；前端通过 iClient3D 读取项目自建 scene 服务并叠加业务图层。
```

不能说：

```text
项目自建三维服务已经达到精细建模或真实倾斜摄影级效果。
```

当前准确状态：

```text
项目自建 scene/map/data 服务均已通过 REST 门禁；当前 3D-low_altitude_demo 是最小项目场景，后续仍需真实三维素材和最终渲染截图。
```
