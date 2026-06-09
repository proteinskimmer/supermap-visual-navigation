# SuperMap 接入预案

本目录用于指导 M1 阶段的 SuperMap 底座接入。软件安装完成后，按本文档顺序执行即可。

## 执行顺序

1. `01_idesktopx_workflow.md`：使用 iDesktopX 整理数据、制作任务区域和三维场景。
2. `02_iserver_publish_workflow.md`：使用 iServer 发布地图、三维、数据和空间分析服务。
3. `03_iclient3d_integration_workflow.md`：前端使用 iClient3D for WebGL 接入三维场景。
4. `04_service_url_registry_template.md`：记录服务地址、图层名、字段和验收状态。
5. `05_supermap_acceptance_checklist.md`：对照检查 M1 是否可以验收。
6. `06_iclient3d_local_verification.md`：记录本机 iClient3D SDK 包结构、接口样例和未完成的渲染/许可验证项。
7. `07_iclient3d_frontend_runtime.md`：记录当前前端 iClient3D 承载层、最小验证页、可替换接口和排错表。
8. `08_idesktopx_local_verification.md`：记录本机 iDesktopX 安装结构、样例数据、许可说明和启动链路验收。
9. `09_idesktopx_demo_data_import.md`：记录 demo GeoJSON 数据包生成、iDesktopX 导入顺序、字段说明和样式建议。
10. `09_iserver_local_verification.md`：记录本机 iServer 2025U1A 安装结构、正确启动方式、端口和 HTTP 页面验收。

## 当前策略

- 优先使用 SuperMap 2025 正式版。
- 先用示范数据跑通服务发布和前端加载。
- 前端保持 `MockMissionMap.vue` 作为备用。
- 真三维接入集中在 `frontend/src/components/SuperMapScene.vue`。
- 服务 URL 统一写入 `config/supermap_services.example.json`，正式使用时复制为 `config/supermap_services.local.json`。
- 当前已核验本机 iClient3D 2025U1 SDK 包完整性；iServer 真实服务发布后才能进入 `SuperMap Verified`。
- 当前已实现 iClient3D 前端承载层，可在没有 iServer 的情况下先在空三维球绘制 mock 航线和业务图形。
- 当前已核验本机 iDesktopX 2025 安装结构、启动链路、主界面、试用许可显示和 `CBD` 样例三维场景。
- 当前已生成 `demo_data/gis_export/`，可导入 iDesktopX 制作 demo 工作空间；这一步仍不等于 iServer 发布完成。
- 当前 `3D-CBD` 只作为官方样例链路验证；下一门禁是发布 `low_altitude_demo` 自建服务并替换前端配置。
- 当前已核验本机 iServer 2025U1A：必须从 `bin` 目录运行 `iserver.bat -start`，默认端口 `8090`，`/iserver`、服务列表、管理页和帮助页均已返回 HTTP 200。
- iServer 当前仅达到安装与运行入口验收；真实 `3D-CBD` 或项目三维服务 URL、iClient3D `scene.open(sceneUrl)` 浏览器渲染截图仍待完成。

## 最小跑通目标

- iDesktopX 能打开任务区域数据并保存工作空间。
- iServer 能发布三维服务和数据服务。
- 浏览器能访问 iServer 服务地址。
- 前端能读取服务配置。
- `SuperMapScene.vue` 能从 mock 切换到 SuperMap 接入模式。
- 前端配置从 `3D-CBD` 切换为 `3D-low_altitude_demo` 或 `data-low_altitude_demo`。
