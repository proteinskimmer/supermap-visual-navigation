# 3D-low_altitude_demo 门禁

更新时间：2026-06-09

## 当前状态

`3D-low_altitude_demo` 已发布并通过 REST 门禁。

当前 REST 检查地址：

```text
http://localhost:8090/iserver/services/3D-low_altitude_demo/rest/realspace/scenes.json
```

返回：

```text
HTTP 200
scene: low_altitude_demo
```

因此当前可以说：项目自建三维服务已完成接口级发布验收。

## 已确认的技术边界

- iObjectSpy 当前公开 Python API 可以自动完成二维工作空间、数据源、数据集、地图对象和地图预览渲染。
- 当前未发现 iObjectSpy Python API 中有直接创建/保存 iDesktopX 三维场景的高层接口。
- 已确认 iObjects Java API 可以通过 `Workspace.getScenes()`、`Scene.toXML()`、`Scenes.add(name, xml)` 脚本化写入三维场景。
- iServer 的 `UGCRealspaceProvider` 可以通过服务配置指向包含三维场景的工作空间并发布 REST Realspace 服务。
- 2026-06-09 已用 iObjects Java 在 `demo_workspace_3d_auto` 中自动生成 `low_altitude_demo` 三维场景，包含 8 个业务图层。
- iServer `3D-low_altitude_demo` 已指向该三维工作空间并发布成功。

## 自动化脚本

生成项目三维工作空间：

```powershell
powershell -ExecutionPolicy Bypass -File E:\supermap_project\scripts\build_low_altitude_3d_workspace.ps1 -Overwrite
```

输出：

```text
E:\supermap_project\supermap_file_root\demo_workspace_3d_auto\low_altitude_demo.smwu
E:\supermap_project\supermap_file_root\demo_workspace_3d_auto\build_3d_scene_summary.txt
```

生成 iServer 3D staged XML：

```powershell
powershell -ExecutionPolicy Bypass -File E:\supermap_project\scripts\stage_iserver_3d_low_altitude_config.ps1 -WorkspacePathInIServer '${fileManagerWorkDir}/demo_workspace_3d_auto/low_altitude_demo.smwu'
```

应用、重启并验收：

```powershell
powershell -ExecutionPolicy Bypass -File E:\supermap_project\scripts\apply_iserver_3d_low_altitude_config.ps1 -Apply -Restart
```

单独复核 3D 门禁：

```powershell
powershell -ExecutionPolicy Bypass -File E:\supermap_project\scripts\check_low_altitude_3d_gate.ps1
```

完整浏览器验收：

```powershell
powershell -ExecutionPolicy Bypass -File E:\supermap_project\scripts\run_supermap_browser_acceptance.ps1 -FrontendUrl http://localhost:5174 -FrontendPort 5174
```

## 当前证据

- `scripts\check_low_altitude_3d_gate.ps1` 已通过。
- `scripts\run_supermap_browser_acceptance.ps1` 已通过。
- 前端配置已切换到 `3D-low_altitude_demo`。
- 正式截图已保存：

```text
E:\supermap_project\docs\delivery\screenshots\frontend_supermap_workspace.png
E:\supermap_project\docs\delivery\screenshots\iserver_3d_low_altitude_demo_scenes.png
```

## GUI 兜底路线

如需更漂亮的三维视觉效果，可在 iDesktopX 中打开：

```text
E:\supermap_project\supermap_file_root\demo_workspace_3d_auto\low_altitude_demo.smwu
```

可微调场景样式、相机和图层高度后保存，再重新发布。

## 回滚

回滚最近备份并重启：

```powershell
powershell -ExecutionPolicy Bypass -File E:\supermap_project\scripts\apply_iserver_3d_low_altitude_config.ps1 -RollbackLatest -Apply -Restart
```

## 严格汇报口径

可以说：

```text
项目已通过 iObjects Java 自动生成项目三维场景，并发布 3D-low_altitude_demo，REST 门禁返回 HTTP 200。
```

不能说：

```text
项目三维场景已经完成精细建模或真实倾斜摄影级效果。
```
