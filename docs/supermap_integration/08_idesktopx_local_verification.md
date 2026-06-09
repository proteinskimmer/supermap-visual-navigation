# iDesktopX 本地安装验收记录

## 1. 核验结论

核验路径：

```text
E:\supermap_software\SuperMap iDesktopX 2025
```

当前结论：

- SuperMap iDesktopX 2025 安装目录存在，核心目录和启动文件完整。
- 主程序 `SuperMap iDesktopX.exe`、`startup.bat`、`iDesktop.jar`、自带 JRE、核心 GIS/三维/许可组件、帮助文档和样例数据均存在。
- 自带 Java 可运行，版本为 OpenJDK `1.8.0_452`。
- `bin/VERSION` 显示版本信息：`12.0.1 24930 125282 x64_Beijing`。
- `What_is_new.html` 标注版本号 `12.0.1.0`，发布日期 `2025.09`。
- `readme.html` 明确说明：若使用安装包，产品首次安装成功后已具有 90 天试用许可，无需再次申请试用许可。
- 已实际启动一次 `SuperMap iDesktopX.exe`，程序未秒退，并拉起 `javaw.exe` 与 SuperMap License Center 进程，说明启动链路已进入许可/运行阶段。
- 用户截图已确认 iDesktopX 主界面可进入，`CBD` 样例工作空间已加载，`CBD` 三维场景可渲染显示，右下角显示本地试用许可剩余 90 天。

严格状态：

- 可以说：`iDesktopX 2025 安装、启动、试用许可显示、CBD 样例工作空间加载和三维场景显示已验证`。
- 不能说：`iDesktopX 已完成三维服务发布`。
- 还需要完成：将正式截图文件归档，并进入 iServer 发布环节。

## 2. 已确认的关键文件

| 路径 | 核验结果 | 用途 |
|---|---|---|
| `SuperMap iDesktopX.exe` | 存在 | GUI 主入口 |
| `startup.bat` | 存在 | Java 启动脚本 |
| `iDesktop.jar` | 存在 | 桌面启动入口 |
| `bin/` | 存在 | 核心 DLL、JAR、数据引擎和三维引擎 |
| `jre/` | 存在 | 自带 Java 运行环境 |
| `help/SuperMap iDesktopX Help.chm` | 存在 | 本地帮助文档 |
| `SuperMap iDesktopX UserManual.pdf` | 存在 | 用户手册 |
| `InstallationGuide.pdf` | 存在 | 安装指南 |
| `readme.html` | 存在 | 产品说明和许可说明 |
| `What_is_new.html` | 存在 | 版本和新特性说明 |
| `sampleData/` | 存在 | 样例数据 |

## 3. 项目相关能力核验

| 能力 | 关键文件或目录 | 结果 |
|---|---|---|
| 工作空间/数据源打开 | `sampleData/3D/CBDDataset/CBD.smwu`、`CBD.udb`、`CBD.udd` | 存在 |
| 二维 WebMap 样例 | `sampleData/WebMap/China100/China100.smwu`、`China100.udbx` | 存在 |
| 三维场景/真实空间能力 | `com.supermap.realspace.jar`、`WrapjRealspace.dll`、`SuScene.dll` | 存在 |
| 三维缓存/瓦片制作 | `SuCacheBuilder3D.dll`、`SuToolkit3DTiles.dll` | 存在 |
| 数据转换 | `com.supermap.data.conversion.jar` | 存在 |
| 空间分析 | `com.supermap.analyst.spatialanalyst.jar` | 存在 |
| 地形分析 | `com.supermap.analyst.terrainanalyst.jar` | 存在 |
| 许可管理 | `com.supermap.licensemanager.jar`、SuperMap License Center 进程 | 存在/已拉起 |

## 4. 样例数据

已发现可用于后续验收的样例：

```text
sampleData\3D\CBDDataset\CBD.smwu
sampleData\3D\CBDDataset\CBD.udb
sampleData\3D\CBDDataset\CBD.udd
sampleData\3D\CBDDataset\FlyRoutes.fpf
sampleData\WebMap\China100\China100.smwu
sampleData\WebMap\China100\China100.udbx
sampleData\WebMap\China100\SouthSea.udbx
sampleData\WebMap\China100\WorldPhysical.udbx
sampleData\DistributedAnalysis\OnlineAnalysis.udb
sampleData\DistributedAnalysis\OnlineAnalysis.udd
```

后续 GUI 验收优先打开：

```text
E:\supermap_software\SuperMap iDesktopX 2025\sampleData\3D\CBDDataset\CBD.smwu
```

验收目标：

1. iDesktopX 主界面可进入。
2. 无许可错误弹窗阻塞。
3. `CBD.smwu` 可打开。
4. 三维场景或数据源可显示。
5. 截图保存到 `docs/delivery/screenshots/`。

## 5. 许可说明

本地 `readme.html` 中“4.1.1 试用许可”说明：

- 使用安装包时，首次安装成功后具有 90 天试用许可。
- 若使用绿色包，需另行申请试用许可。
- 许可到期后按比赛报名系统或 SuperMap 许可流程申请延长。

本项目当前口径：

- 可以依据安装包说明、主办方说明和 GUI 截图按“本地试用许可可用，剩余 90 天”推进。
- 正式交付材料仍需将许可状态截图保存为文件。

## 6. 当前未完成项

| 项 | 状态 | 后续动作 |
|---|---|---|
| GUI 主界面截图 | 对话证据已完成 | 后续保存正式截图文件到 `docs/delivery/screenshots/` |
| 打开 `CBD.smwu` 样例 | 对话证据已完成 | `CBD` 工作空间已在工作空间管理器中显示 |
| 三维场景显示截图 | 对话证据已完成 | `CBD` 三维建筑、道路和地形图层已显示，后续保存正式截图文件 |
| 许可状态截图 | 对话证据已完成 | 右下角显示本地试用许可剩余 90 天，后续保存正式截图文件 |
| 发布到 iServer | 未开始 | 等 iServer 安装验收后执行 |

## 7. 可复查命令

```powershell
powershell -ExecutionPolicy Bypass -File scripts\check_supermap_idesktopx.ps1 -InstallRoot "E:\supermap_software\SuperMap iDesktopX 2025"
```
