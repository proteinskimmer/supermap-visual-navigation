# GitHub 接管说明

仓库地址：

```text
https://github.com/proteinskimmer/supermap-visual-navigation
```

## 分支说明

```text
main                         稳定演示基线
develop                      团队集成分支
codex/v0.5-development       Codex 历史工作分支
```

稳定标签：

```text
v0.4
v0.5
v0.6
```

## 第一次克隆

```powershell
git clone https://github.com/proteinskimmer/supermap-visual-navigation.git
cd supermap-visual-navigation
git checkout develop
```

然后按部署说明准备环境：

```text
docs/deploy_one_click.md
```

## 需要注意的本地文件

以下内容和本机环境或生成过程有关，克隆仓库后不一定直接存在：

- SuperMap 已发布服务注册状态；
- 本机 iServer 账号、许可和管理根目录；
- 批量生成的视觉证据图片；
- 大型原始 GIS 数据；
- 如果未复制 SDK，`frontend/public/vendor/supermap3d` 也不会存在。

新电脑请先运行：

```text
INSTALL_DEMO.bat
```

用于准备依赖和 iClient3D 静态资源。

## 接管前应阅读

```text
CONTRIBUTING.md
docs/team_workflow.md
docs/project_management/12_project_status_log.md
```

然后确认当前演示状态：

```powershell
cd frontend
npm run build
cd ..
E:\anaconda\envs\supermap_nav\python.exe -m pytest backend/tests
```
