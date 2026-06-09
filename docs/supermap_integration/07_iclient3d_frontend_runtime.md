# iClient3D 前端承载层使用说明

本文记录当前工程中 iClient3D 前端承载层的使用方式、可替换接口、最小验证页和排错表。

## 1. 当前实现位置

| 文件 | 用途 |
|---|---|
| `frontend/src/components/SuperMapScene.vue` | Vue 场景承载组件，负责 SDK 加载、Viewer 初始化、销毁、`scene.open(sceneUrl)` 和 mock 数据三维绘制 |
| `frontend/src/services/supermap3d.js` | 非响应式 iClient3D 工具层，负责动态加载 SDK、WebGL2 检测、Viewer 创建、实体绘制、相机定位 |
| `frontend/public/supermap-minimal.html` | 不依赖 Vue/后端/iServer 的最小验证页 |
| `scripts/prepare_iclient3d_public.ps1` | 将本机 iClient3D SDK 必需资源复制到前端静态目录 |
| `scripts/start_frontend_supermap_cbd.ps1` | 使用本机 `3D-CBD` 场景服务启动前端 SuperMap 模式 |

默认情况下，工作台仍使用 mock SVG。设置环境变量后才启用 iClient3D：

```powershell
$env:VITE_SCENE_PROVIDER='supermap'
$env:VITE_SUPERMAP_SDK_BASE='/vendor/supermap3d/Build/SuperMap3D'
.\scripts\start_frontend.ps1
```

本机 `3D-CBD` 已确认后，可直接使用：

```powershell
.\scripts\start_frontend_supermap_cbd.ps1
```

## 2. SDK 准备

默认本机 SDK 路径：

```text
E:\supermap_software\supermap-iclient3d-for-webgl_webgpu-2025u1
```

准备前端静态资源：

```powershell
.\scripts\prepare_iclient3d_public.ps1
```

脚本会复制：

- `Build/SuperMap3D/SuperMap3D.js`
- `Build/SuperMap3D/Widgets/`
- `Build/SuperMap3D/Workers/`
- `Build/SuperMap3D/Assets/`
- `Build/SuperMap3D/ThirdParty/`

复制目标：

```text
frontend/public/vendor/supermap3d/
```

该目录已加入 `.gitignore`，避免把大体积 SDK 资源直接提交。

## 3. 最小验证页

启动前端后打开：

```text
http://localhost:5173/supermap-minimal.html
```

可选参数：

```text
http://localhost:5173/supermap-minimal.html?sdkBase=/vendor/supermap3d/Build/SuperMap3D&contextType=2
```

如果已有 iServer 三维场景 URL：

```text
http://localhost:5173/supermap-minimal.html?sceneUrl=http://localhost:8090/iserver/services/3D-xxx/rest/realspace
```

本机已确认的 `3D-CBD` 最小验证地址：

```text
http://localhost:5173/supermap-minimal.html?sceneUrl=http%3A%2F%2Flocalhost%3A8090%2Fiserver%2Fservices%2F3D-CBD%2Frest%2Frealspace
```

验证内容：

- `widgets.css` 是否能加载。
- `SuperMap3D.js` 是否能加载。
- 浏览器 WebGL2 是否可用。
- `new SuperMap3D.Viewer(...)` 是否能创建。
- 空三维球上实体点是否能绘制。
- 可选 `scene.open(sceneUrl)` 是否成功。

## 4. 可替换接口

当前真实场景接入点已经固定为：

```javascript
await openScene(viewer, sceneUrl)
```

内部等价于：

```javascript
const scene = await viewer.scenePromise
await scene.open(sceneUrl)
```

`sceneUrl` 来源优先级：

1. `VITE_SUPERMAP_SCENE_URL`
2. 后端 `/api/supermap/config` 返回的 `services.scene.url`
3. `layers[].service_url`

iServer 服务发布后，优先填：

```text
config/supermap_services.local.json
```

当前本机配置：

```text
services.scene.name = 3D-CBD
services.scene.url = http://localhost:8090/iserver/services/3D-CBD/rest/realspace
services.scene.metadata_url = http://localhost:8090/iserver/services/3D-CBD/rest/realspace/scenes/CBD.json
```

必要时也可临时写：

```powershell
$env:VITE_SUPERMAP_SCENE_URL='http://localhost:8090/iserver/services/3D-xxx/rest/realspace'
```

## 5. 已提炼的项目可用 API

### Viewer

```javascript
const viewer = new SuperMap3D.Viewer(container, {
  contextOptions: {
    contextType: 2
  }
})
```

项目默认 `contextType=2`，即 WebGL2。WebGPU 后置，只有浏览器和显卡验证通过后再切 `contextType=3`。

### scene.open

```javascript
const scene = await viewer.scenePromise
await scene.open(sceneUrl)
```

没有 iServer 服务时，可以不传 `sceneUrl`，先在空三维球上绘制 mock 航线、风险区和点位。

### 点线面实体

点：

```javascript
viewer.entities.add({
  position: SuperMap3D.Cartesian3.fromDegrees(lon, lat, height),
  point: { pixelSize: 12, color: SuperMap3D.Color.LIME }
})
```

