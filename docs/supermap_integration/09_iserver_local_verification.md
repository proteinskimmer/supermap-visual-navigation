# iServer 本地安装与运行验收记录

## 1. 核验结论

核验路径：

```text
E:\supermap_software\supermap-iserver-2025u1a-windows-x64-all
```

当前结论：

- SuperMap iServer 2025U1A 安装目录存在，Tomcat/iServer 结构完整。
- `bin/startup.bat`、`bin/shutdown.bat`、`bin/iserver.bat`、`conf/server.xml`、`webapps/iserver`、`samples/`、`docs/`、`support/jre`、`support/objectsjava` 和 `support/SuperMapLicenseCenter` 均存在。
- 自带 JRE 可运行，版本为 OpenJDK `17.0.13+11`。
- `iserver.bat -v` 输出 iServer 版本：`12.0.0.0-24929`，主 jar 为 `iserver-all-12.0.1.0-24929.jar`。
- `server.xml` 默认 HTTP 端口为 `8090`，shutdown 端口为 `8015`。
- 已从正确目录 `bin/` 使用 `iserver.bat -start` 启动服务。
- 启动后 `java.exe` 监听 `0.0.0.0:8090` 和 `127.0.0.1:8015`。
- 已完成 iServer 初始化向导，服务管理器地址为 `http://localhost:8090/iserver/admin-ui/home`。
- 已配置文件管理根目录为 `E:\supermap_project\supermap_file_root`，用于限制 iServer 可浏览、上传和管理的数据文件范围。
- 以下地址已返回 HTTP 200：
  - `http://localhost:8090/iserver`
  - `http://localhost:8090/iserver/services`
  - `http://localhost:8090/iserver/admin-ui/services/serviceManagement`
  - `http://localhost:8090/iserver/help`

严格状态：

- 可以说：`iServer 2025U1A 安装、正确启动入口、8090 端口、管理页和服务页已通过运行验收`。
- 不能说：`项目三维服务已发布并完成前端接入`。
- 已完成：iClient3D 前端加载 `3D-CBD` 场景并完成浏览器截图确认。
- 还需要完成：项目自建三维/数据服务仍待后续发布。

## 2. 启动方式要求

必须从 `bin` 目录运行：

```powershell
cd /d "E:\supermap_software\supermap-iserver-2025u1a-windows-x64-all\bin"
iserver.bat -start
```

停止服务：

```powershell
cd /d "E:\supermap_software\supermap-iserver-2025u1a-windows-x64-all\bin"
shutdown.bat
```

重要说明：

- 不要从安装根目录直接调用 `bin\startup.bat`。
- `setenv.bat` 依赖当前目录推导 `ISERVER_ROOT`，从错误目录启动会导致 `UGO_HOME`/Objects Java 环境不正确。
- 本次曾从安装根目录启动，导致 `/iserver` 主应用环境检查失败，日志出现 `Tool.isGreatUGOVersion` 空指针；改为从 `bin` 目录运行 `iserver.bat -start` 后恢复正常。

## 3. 已确认的关键结构

| 路径 | 核验结果 | 用途 |
|---|---|---|
| `bin/iserver.bat` | 存在 | iServer 官方启动入口 |
| `bin/startup.bat` | 存在 | Tomcat 启动脚本 |
| `bin/shutdown.bat` | 存在 | Tomcat 停止脚本 |
| `bin/version.bat` | 存在 | 版本信息脚本 |
| `conf/server.xml` | 存在 | 端口和 Tomcat 配置 |
| `webapps/iserver` | 存在 | iServer 主应用 |
| `webapps/ROOT` | 存在 | 根应用 |
| `docs/` | 存在 | 本地帮助文档 |
| `iClient/for3D/webgl` | 存在 | iClient3D 资源 |
| `iClient/forJavaScript` | 存在 | iClient JS 资源 |
| `samples/data` | 存在 | 示例数据 |
| `support/jre` | 存在 | 自带 Java 17 |
| `support/objectsjava` | 存在 | iObjects Java/UGO 组件 |
| `support/SuperMapLicenseCenter` | 存在 | 许可中心 |

## 4. 内置样例服务线索

`webapps/iserver/WEB-INF/iserver-services-samples.xml` 已确认包含：

| 服务组件 | 样例工作空间 |
|---|---|
| `map-world` | `../../samples/data/World/World.sxwu` |
| `data-world` | `../../samples/data/World/World.sxwu` |
| `3D-CBD` | `../../samples/data/Realspace/CBD/CBD.sxwu` |

项目优先验证的三维服务 URL：

```text
http://localhost:8090/iserver/services/3D-CBD/rest/realspace
```

当前已在浏览器中确认该地址进入 `三维服务根节点(3D)` 页面，并显示 `datas`、`scenes`、`symbols` 子资源。

已确认场景列表：

| 地址 | 结果 |
|---|---|
| `http://localhost:8090/iserver/services/3D-CBD/rest/realspace.json` | HTTP 200，返回三维服务根资源 JSON |
| `http://localhost:8090/iserver/services/3D-CBD/rest/realspace/scenes.json` | HTTP 200，返回场景 `CBD` |
| `http://localhost:8090/iserver/services/3D-CBD/rest/realspace/scenes/CBD.json` | HTTP 200，返回 `CBD` 场景 JSON，包含 `Tree@CBD` 等三维图层 |

