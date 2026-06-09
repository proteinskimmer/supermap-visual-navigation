# iClient3D 本地安装与接口核验记录

## 1. 核验结论

核验路径：

```text
E:\supermap_software\supermap-iclient3d-for-webgl_webgpu-2025u1
```

当前结论：

- iClient3D for WebGL/WebGPU 2025U1 安装包已解压，目录结构完整。
- 核心 SDK 文件、Widgets 样式、Workers、Assets、ThirdParty 资源、API 文档和示例工程均存在。
- 本地示例已验证到以下接口调用方式：`SuperMap3D.Viewer`、`viewer.scenePromise`、`scene.open`、`SuperMapImageryProvider`、`SuperMapTerrainProvider`、`UrlTemplateImageryProvider`、`viewer.entities.add`、`Cartesian3.fromDegrees`、`Cartesian3.fromDegreesArray`。
- 本次未做浏览器渲染实测，未打开 iServer 真实服务，因此不能升级为 `SuperMap Verified`。
- 许可状态未通过程序化方式验证。按主办方说明，SuperMap GIS 8C 系列产品默认有 90 天试用许可，但本项目仍需在实际打开示例或服务发布时记录截图证据。

建议状态：`Runtime Verified` for iClient3D SDK package，`Blocked` for real SuperMap scene until iServer service URL is available.

## 2. 已确认的本地结构

| 路径 | 核验结果 | 用途 |
|---|---|---|
| `Build/SuperMap3D/SuperMap3D.js` | 存在 | iClient3D 核心 JS |
| `Build/SuperMap3D/Widgets/widgets.css` | 存在 | Viewer 和控件样式 |
| `Build/SuperMap3D/Workers/` | 存在 | 三维引擎后台任务资源 |
| `Build/SuperMap3D/Assets/` | 存在 | 默认纹理、地形和运行资源 |
| `Build/SuperMap3D/ThirdParty/` | 存在 | 第三方依赖 |
| `docs/Documentation/` | 存在，约 719 个 HTML | API 文档 |
| `examples/webgl/` | 存在，约 249 个 HTML | WebGL/WebGPU 示例 |
| `examples/component/` | 存在 | Vue 组件示例 |
| `examples/TopicDOC/` | 存在 | 专题文档，包括 WebGPU 和 Vue 接入说明 |
| `web/` | 存在 | 本地产品文档站 |

## 3. 前端资源引入方式

本地示例采用静态文件方式引入：

```html
<link href="../../Build/SuperMap3D/Widgets/widgets.css" rel="stylesheet">
<script src="../../Build/SuperMap3D/SuperMap3D.js"></script>
```

落到本项目时推荐两种方式：

| 方式 | 说明 | 当前建议 |
|---|---|---|
| 复制 SDK 到 `frontend/public/vendor/supermap3d/` | 前端可用 `/vendor/supermap3d/SuperMap3D.js` 直接加载 | 比赛演示最稳，但 SDK 文件较大，复制前先确认提交包大小 |
| Vite dev server 指向本机安装路径 | 不复制大文件，开发机依赖本地路径 | 适合临时调试，不适合作为最终提交方案 |

正式接入时，不要把 `viewer` 放进 Vue 的 `data`、`computed` 或全局响应式 store。本地专题文档 `Vue&WebGLDevelopment.html` 明确提示这样会降低 SuperMap3D 帧率。项目中应使用 `shallowRef`、普通模块变量或 `window.__supermapViewer` 保存 Viewer 实例。

## 4. 已核验接口

### 4.1 创建 Viewer

本地示例：

```javascript
var viewer = new SuperMap3D.Viewer('Container', {
  contextOptions: {
    contextType: Number(EngineType) // Webgl2:2 ; WebGPU:3
  }
})
```

项目建议：

- 默认使用 WebGL2，即 `contextType: 2`，稳定优先。
- WebGPU 作为可选增强，只有浏览器和显卡环境确认后再启用。
- 初始化后通过 `viewer.scenePromise.then(...)` 进入加载逻辑。

