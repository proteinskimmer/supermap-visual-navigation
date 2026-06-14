# SuperMap 低空视觉自主导航仿真系统

本仓库是一个面向低空无人机视觉自主导航的 SuperMap GIS 原型系统。项目主线不是单纯播放航线动画，而是围绕“无人机实时影像与地图/三维场景合成影像匹配”，验证在弱 GPS 或无 GPS 条件下，如何利用正射影像、DEM、建筑物和三维场景数据提供导航定位观测，并在仿真平台中展示飞行轨迹、视觉匹配结果和导航修正效果。

当前共享检查点：

```text
branch: develop
tag: v0.7
commit: 2707001
```

## 项目目标

- 输入：任务起终点、飞行约束、风险区域、DEM、正射影像、建筑物/三维场景数据、无人机影像帧或仿真影像帧。
- 处理：航线规划、安全约束校验、三维场景展示、合成视图生成、OpenCV 多算法影像匹配、视觉定位观测输出、导航状态更新。
- 输出：可解释的低空导航指导，包括推荐航线、风险提示、视觉匹配候选、定位置信度、误差半径、实际轨迹与规划轨迹对比。

## 当前能力

- FastAPI 后端接口：任务、图层、航线规划、风险分析、仿真状态、报告、SuperMap 服务配置、视觉定位。
- Vue + Vite 前端：三维场景展示、航线交互、无人机状态面板、视觉帧选择、算法对比、匹配证据展示。
- SuperMap 接入：支持 iServer 发布的地图、数据和三维服务，当前以珞珈山局部高精度区域为视觉导航主验证区。
- 视觉匹配：已接入 OpenCV ORB/SIFT/AKAZE/BRISK 多 provider，对外保留后续 LoFTR/LightGlue 等深度匹配器适配口。
- 部署脚本：提供 `INSTALL_DEMO.bat`、`START_DEMO.bat`、`STOP_DEMO.bat`，用于 Windows 电脑快速部署和启动。

## 目录结构

```text
backend/                 FastAPI 后端、航线规划、风险分析、视觉定位服务
frontend/                Vue + Vite 前端界面
demo_data/               演示任务数据、GIS 导出数据、生成数据目录
data_sources/            原始或整理后的数据来源说明
config/                  SuperMap 服务 URL 和运行配置
scripts/                 安装、启动、验收、证据生成脚本
docs/                    项目章程、分工、状态日志、交付和部署文档
supermap_file_root/      iServer 文件根目录建议位置
release/                 阶段性交付包目录
```

## 快速部署

推荐组员从 `develop` 分支开始：

```powershell
git clone https://github.com/proteinskimmer/supermap-visual-navigation.git
cd supermap-visual-navigation
git checkout develop
```

目标电脑需要先安装：

```text
Git
Anaconda 或 Miniconda
Node.js 20 LTS 或 22 LTS
SuperMap iServer 2025
SuperMap iClient3D for WebGL/WebGPU 2025U1
```

如果需要重新制作或发布 SuperMap 工作空间，再安装：

```text
SuperMap iDesktopX 2025
```

然后双击：

```text
INSTALL_DEMO.bat
START_DEMO.bat
```

默认访问地址：

```text
http://localhost:5173
```

详细说明见：

```text
docs/deploy_one_click.md
```

## SuperMap 服务要求

首次迁移到新电脑时，一键脚本不能完全代替 iServer 本地配置。需要确认：

- iServer 已启动，并可访问 `http://localhost:8090/iserver`。
- 文件根目录建议设置为项目内 `supermap_file_root`。
- 已发布或可访问项目需要的地图、数据、三维服务。
- `config/supermap_services.json` 中的服务 URL 与目标电脑一致。

正式验收可运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check_supermap_goal_evidence.ps1 -Strict
```

## 项目管理入口

跨对话和跨成员协作时，优先阅读：

```text
docs/project_management/12_project_status_log.md
docs/project_management/08_task_board.md
docs/team_workflow.md
docs/git_handoff.md
```

其中 `12_project_status_log.md` 是项目推进状态的主要记录源。新增功能、验收结果、风险和版本检查点都应同步写入。

## 开发与验证

后端测试：

```powershell
E:\anaconda\envs\supermap_nav\python.exe -m pytest backend\tests -vv
```

前端构建：

```powershell
cd frontend
npm run build
```

注意：不要把大批量生成图片、匹配证据缓存、临时运行产物直接提交到 Git 主仓库。此类文件应通过脚本重新生成，或作为单独演示素材包交付。

## 当前边界

- 视觉导航主线锁定本地高精度区域，当前不把全球在线底图作为核心定位依据。
- 真实航拍图输入可以后续接入；当前重点是用本地 DEM/正射影像/建筑物与合成视图完成可解释的仿真验证。
- 深度学习匹配器接口已预留，但默认共享版本不下载大模型权重。
