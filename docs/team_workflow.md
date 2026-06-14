# 团队协作流程

## 当前稳定基线

当前稳定 Git 检查点：

```text
tag: v0.6
branch: main
branch: develop
```

`v0.6` 包含：

- 视觉当前帧显示修复；
- 在线区域影像贴地形预览；
- 一键部署准备；
- 航线安全约束相关稳定修复。

## 建议分工

| 小组 | 分支前缀 | 主要任务 |
| --- | --- | --- |
| 视觉组 | `feature/vision-*` | OpenCV/SIFT/AKAZE/BRISK、证据生成、视觉定位可信度 |
| 前端组 | `feature/frontend-*` | 驾驶舱 UI、视觉帧面板、可视化、截图验收 |
| SuperMap/GIS 组 | `feature/supermap-*` | 珞珈山工作空间、iServer 服务、DEM/正射/建筑数据 |
| 文档交付组 | `feature/docs-*` | PPT、报告、演示讲稿、验收清单 |

## 日常开发流程

1. 拉取最新 `develop`。
2. 新建功能分支。
3. 做小范围、聚焦的修改。
4. 运行对应检查。
5. 向 `develop` 发起 Pull Request。
6. 经过检查或 Review 后合并。
7. 达到可演示状态后打新版本标签。

示例：

```powershell
git checkout develop
git pull
git checkout -b feature/frontend-vision-panel
```

## 演示版本管理

演示检查点用 tag 固化。

示例：

```text
v0.6
v0.7
v1.0-demo
```

每个 tag 都应该对应一个可以解释、最好也能通过 `START_DEMO.bat` 启动的项目状态。

## 新电脑本地部署

新电脑优先使用：

```text
INSTALL_DEMO.bat
START_DEMO.bat
STOP_DEMO.bat
```

详细说明见：

```text
docs/deploy_one_click.md
```

## 合并前检查清单

合并到 `develop` 前请确认：

- 没有误提交大型生成文件。
- 前端仍能构建。
- 改动后端行为时，后端测试通过。
- 重要里程碑已更新项目状态日志。
- 演示口径真实：区分 mock/proxy、OpenCV 证据、真实 SuperMap 服务状态。
