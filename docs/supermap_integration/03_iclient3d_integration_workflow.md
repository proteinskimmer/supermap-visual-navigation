# iClient3D for WebGL 接入步骤

## 1. 目标

将当前前端 mock 态势图逐步替换为 SuperMap iClient3D for WebGL 三维场景，同时保留 mock 视图作为备用。

## 2. 当前代码入口

真实三维接入集中在：

```text
frontend/src/components/SuperMapScene.vue
```

当前备用态势图在：

```text
frontend/src/components/MockMissionMap.vue
```

前端可通过环境变量切换：

```text
VITE_SCENE_PROVIDER=supermap
```

## 3. 接入原则

- 不直接在 `App.vue` 中堆 SuperMap 代码。
- 先加载三维场景，再叠加业务图层。
- 航线、风险区、视觉候选区域仍使用现有后端 API。
- 如果 SuperMap 加载失败，保留 mock 图展示主流程。
- 具体 API 名称和参数以本机安装版本的官方示例为准。

## 4. 前端接入步骤

### 步骤 1：确认资源引入方式

根据安装包或官方示例确认 iClient3D 的引入方式：

- npm 包方式。
- 本地静态 JS/CSS。
- 官方示例中的 Cesium/SuperMap 资源路径。

记录：

- JS 文件路径。
- CSS 文件路径。
- Cesium 资源路径。
- 是否需要 token 或许可。

### 步骤 2：填写服务配置

复制配置模板：

```powershell
Copy-Item config\supermap_services.example.json config\supermap_services.local.json
```

填写：

- `iserver.base_url`
- `services.scene.url`
- `services.map.url`
- `services.data.url`
- `layers.risk_zone.dataset`
- `layers.obstacle.dataset`

### 步骤 3：加载三维场景

在 `SuperMapScene.vue` 中：

1. 创建场景容器。
2. 初始化 Cesium/SuperMap Viewer。
3. 加载 iServer 三维服务。
4. 设置默认视角到任务区域。
5. 显示加载状态和错误状态。

注意：具体加载方法必须现场核对本机官方示例，例如 S3M/SCP 加载方式。

### 步骤 4：叠加任务图层

优先叠加：

1. 任务区域边界。
2. 风险区。
3. 障碍物。
4. 候选航线。
5. 动态重规划航线。
6. 视觉匹配候选区域。

业务数据来源仍来自：

```text
http://localhost:8000/api
```

### 步骤 5：联动仿真

将现有 `currentPoint` 映射为三维实体：

- 当前无人机位置。
- 航迹线。
- 视角跟随。
- 风险事件高亮。

先做位置点和航迹线，视角跟随后置。

## 5. 推荐接入顺序

| 顺序 | 功能 | 验收 |
|---|---|---|
| 1 | 显示空 Viewer | 页面无报错 |
| 2 | 加载三维服务 | 能看到任务区域 |
| 3 | 设置默认视角 | 打开页面自动定位 |
| 4 | 叠加风险区 | 与场景位置对齐 |
| 5 | 叠加航线 | 航线与风险区对齐 |
| 6 | 叠加动态重规划 | 新旧航线可区分 |
| 7 | 叠加视觉候选区 | 候选区域可高亮 |

## 6. 风险与回退

| 风险 | 回退方式 |
|---|---|
| SuperMap API 示例不匹配 | 优先查本机安装示例 |
| 三维服务加载失败 | 切回 mock provider |
| 坐标偏移 | 检查 iDesktopX 坐标系和前端 lon/lat 顺序 |
| 跨域失败 | 配置 iServer CORS 或 Vite 代理 |
| 性能差 | 缩小任务区域，减少图层 |

