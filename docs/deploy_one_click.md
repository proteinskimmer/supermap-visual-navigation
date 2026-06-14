# 一键部署说明

本文档用于把演示系统迁移到另一台 Windows 电脑，并尽量复现当前电脑上的流畅运行状态。

## 推荐部署流程

1. 克隆或复制完整项目目录到目标电脑。

   推荐路径：

   ```text
   E:\supermap_project
   ```

   其他路径也可以使用。`INSTALL_DEMO.bat`、`START_DEMO.bat`、`STOP_DEMO.bat` 会从脚本所在位置自动识别项目根目录。

2. 在目标电脑安装基础软件。

   必需：

   ```text
   Git
   Anaconda 或 Miniconda
   Node.js 20 LTS 或 22 LTS
   SuperMap iServer 2025
   SuperMap iClient3D for WebGL/WebGPU 2025U1
   ```

   可选，仅在需要重新制作、导入或发布 SuperMap 工作空间时安装：

   ```text
   SuperMap iDesktopX 2025
   ```

3. 双击运行：

   ```text
   INSTALL_DEMO.bat
   ```

   安装脚本会执行：

   - 根据 `environment.yml` 创建或更新 `supermap_nav` conda 环境；
   - 在 `frontend` 目录执行 `npm ci`；
   - 执行 `npm run build`；
   - 必要时把 iClient3D 静态资源复制到 `frontend/public/vendor/supermap3d`；
   - 检查 `supermap_file_root` 和 SuperMap 服务配置是否存在。

4. 确认 iServer 服务发布状态。

   打开：

   ```text
   http://localhost:8090/iserver
   ```

   如果是全新的电脑，需要先完成 iServer 管理员初始化、许可确认、文件根目录设置和项目服务发布。

   文件根目录建议设置为：

   ```text
   <project_root>\supermap_file_root
   ```

   项目演示至少需要确认以下服务地址在目标电脑可访问：

   ```text
   map-low_altitude_demo
   data-low_altitude_demo
   3D-low_altitude_demo
   ```

   对应配置文件：

   ```text
   config\supermap_services.local.json
   ```

   如果需要显示天地图大范围影像背景，在 `services.online_basemap` 中填写本机可用的天地图 token。模板已经预留：

   ```json
   {
     "url": "https://t0.tianditu.gov.cn/img_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=img&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk={token}",
     "token": "填入本机天地图 API 密钥"
   }
   ```

   注意：`config\supermap_services.local.json` 不进入 Git。团队成员需要在各自电脑上从模板复制并填写本机服务地址和 token。

5. 双击启动演示系统：

   ```text
   START_DEMO.bat
   ```

   默认访问地址：

   ```text
   http://localhost:5173
   ```

6. 演示结束后双击停止：

   ```text
   STOP_DEMO.bat
   ```

## 无网络部署

如果目标电脑无法联网，可以使用：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_demo_one_click.ps1 -NoNetwork
```

`-NoNetwork` 模式要求目标电脑已经提前具备：

- conda 环境 `supermap_nav`；
- `frontend\node_modules`；
- 已复制好的 iClient3D SDK：`frontend\public\vendor\supermap3d`。

因此更推荐先在一台能联网的电脑上完成安装，再把项目目录和必要运行环境打包迁移。

## 自定义软件路径

如果 SuperMap 软件没有安装在默认目录，可以手动指定：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_demo_one_click.ps1 `
  -IClient3DRoot "D:\supermap_software\supermap-iclient3d-for-webgl_webgpu-2025u1" `
  -IServerRoot "D:\supermap_software\supermap-iserver-2025u1a-windows-x64-all"
```

## 影响流畅度的注意事项

- 尽量把项目放在本机 SSD，不要直接从移动硬盘或网盘同步目录运行。
- 推荐使用 Chrome 或 Edge，并确认 WebGL 可用。
- 演示时关闭大型下载、视频会议、杀毒全盘扫描等高占用程序。
- 不要在正式演示时运行大规模证据生成脚本，例如 `scripts/generate_v05_match_evidence.py`。
- iServer、后端和前端最好都在同一台机器本地运行，减少局域网延迟和跨机服务地址问题。
- 如果目标电脑显卡较弱，可以降低浏览器窗口分辨率，优先保证无人机轨迹、视觉匹配和右侧状态面板流畅。

## 部署边界

一键脚本可以准备代码依赖、前端构建和静态 SDK 资源，但不能完全替代首次 iServer 管理配置，因为这些内容依赖目标电脑本地的账号、许可、文件根目录和服务注册表。

正式验收前建议运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check_supermap_goal_evidence.ps1 -Strict
```

如果该检查未通过，优先核对 `config\supermap_services.local.json` 中的服务 URL，以及 iServer 是否已经发布并启动对应服务。

## 天地图配置边界

天地图影像只用于大范围三维展示背景，帮助局部珞珈山高精度场景与周边区域连起来。视觉自主导航主线仍以本地 DEM、正射影像、建筑物和合成视图匹配为准。

不要把个人天地图 token 提交到公开仓库。仓库模板只保留 `{token}` 占位符，正式运行时在本机 `config\supermap_services.local.json` 中填写。
