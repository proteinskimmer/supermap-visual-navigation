# SuperMap 官方文档本地索引

本目录记录本项目使用到的 SuperMap 官方文档入口。当前没有复制全量 HTML 文档到仓库，原因是 iClient3D 安装包已经包含完整本地文档和示例，且文件数量较多。

## iClient3D for WebGL/WebGPU 2025U1

本机安装路径：

```text
E:\supermap_software\supermap-iclient3d-for-webgl_webgpu-2025u1
```

常用入口：

| 类型 | 本机路径 | 说明 |
|---|---|---|
| 产品首页 | `E:\supermap_software\supermap-iclient3d-for-webgl_webgpu-2025u1\index.html` | 安装包入口 |
| 本地文档站 | `E:\supermap_software\supermap-iclient3d-for-webgl_webgpu-2025u1\web\index.html` | 产品文档和说明 |
| API 文档 | `E:\supermap_software\supermap-iclient3d-for-webgl_webgpu-2025u1\docs\Documentation\index.html` | API 查询 |
| WebGL 示例 | `E:\supermap_software\supermap-iclient3d-for-webgl_webgpu-2025u1\examples\webgl\` | 示例源码 |
| Vue 组件示例 | `E:\supermap_software\supermap-iclient3d-for-webgl_webgpu-2025u1\examples\component\vue_viewer.html` | Vue 接入参考 |
| WebGPU 专题 | `E:\supermap_software\supermap-iclient3d-for-webgl_webgpu-2025u1\examples\TopicDOC\HowToUseWebGPU.html` | WebGPU 切换说明 |
| Vue 专题 | `E:\supermap_software\supermap-iclient3d-for-webgl_webgpu-2025u1\examples\TopicDOC\Vue&WebGLDevelopment.html` | Vue 性能注意事项 |

## 本项目已整理文档

- `docs/supermap_integration/03_iclient3d_integration_workflow.md`
- `docs/supermap_integration/06_iclient3d_local_verification.md`
- `docs/supermap_integration/08_idesktopx_local_verification.md`
- `docs/supermap_integration/09_iserver_local_verification.md`

如后续需要离线提交全量官方文档，再从安装包中复制 `docs/Documentation/`、`examples/TopicDOC/` 和必要图片资源。

## iDesktopX 2025

本机安装路径：

```text
E:\supermap_software\SuperMap iDesktopX 2025
```

常用入口：

| 类型 | 本机路径 | 说明 |
|---|---|---|
| 主程序 | `E:\supermap_software\SuperMap iDesktopX 2025\SuperMap iDesktopX.exe` | GUI 启动入口 |
| 启动脚本 | `E:\supermap_software\SuperMap iDesktopX 2025\startup.bat` | Java 启动链路 |
| 自述文件 | `E:\supermap_software\SuperMap iDesktopX 2025\readme.html` | 产品、环境和许可说明 |
| 新特性 | `E:\supermap_software\SuperMap iDesktopX 2025\What_is_new.html` | 版本和新功能 |
| 用户手册 | `E:\supermap_software\SuperMap iDesktopX 2025\SuperMap iDesktopX UserManual.pdf` | 操作手册 |
| 本地帮助 | `E:\supermap_software\SuperMap iDesktopX 2025\help\SuperMap iDesktopX Help.chm` | 完整帮助 |
| 三维样例 | `E:\supermap_software\SuperMap iDesktopX 2025\sampleData\3D\CBDDataset\CBD.smwu` | 后续 GUI 验收优先打开 |

## iServer 2025U1A

本机安装路径：

```text
E:\supermap_software\supermap-iserver-2025u1a-windows-x64-all
```

常用入口：

| 类型 | 本机路径或地址 | 说明 |
|---|---|---|
| 启动入口 | `E:\supermap_software\supermap-iserver-2025u1a-windows-x64-all\bin\iserver.bat` | 必须从 `bin` 目录执行 `iserver.bat -start` |
| 停止脚本 | `E:\supermap_software\supermap-iserver-2025u1a-windows-x64-all\bin\shutdown.bat` | 停止本机 iServer |
| Tomcat 配置 | `E:\supermap_software\supermap-iserver-2025u1a-windows-x64-all\conf\server.xml` | 默认 HTTP 端口 `8090`，shutdown 端口 `8015` |
| 本地帮助 | `http://localhost:8090/iserver/help` | 已返回 HTTP 200 |
| 服务列表 | `http://localhost:8090/iserver/services` | 已返回 HTTP 200 |
| 管理页 | `http://localhost:8090/iserver/admin-ui/services/serviceManagement` | 已返回 HTTP 200，后续用于确认/发布服务 |
| 内置 3D-CBD 线索 | `http://localhost:8090/iserver/services/3D-CBD/rest/realspace` | 需在浏览器服务详情页确认后再填入前端 |

本项目验收记录见 `docs/supermap_integration/09_iserver_local_verification.md`。
