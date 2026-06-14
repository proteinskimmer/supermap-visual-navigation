# 团队贡献规范

本仓库是 SuperMap 视觉自主导航演示系统的团队协作仓库。所有成员提交代码、文档和数据前，请先阅读本规范。

## 分支约定

- `main`：稳定演示基线，必须保持可运行。
- `develop`：团队日常集成分支，功能分支合并到这里。
- `feature/vision-*`：视觉定位、影像匹配、算法证据相关工作。
- `feature/frontend-*`：前端界面、交互、可视化、截图验收相关工作。
- `feature/supermap-*`：GIS 数据、SuperMap 服务、三维场景相关工作。
- `feature/docs-*`：文档、报告、PPT、讲稿和交付材料相关工作。

不要直接向 `main` 提交。日常开发请从 `develop` 拉功能分支，完成后通过 Pull Request 合并回 `develop`。

## 提交前检查

根据改动范围运行对应检查。

前端改动：

```powershell
cd E:\supermap_project\frontend
npm run build
```

后端改动：

```powershell
cd E:\supermap_project
E:\anaconda\envs\supermap_nav\python.exe -m pytest backend/tests
```

SuperMap 服务或验收证据相关改动：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check_supermap_goal_evidence.ps1 -Strict
```

## 文件入库原则

建议提交：

- 源代码；
- 小型配置文件；
- 项目文档；
- 小型、经过整理的演示 JSON 数据。

不要随意提交：

- 自动生成的无人机影像帧缓存；
- 批量生成的 OpenCV 证据图；
- 视频文件；
- 原始大型 GIS 数据；
- 本地 SuperMap 二进制工作空间；
- `node_modules`；
- 本地 Python/Conda 环境目录。

大型证据、视频、原始数据和交付素材建议通过 GitHub Release、网盘或单独的交付包共享，不要直接混进源码提交。

## 提交信息规范

提交信息要短、清楚，说明改了什么。

示例：

```text
修复视觉帧同步
新增 SuperMap 部署检查脚本
补充 v0.6 GitHub 接管说明
```

## Pull Request 要求

每个 PR 至少说明：

- 改了什么；
- 如何验证；
- 是否包含生成文件或大型素材；
- 如果改了 UI 或 SuperMap 场景，附截图或说明验收方式。
