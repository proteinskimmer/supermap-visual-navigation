# SuperMap 接口闭环目标审计

更新时间：2026-06-09

本文件按原始目标逐项审计，不用乐观口径替代证据。

## 审计结论

接口级目标、浏览器自动验收和 GUI 原始截图补证均已完成。

可以标为已完成：

- `导入 GeoJSON -> 生成地图 -> 保存 smwu -> 验收 REST` 一键流程。
- 前端读取真实 `map-low_altitude_demo` / `data-low_altitude_demo` 服务状态。
- `low_altitude_demo_map`、8 个业务图层、scene/map/data REST 门禁。
- 项目自建 `3D-low_altitude_demo` REST 门禁。
- 前端默认项目自建 3D，且可通过环境变量切换回官方 `3D-CBD`。
- 浏览器自动验收与主截图保存。

本目标可标为已完成。仍需注意：当前 `3D-low_altitude_demo` 是最小项目场景和接口级验收，不等同于精细三维建模或真实倾斜摄影成果。

## 逐项审计

| 原始要求 | 当前证据 | 结论 |
| --- | --- | --- |
| 导入 GeoJSON | `scripts/run_low_altitude_map_data_pipeline.ps1` 复跑通过；`demo_data/gis_export/*.geojson` 已生成 | 已完成 |
| 生成地图 | iObjectSpy 自动生成 `low_altitude_demo_map`，摘要记录 8 个图层 | 已完成 |
| 保存 smwu | `supermap_file_root/demo_workspace_auto/low_altitude_demo.smwu` 已生成；正式 `supermap_file_root/demo_workspace/low_altitude_demo.smwu` 存在 | 已完成 |
| 验收 REST | `scripts/check_supermap_delivery_gate.ps1` 由管线调用通过 | 已完成 |
| 后端 `/api/supermap/services` 返回最新配置 | 浏览器验收脚本输出 HTTP 200，scene/map/data 均 verified | 已完成 |
| 前端读取真实 map/data 服务 | `frontend_supermap_workspace.png` 与服务面板验证 | 已完成 |
| `map-low_altitude_demo: verified` | `config/supermap_services.local.json` 与 REST 门禁输出 | 已完成 |
| `data-low_altitude_demo: verified` | `config/supermap_services.local.json` 与 REST 门禁输出 | 已完成 |
| `low_altitude_demo_map` 可访问 | `iserver_map_low_altitude_demo_map.png`、`iserver_map_low_altitude_demo_map_json.png` | 已完成 |
| 8 个业务图层可访问 | `layers.json` 门禁检查、`data-low_altitude_demo` datasets 截图、前端服务面板 | 已完成 |
| 前端仍能加载 `3D-CBD` | `docs/delivery/screenshots/compat_cbd/frontend_supermap_workspace.png` | 已完成 |
| 业务航线/风险区/视觉瓦片叠加 | `frontend_supermap_workspace.png` | 已完成 |
| 服务状态显示 map/data verified | `frontend_supermap_workspace.png` | 已完成 |
| 保存 map 服务页面截图 | `iserver_map_low_altitude_demo_map.png` | 已完成 |
| 保存 data 数据集列表截图 | `iserver_data_low_altitude_demo_datasets.png` | 已完成 |
| 保存前端工作台 SuperMap 场景加载页 | `frontend_supermap_workspace.png` | 已完成 |
| 发布 `3D-low_altitude_demo` 下一门禁 | `iserver_3d_low_altitude_demo_scenes.png`、`check_low_altitude_3d_gate.ps1` | 已完成接口级门禁 |
| 保存 iServer 发布成功页 | `iserver_publish_success_admin.png` 已由用户在真实交互桌面补证；`iserver_services_list.png` 作为无登录公共服务列表证据保留 | 已完成 |
| 保存 iDesktopX 中 `low_altitude_demo_map` 图层显示 | `idesktopx_low_altitude_demo_map_layers.png` 已由用户在真实交互桌面补证；`low_altitude_demo_map_iobjectspy_preview.png` 作为脚本替代证据保留 | 已完成 |

## 复验命令

补证已完成。后续复验使用：

```powershell
powershell -ExecutionPolicy Bypass -File E:\supermap_project\scripts\check_supermap_goal_evidence.ps1 -Strict
```

## 严格状态

```text
接口闭环：Done
自动浏览器验收：Done
项目自建 3D REST 门禁：Done
GUI 原始截图补证：Done
```
