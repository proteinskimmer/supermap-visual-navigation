# iServer 发布自动化路线

更新时间：2026-06-09

## 当前结论

项目已经完成 `map-low_altitude_demo` 与 `data-low_altitude_demo` 的人工发布和 REST 验收。下一步自动化目标是把发布过程压缩为可复用脚本。

稳定路线分两级：

1. 优先路线：继续寻找并封装 iServer 管理 REST/Admin API。
2. 兜底路线：生成可审计的 `iserver-services.xml` 服务配置片段，由人工或受控脚本合并到 iServer 配置，再重启 iServer 并运行 REST 验收。

当前不直接修改 iServer 安装目录，避免破坏已经验收通过的服务。

## 已验证的发布配置结构

当前已发布服务在 iServer 配置中对应：

```text
E:\supermap_software\supermap-iserver-2025u1a-windows-x64-all\webapps\iserver\WEB-INF\iserver-services.xml
```

已确认的核心元素：

```text
component: map-low_altitude_demo
component class: com.supermap.services.components.impl.MapImpl
provider: map-low_altitude_demo
provider class: com.supermap.services.providers.UGCMapProvider

component: data-low_altitude_demo
component class: com.supermap.services.components.impl.DataImpl
provider: data-low_altitude_demo
provider class: com.supermap.services.providers.UGCDataProvider
```

两类 provider 都指向同一个项目工作空间：

```text
${fileManagerWorkDir}/demo_workspace/low_altitude_demo.smwu
```

## 新增脚本

一键执行当前 map/data 自动化流水线：

```powershell
powershell -ExecutionPolicy Bypass -File E:\supermap_project\scripts\run_low_altitude_map_data_pipeline.ps1 -OverwriteAutoWorkspace
```

该脚本串起：

```text
导出 GeoJSON -> iObjectSpy 生成 demo_workspace_auto 工作空间 -> 生成 iServer 配置片段 -> 渲染项目地图预览 -> 验收 map/data/3D-CBD REST 门禁
```

默认不会覆盖已经发布的正式工作空间：

```text
E:\supermap_project\supermap_file_root\demo_workspace\low_altitude_demo.smwu
```

生成 iServer 服务配置片段：

```powershell
powershell -ExecutionPolicy Bypass -File E:\supermap_project\scripts\export_iserver_low_altitude_service_config.ps1
```

输出目录：

```text
E:\supermap_project\docs\supermap_integration\generated
```

主要输出：

```text
low_altitude_demo_map_data_iserver_services_fragment.xml
low_altitude_demo_iserver_services_draft.xml
low_altitude_demo_iserver_config_summary.json
```

如果需要生成未验收的三维服务候选片段：

```powershell
powershell -ExecutionPolicy Bypass -File E:\supermap_project\scripts\export_iserver_low_altitude_service_config.ps1 -IncludeUnverified3D
```

注意：`3D-low_altitude_demo` 片段只表示候选配置，不代表服务已发布或可用。

## 自动化边界

可以自动化：

- 生成 iServer map/data 服务配置片段。
- 校验 XML 格式是否良好。
- 记录 map/data/3D 候选服务名称。
- 发布后运行 REST 验收：
  - `map-low_altitude_demo/rest/maps.json`
  - `map-low_altitude_demo/rest/maps/low_altitude_demo_map.json`
  - `map-low_altitude_demo/rest/maps/low_altitude_demo_map/layers.json`
  - `data-low_altitude_demo/rest/data/datasources/low_altitude_demo/datasets.json`
- 使用 iObjectSpy 渲染 `low_altitude_demo_map` 地图预览：

```powershell
powershell -ExecutionPolicy Bypass -File E:\supermap_project\scripts\render_low_altitude_map_preview.ps1
```

暂不自动直接执行：

- 覆盖 iServer 的 `WEB-INF/iserver-services.xml`。
- 自动重启 iServer。
- 宣称 `3D-low_altitude_demo` 已可用。

## 当前 3D 门禁状态

`3D-low_altitude_demo` 已完成当前脚本门禁验证：

```powershell
powershell -ExecutionPolicy Bypass -File E:\supermap_project\scripts\check_low_altitude_3d_gate.ps1
```

当前 REST 可访问：

```text
http://localhost:8090/iserver/services/3D-low_altitude_demo/rest/realspace/scenes.json
```

当前仍需补齐的是浏览器截图证据：

1. 打开项目工作台。
2. 确认服务面板中 scene 指向 `3D-low_altitude_demo`。
3. 确认页面可加载并叠加业务图形。
4. 保存截图到 `docs/delivery/screenshots/` 并更新截图证据注册表。

## 严格汇报口径

可以说：

```text
项目已形成 iServer 发布自动化预案：map/data 服务配置可由脚本生成，发布后由 REST 脚本验收。
```

不能说：

```text
iServer 发布已完全无 GUI 自动化。
```

当前准确状态：

```text
scene/map/data 已发布并通过脚本门禁；发布自动化路线已收敛到 Admin API 优先、XML 配置兜底；最终材料仍需补齐浏览器截图、PPT 和视频。
```

下一门禁详见：

```text
docs/supermap_integration/12_3d_low_altitude_demo_gate.md
```