线：

```javascript
viewer.entities.add({
  polyline: {
    positions: points.map(p => SuperMap3D.Cartesian3.fromDegrees(p[0], p[1], p[2])),
    width: 4,
    material: SuperMap3D.Color.ORANGERED
  }
})
```

面：

```javascript
const positions = polygon.map(p => SuperMap3D.Cartesian3.fromDegrees(p[0], p[1], p[2] || 80))
viewer.entities.add({
  polygon: {
    hierarchy: new SuperMap3D.PolygonHierarchy(positions),
    material: SuperMap3D.Color.RED.withAlpha(0.26)
  }
})
```

### 影像和地形

已在官方示例中核验到：

- `SuperMap3D.SuperMapImageryProvider`
- `SuperMap3D.SuperMapTerrainProvider`
- `SuperMap3D.UrlTemplateImageryProvider`

当前项目先依赖 iServer 场景服务；影像和地形单独接入作为后续增强。

## 6. Vue 注意事项

- 不要把 `viewer` 放进深层响应式对象。
- 当前项目使用 `shallowRef` 保存 Viewer 和 SDK 对象。
- 绘制函数放在 `frontend/src/services/supermap3d.js`，避免组件模板里直接操作大量三维实体。
- 仿真播放时只重绘 demo 实体，不反复重置相机。
- 离开组件时必须执行 `viewer.destroy()`，避免 WebGL 上下文泄漏。

## 7. 排错表

| 问题 | 常见原因 | 处理方式 |
|---|---|---|
| 页面白屏，提示 `failed to load SuperMap3D.js` | SDK 未复制到 `frontend/public/vendor/supermap3d/` 或 `VITE_SUPERMAP_SDK_BASE` 配错 | 运行 `scripts/prepare_iclient3d_public.ps1`，检查浏览器 Network 中 JS 路径 |
| `window.SuperMap3D is not available` | JS 文件返回了 404 HTML 或被浏览器拦截 | 打开 JS URL，确认响应是脚本文件 |
| WebGL2 不可用 | 浏览器、显卡或远程桌面环境不支持 | 换 Chrome/Edge，本机显卡运行，关闭强制 WebGPU |
| Viewer 创建后无球体 | Workers/Assets/ThirdParty 未复制完整 | 确认复制了整个 `Build/SuperMap3D` 相关资源 |
| `scene.open(sceneUrl)` 失败 | iServer 未启动、URL 不是 realspace 服务、跨域未开 | 先打开 iServer 管理页和服务 URL，给 iServer 配 CORS |
| 坐标偏移 | 经纬度顺序写反或数据不是 WGS84 | 项目统一 `[lon, lat, height]`，接真实 GIS 前核对坐标系 |
| 风险面看不到 | 面高度太低、透明度太低或被地形遮挡 | 当前 mock 面使用固定高度 60m，真实场景可改为贴地或抬高 |
| 仿真播放卡顿 | 频繁销毁/创建实体或 Viewer 被 Vue 深层响应式代理 | 保持 Viewer 非响应式，后续可优化为复用 entity 而非全量重绘 |
| WebGPU 不兼容 | 浏览器 WebGPU 未启用或驱动不支持 | 比赛默认 WebGL2，WebGPU 仅作为答辩扩展 |
| 许可弹窗或报错 | 本机许可未激活或试用许可不可用 | 打开官方示例和项目最小验证页截图，必要时联系主办方/老师确认许可 |
| Codex 后台启动后端/前端很快退出 | 当前桌面线程的隐藏后台进程宿主不稳定 | 用普通 PowerShell 分别运行 `scripts\start_backend.ps1` 和 `scripts\start_frontend_supermap_cbd.ps1`，保持窗口不关闭 |

## 8. 当前边界

当前 iClient3D 承载层可以完成：

- 加载 SDK。
- 创建 Viewer。
- 可选打开 `sceneUrl`；当前本机 `3D-CBD` 服务 URL 已确认并写入本地配置。
- 在空三维球上绘制 mock 航线、起终点、风险区、视觉候选区和无人机位置。
- 初始化失败时回退到 `MockMissionMap.vue`。

仍不能替代：

- iDesktopX 制作真实三维场景。
- iServer 发布真实三维服务。
- 真实许可状态截图验收。
- 真实 GIS 数据底座。

当前进度说明：

- `3D-CBD/rest/realspace`、`scenes.json` 和 `scenes/CBD.json` 已通过浏览器/HTTP 验证。
- `config/supermap_services.local.json` 已配置 `3D-CBD`。
- `scripts/prepare_iclient3d_public.ps1` 已通过，前端 SDK 静态资源已准备。
- `npm run build` 已通过。
- 浏览器 WebGL 截图已由用户确认：最小验证页显示 `scene.open(sceneUrl) 成功`，项目工作台显示 `SuperMap 场景已就绪` 并叠加业务图形。
- 当前可将内置 `3D-CBD` 样例服务接入升级为 `SuperMap Verified`；项目自建三维/数据服务仍待后续发布。