iClient3D `scene.open(sceneUrl)` 当前采用：

```text
http://localhost:8090/iserver/services/3D-CBD/rest/realspace
```

说明：官方 iClient3D 示例中的 `SCENE_*` 配置也是指向 `/rest/realspace` 场景服务根地址；`/scenes/CBD.json` 作为元数据验收地址，不作为优先 `scene.open` 地址。

## 5. 已验证地址

| 地址 | 结果 |
|---|---|
| `http://localhost:8090/iserver` | HTTP 200 |
| `http://localhost:8090/iserver/services` | HTTP 200 |
| `http://localhost:8090/iserver/admin-ui/services/serviceManagement` | HTTP 200 |
| `http://localhost:8090/iserver/help` | HTTP 200，标题为 `SuperMap iServer OnlineHelp` |
| `http://localhost:8090/iserver/services/3D-CBD/rest/realspace` | 浏览器可打开，显示 `三维服务根节点(3D)` |
| `http://localhost:8090/iserver/services/3D-CBD/rest/realspace/scenes.json` | HTTP 200，返回 `CBD` 场景 |
| `http://localhost:8090/iserver/services/3D-CBD/rest/realspace/scenes/CBD.json` | HTTP 200，返回场景 JSON 和图层信息 |
| `http://localhost:5173/supermap-minimal.html?sceneUrl=...3D-CBD...` | 浏览器截图确认 WebGL2、SDK、Viewer、实体点和 `scene.open(sceneUrl)` 成功 |
| `http://localhost:5173/` | 浏览器截图确认项目工作台 `SuperMap 场景已就绪`，并叠加业务图形 |

初始化向导完成页已确认：

| 项 | 值 |
|---|---|
| 首页 | `http://localhost:8090/iserver/` |
| 服务管理器 | `http://localhost:8090/iserver/admin-ui/home` |
| 文件管理根目录 | `E:\supermap_project\supermap_file_root` |

命令行请求 REST 服务 URL 时，当前返回新版 iServer 前端 SPA HTML 页面。后续需要在浏览器中确认服务详情页和可复制的 REST 服务地址。

## 6. 当前未完成项

| 项 | 状态 | 后续动作 |
|---|---|---|
| 浏览器截图 | 部分完成 | 已确认 iServer `3D-CBD` 页面、iClient3D 最小验证页和项目工作台截图；正式截图文件仍待保存到 `docs/delivery/screenshots/` |
| 管理员初始化/登录 | 已完成 | 初始化向导已进入完成页；账号信息不写入仓库 |
| 文件管理根目录 | 已完成 | 已配置为 `E:\supermap_project\supermap_file_root` |
| `3D-CBD` 服务详情页 | 已完成 | 浏览器已打开 `3D-CBD/rest/realspace` 三维服务根节点 |
| 本地服务配置 | 已完成 | `config/supermap_services.local.json` 已配置 `3D-CBD` 场景服务 URL |
| 前端 iClient3D 加载 iServer 3D 服务 | 已完成 | `supermap-minimal.html` 和项目工作台均已截图确认加载 `3D-CBD` 成功 |
| 项目真实三维服务发布 | 未开始 | 使用 iDesktopX 项目工作空间发布到 iServer |

## 7. 可复查命令

```powershell
powershell -ExecutionPolicy Bypass -File scripts\check_supermap_iserver.ps1 -InstallRoot "E:\supermap_software\supermap-iserver-2025u1a-windows-x64-all"
```

## 2026-06-09 low_altitude_demo 项目服务发布记录

### 发布结果

| 服务 | URL | 验收结果 | 状态口径 |
|---|---|---|---|
| `map-low_altitude_demo` | `http://localhost:8090/iserver/services/map-low_altitude_demo/rest/maps` | HTTP 200；`maps.json` 返回 `[]` | 已发布，但工作空间尚未保存地图对象，暂记为 `published_no_maps` |
| `data-low_altitude_demo` | `http://localhost:8090/iserver/services/data-low_altitude_demo/rest/data` | HTTP 200；`datasources.json` 可见 `low_altitude_demo` | 已发布并完成数据服务验收，记为 `verified` |

### 数据集验收

`data-low_altitude_demo` 已返回 8 个数据集：

```text
obstacle_ZP
routes_preview_ZL
start_target_ZP
task_area_R
uav_position_ZP
vision_image_center_ZP
risk_zone_R
vision_tile_R
```

### 配置同步

已更新 `config/supermap_services.local.json`：

- `workspace_path` 指向 `E:\supermap_project\supermap_file_root\demo_workspace\low_altitude_demo.smwu`。
- `services.data` 指向 `data-low_altitude_demo`，状态为 `verified`。
- `services.map` 指向 `map-low_altitude_demo`，状态为 `published_no_maps`。
- `services.scene` 仍保留官方样例 `3D-CBD`，状态为 `verified`，用于三维底座链路；项目自建 `3D-low_altitude_demo` 尚未发布。

### 下一门禁

若需要让地图服务返回具体地图，需要回到 iDesktopX，把 8 个数据集叠加成一张地图并保存到工作空间，再在 iServer 中刷新/重启对应服务。否则当前阶段可先使用数据服务作为项目自建 GIS 服务验收证据。