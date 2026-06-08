# SuperMap 接入预案

本目录用于指导 M1 阶段的 SuperMap 底座接入。软件安装完成后，按本文档顺序执行即可。

## 执行顺序

1. `01_idesktopx_workflow.md`：使用 iDesktopX 整理数据、制作任务区域和三维场景。
2. `02_iserver_publish_workflow.md`：使用 iServer 发布地图、三维、数据和空间分析服务。
3. `03_iclient3d_integration_workflow.md`：前端使用 iClient3D for WebGL 接入三维场景。
4. `04_service_url_registry_template.md`：记录服务地址、图层名、字段和验收状态。
5. `05_supermap_acceptance_checklist.md`：对照检查 M1 是否可以验收。

## 当前策略

- 优先使用 SuperMap 2025 正式版。
- 先用示范数据跑通服务发布和前端加载。
- 前端保持 `MockMissionMap.vue` 作为备用。
- 真三维接入集中在 `frontend/src/components/SuperMapScene.vue`。
- 服务 URL 统一写入 `config/supermap_services.example.json`，正式使用时复制为 `config/supermap_services.local.json`。

## 最小跑通目标

- iDesktopX 能打开任务区域数据并保存工作空间。
- iServer 能发布三维服务和数据服务。
- 浏览器能访问 iServer 服务地址。
- 前端能读取服务配置。
- `SuperMapScene.vue` 能从 mock 切换到 SuperMap 接入模式。

