# iServer 发布流程

## 1. 目标

使用 SuperMap iServer 2025 发布项目所需的地图服务、三维服务、数据服务和可选空间分析服务，并输出前后端联调用的服务地址。

## 2. 发布前检查

- iServer 已安装并能启动。
- 能访问 iServer 管理页面。
- iDesktopX 工作空间已准备好。
- 数据路径在 iServer 运行环境中可访问。
- 已明确任务区域、图层名、字段规范。

当前项目有两个阶段，必须区分：

| 阶段 | 服务 | 作用 | 状态 |
|---|---|---|---|
| 样例链路验证 | `3D-CBD` | 证明 iServer、iClient3D、浏览器 WebGL 链路可跑通 | 已验证 |
| 项目 demo 服务 | `low_altitude_demo` | 承载本项目任务区、风险区、航线、视觉瓦片等数据 | 待制作工作空间并发布 |

发布项目服务前可运行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\check_low_altitude_demo_publish_ready.ps1
```

该脚本会检查 `demo_data\gis_export` 是否齐全、目标配置是否已指向 `low_altitude_demo`，并提示 `low_altitude_demo.smwu` 是否已经由 iDesktopX 保存。

## 3. 推荐服务类型

| 服务 | 是否必需 | 用途 |
|---|---|---|
| 三维服务 | 是 | 前端 iClient3D 加载三维场景 |
| 地图服务 | 是 | 影像、矢量、风险区二维/叠加备用 |
| 数据服务 | 是 | 后端读取风险区、障碍物、任务区域 |
| 空间分析服务 | 可选 | 缓冲区、叠加分析、空间查询 |

## 4. 操作步骤

### 步骤 1：启动 iServer

1. 从 `bin` 目录启动 SuperMap iServer：

```powershell
cd /d "E:\supermap_software\supermap-iserver-2025u1a-windows-x64-all\bin"
iserver.bat -start
```

不要从安装根目录直接调用 `bin\startup.bat`，否则可能导致 Objects Java/UGO 环境推导错误。

2. 打开管理页面，常见地址类似：

```text
http://localhost:8090/iserver/manager
```

3. 若 `/iserver/manager` 跳转到新版管理页，可使用已验收地址：

```text
http://localhost:8090/iserver/admin-ui/services/serviceManagement
```

4. 登录管理员账号。
5. 检查许可状态和服务状态。

交付：

- 管理页面截图。
- iServer 根地址。

### 步骤 2：注册/选择工作空间

1. 在服务发布入口选择工作空间。
2. 指向 iDesktopX 保存的项目工作空间文件：

```text
E:\supermap_project\supermap_file_root\demo_workspace\low_altitude_demo.smwu
```

3. 确认数据源和图层能被 iServer 识别。

检查：

- 工作空间路径不是官方 `CBD.smwu`，而是项目自己的 `low_altitude_demo.smwu`。
- `task_area`、`risk_zone`、`obstacle`、`vision_tile`、`start_target`、`routes_preview`、`vision_image_center`、`uav_position` 均可识别。
- 如果三维场景暂未制作完成，至少先发布地图服务和数据服务。

### 步骤 3：发布三维服务

1. 选择三维场景或三维数据。
2. 发布为三维服务。
3. 建议服务名：

```text
3D-low_altitude_demo
```

4. 记录服务名和服务 URL。
4. 在浏览器中打开服务详情页面。
5. 查找前端可加载的场景地址、SCP 地址或三维图层地址。

记录到：

```text
docs/supermap_integration/04_service_url_registry_template.md
config/supermap_services.local.json
```

### 步骤 4：发布地图服务

1. 选择任务区域地图或工作空间地图。
2. 发布地图服务。
3. 建议服务名：

```text
map-low_altitude_demo
```

4. 记录地图服务 URL。
4. 浏览器打开确认可访问。

用途：

- 前端备用底图。
- 服务发布截图。
- 答辩说明 SuperMap 服务能力。

### 步骤 5：发布数据服务

1. 选择数据源。
2. 发布数据服务。
3. 建议服务名：

```text
data-low_altitude_demo
```

4. 确认 `task_area`、`risk_zone`、`obstacle`、`vision_tile`、`routes_preview` 等数据集可查询。
4. 记录数据服务 URL 和数据集名称。

后端用途：

- 读取风险区。
- 读取障碍物。
- 读取任务边界。

### 步骤 6：发布空间分析服务，可选

如时间允许，发布空间分析服务，用于：

- 缓冲区分析。
- 叠加分析。
- 空间查询。
- 航线与风险区相交校验。

当前 mock 阶段可暂不依赖该服务。

## 5. 服务 URL 记录格式

每个服务至少记录：

- 服务类型。
- 服务名称。
- 服务 URL。
- 图层/数据集名。
- 是否可浏览器访问。
- 是否已接入前端。
- 是否已接入后端。
- 截图路径。

模板见：

```text
04_service_url_registry_template.md
```

## 6. 验收标准

- iServer 管理页面能访问。
- 至少一个三维服务发布成功。
- 至少一个数据服务发布成功。
- 浏览器直接打开服务 URL 不报错。
- 服务地址已写入记录模板。
- 前端/后端知道使用哪个服务 URL。
- `config/supermap_services.local.json` 已从 `3D-CBD` 切换到 `low_altitude_demo` 服务。
- 前端项目页不再只加载官方 CBD 样例，而能加载项目服务或读取项目数据服务。

## 7. 常见问题

| 问题 | 处理 |
|---|---|
| 服务发布失败 | 检查工作空间路径、许可、数据源是否可访问 |
| 浏览器打不开服务 | 检查 iServer 是否启动、端口是否被占用、防火墙 |
| 前端跨域失败 | 在 iServer 或前端代理中配置 CORS |
| 图层名找不到 | 回到 iDesktopX 检查数据集名称和发布范围 |
| 三维服务加载慢 | 使用更小区域或样例数据先跑通 |