### 4.2 加载 iServer 三维场景

本地示例：

```javascript
var promise = scene.open(URL_CONFIG.SCENE_JINJIANG)
```

项目映射：

- 将 `URL_CONFIG.SCENE_JINJIANG` 替换为 `config/supermap_services.local.json` 中的 `services.scene.url`。
- 服务必须来自 iServer 发布后的真实 REST realspace 地址。
- 没有真实服务前，`SuperMapScene.vue` 继续回退到 `MockMissionMap.vue`。

### 4.3 加载地形与影像

本地示例：

```javascript
terrainProvider: new SuperMap3D.SuperMapTerrainProvider({
  url: URL_CONFIG.SiChuan_TERRAIN,
  isSct: true,
  invisibility: true
})
```

```javascript
viewer.imageryLayers.addImageryProvider(new SuperMap3D.SuperMapImageryProvider({
  url: URL_CONFIG.SiChuan_IMG
}))
```

项目映射：

- 地形服务后续写入 `services.terrain.url` 或场景服务内置。
- 影像服务后续写入 `services.map.url` 或场景服务内置。
- 若先使用公开底图，可用 `UrlTemplateImageryProvider`，但答辩中应说明底图来源。

### 4.4 叠加业务实体

航线：

```javascript
const positions = SuperMap3D.Cartesian3.fromDegreesArray(points)
viewer.entities.add({
  polyline: {
    positions,
    width: 4,
    clampToGround: true
  }
})
```

风险区和视觉候选区：

```javascript
viewer.entities.add({
  polygon: {
    hierarchy: {
      positions: SuperMap3D.Cartesian3.fromDegreesArray(points)
    }
  }
})
```

无人机当前位置：

```javascript
viewer.entities.add({
  position: SuperMap3D.Cartesian3.fromDegrees(lon, lat, height),
  point: new SuperMap3D.PointGraphics({
    pixelSize: 15
  })
})
```

项目映射：

- 航线点来自 `/api/planning/routes`。
- 风险区来自 `demo_data/task_demo.json` 或后续 iServer 数据服务。
- 视觉候选区来自 `/api/vision/match`。
- 当前飞行点来自仿真状态 `currentPoint`。

## 5. 推荐接入路线

1. 保持 `VITE_SCENE_PROVIDER=mock`，确认现有演示闭环不受影响。
2. 将 SDK 复制到 `frontend/public/vendor/supermap3d/` 或确定本机静态加载方案。
3. 在 `SuperMapScene.vue` 中先加载空 Viewer，截图记录。
4. 填写 `config/supermap_services.local.json` 的真实 `services.scene.url`。
5. 用 `scene.open(sceneUrl)` 加载三维场景，截图记录。
6. 叠加航线 polyline，确认经纬度顺序和高度。
7. 叠加风险区 polygon 和视觉候选区 polygon。
8. 接入仿真当前点，完成一次演示彩排。

## 6. 当前未完成项

| 项 | 状态 | 后续动作 |
|---|---|---|
| 浏览器打开本地 iClient3D 示例 | 未验证 | 启动本地静态服务器后打开 `examples/webgl/S3MTiles.html` |
| iServer 三维服务 URL | 未提供 | 等 GIS 组发布服务后填写 |
| 许可有效性截图 | 未验证 | 打开示例或 iServer 页面后截图记录 |
| 前端真实三维渲染 | 未验证 | 服务 URL 可用后接入 `SuperMapScene.vue` |
| WebGPU 模式 | 未验证 | 默认 WebGL2，WebGPU 后置 |

## 7. 可复查命令

```powershell
powershell -ExecutionPolicy Bypass -File scripts\check_supermap_iclient3d.ps1 -SdkRoot "E:\supermap_software\supermap-iclient3d-for-webgl_webgpu-2025u1"
```

