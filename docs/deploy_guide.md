# 部署与启动说明

本文档用于当前 mock 阶段。SuperMap 软件安装完成后，只需要补充 iServer 服务地址和前端三维场景接入。

## 1. 环境要求

- Windows 10/11。
- Anaconda，当前检测到路径为 `E:\anaconda`。
- Node.js，当前已检测到 `v24.16.0`。
- npm，当前已检测到 `11.13.0`。

后端建议使用独立 Conda 环境，不使用 base，也不污染系统 Python。

## 2. 创建后端环境

```powershell
cd E:\supermap_project
& 'E:\anaconda\Scripts\conda.exe' env create -f environment.yml
```

如果环境已存在，更新环境：

```powershell
& 'E:\anaconda\Scripts\conda.exe' env update -n supermap_nav -f environment.yml
```

## 3. 安装前端依赖

```powershell
cd E:\supermap_project\frontend
npm install
```

依赖只会安装到 `frontend\node_modules`。

## 4. 启动后端

最推荐使用一键启动脚本。它会检查 iServer，后台启动后端和前端，并自动打开浏览器：

```powershell
cd E:\supermap_project
.\scripts\start_demo_one_click.ps1
```

也可以直接双击项目根目录下的：

```text
START_DEMO.bat
```

停止后端和前端：

```powershell
.\scripts\stop_demo_one_click.ps1
```

也可以双击：

```text
STOP_DEMO.bat
```

下面是拆分启动方式，调试时使用。

```powershell
cd E:\supermap_project
.\scripts\start_backend.ps1
```

`start_backend.ps1` 会优先使用 `supermap_nav` 环境中的 `python.exe` 直接运行 uvicorn，Conda wrapper 只作为兜底。

默认地址：

```text
http://localhost:8000/api/health
```

## 5. 启动前端

```powershell
cd E:\supermap_project
.\scripts\start_frontend.ps1
```

默认地址：

```text
http://localhost:5173
```

如果要直接使用本机 iServer `3D-CBD` 三维服务启动 SuperMap 模式：

```powershell
cd E:\supermap_project
.\scripts\start_frontend_supermap_cbd.ps1
```

## 6. SuperMap 接入位置

当前前端中间区域默认是 mock SVG 态势图。后续接入 SuperMap 时，优先替换独立场景组件：

```text
frontend/src/components/SuperMapScene.vue
```

当前组件边界：

```text
frontend/src/components/MockMissionMap.vue    # 稳定 mock 演示备用图
frontend/src/components/SuperMapScene.vue     # iClient3D / Cesium 接入点
```

后端 iServer 服务配置建议放入：

```text
backend/app/core/config.py
demo_data/task_demo.json 的 layers[].service_url
```

完整接入预案见：

```text
docs/supermap_integration/README.md
```

服务地址配置模板：

```text
config/supermap_services.example.json
```

正式联调时复制为：

```powershell
Copy-Item config\supermap_services.example.json config\supermap_services.local.json
```

如果要从官方 `3D-CBD` 样例切换到项目自建 demo 服务，使用项目模板：

```powershell
Copy-Item config\supermap_services.low_altitude_demo.example.json config\supermap_services.local.json
```

然后根据 iServer 实际发布结果修正 `scene.url`、`map.url`、`data.url` 和 `workspace_path`。

后端可读取：

```text
GET /api/supermap/config
GET /api/supermap/services
```

如果要在前端切到 SuperMap 接入占位模式，可设置环境变量：

```powershell
$env:VITE_SCENE_PROVIDER='supermap'
.\scripts\start_frontend.ps1
```

当 `layers[].service_url` 为空时，页面仍会保留 mock 态势图，避免演示链路被 SuperMap 环境阻塞。

## 7. 验证命令

当前推荐先运行综合 runtime 检查。它不依赖 iServer，会覆盖 demo GeoJSON 导出和解析、iClient3D 静态资源、最小验证页关键标记、前端语法和构建、后端 pytest、增强 smoke：

```powershell
.\scripts\check_project_runtime.ps1
```

不启动服务也可以做轻量后端检查：

```powershell
.\scripts\check_backend_smoke.ps1
```

安装后端依赖后，可运行增强版 smoke，检查 JSON、Python 语法、服务层和 FastAPI 接口契约：

```powershell
.\scripts\check_backend_smoke_full.ps1
```

如果使用 Conda 环境：

```powershell
.\scripts\check_backend_smoke_full.ps1 -PythonExe 'E:\anaconda\Scripts\conda.exe' -PythonArgs @('run','-n','supermap_nav','python')
```

也可以运行 mock API 单元测试：

```powershell
cd E:\supermap_project\backend
pytest
```

## 8. iClient3D 最小验证

准备 SDK 静态资源：

```powershell
cd E:\supermap_project
.\scripts\prepare_iclient3d_public.ps1
```

启动前端：

```powershell
.\scripts\start_frontend.ps1
```

打开最小验证页：

```text
http://localhost:5173/supermap-minimal.html
```

项目工作台启用 iClient3D 承载层：

```powershell
$env:VITE_SCENE_PROVIDER='supermap'
$env:VITE_SUPERMAP_SDK_BASE='/vendor/supermap3d/Build/SuperMap3D'
.\scripts\start_frontend.ps1
```

本机 `3D-CBD` 场景服务已确认：

```text
http://localhost:8090/iserver/services/3D-CBD/rest/realspace
```

最小验证页：

```text
http://localhost:5173/supermap-minimal.html?sceneUrl=http%3A%2F%2Flocalhost%3A8090%2Fiserver%2Fservices%2F3D-CBD%2Frest%2Frealspace
```

当前 Codex 桌面线程中，隐藏后台方式启动 dev server 会很快退出；验收截图时请使用普通 PowerShell 窗口分别运行后端和前端启动脚本，并保持窗口打开。

## 9. 项目自建 demo 服务发布前检查

官方 `3D-CBD` 只用于证明 SuperMap 链路可跑通。发布项目自建服务前，先检查 demo GeoJSON、目标工作空间路径和目标配置模板：

```powershell
.\scripts\check_low_altitude_demo_publish_ready.ps1
```

当脚本提示 `low_altitude_demo.smwu` 缺失时，说明还需要在 iDesktopX 中导入 `demo_data\gis_export` 并保存工作空间。

## 10. 手动启动后端备用命令

```powershell
cd E:\supermap_project\backend
& 'E:\anaconda\envs\supermap_nav\python.exe' -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
