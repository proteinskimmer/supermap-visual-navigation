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

```powershell
cd E:\supermap_project
.\scripts\start_backend.ps1
```

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

不启动服务也可以做轻量后端检查：

```powershell
.\scripts\check_backend_smoke.ps1
```

安装后端依赖后，可运行增强版 smoke，检查 JSON、Python 语法、服务层和 FastAPI 接口契约：

```powershell
.\scripts\check_backend_smoke_full.ps1
```

也可以运行 mock API 单元测试：

```powershell
cd E:\supermap_project\backend
pytest
```

## 8. 手动启动后端备用命令

```powershell
cd E:\supermap_project\backend
& 'E:\anaconda\Scripts\conda.exe' run -n supermap_nav fastapi dev app\main.py --port 8000
```
