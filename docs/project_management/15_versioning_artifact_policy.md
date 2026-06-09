# 版本管理与生成物归属策略

## 1. 当前结论

当前项目达到 `v0.3-supermap-verified` 阶段证据包标准，但最终比赛提交尚未完成。下一阶段继续开发前，必须先保持 Git 提交点清晰，避免源码、阶段证据包、本地 SuperMap 二进制工作空间和临时探针文件混在一起。

## 2. 进入 Git 的内容

以下内容应进入 Git：

| 类型 | 路径示例 | 原因 |
|---|---|---|
| 前后端源码 | `backend/`、`frontend/src/` | 可复现系统行为 |
| 测试与验收脚本 | `backend/tests/`、`scripts/check_*.ps1`、`scripts/start_*.ps1` | 可复验阶段结论 |
| 轻量配置模板 | `config/*.example.json` | 指导本地配置，不包含个人环境状态 |
| demo 源数据与导出 GeoJSON | `demo_data/task_demo.json`、`demo_data/gis_export/` | 项目自建服务的数据输入，可复现 |
| 项目文档 | `docs/` 中的管理、部署、接口、SuperMap、交付底稿 | 记录边界、证据和操作路径 |
| 轻量生成配置摘要 | `docs/supermap_integration/generated/*.json`、稳定 XML fragment | 记录 iServer 发布配置草稿和接口门禁证据 |
| 工作空间目录说明 | `supermap_file_root/README.md`、`supermap_file_root/demo_workspace/README.md` | 指明本地二进制工作空间放置位置 |
| 启停入口 | `START_DEMO.bat`、`STOP_DEMO.bat` | 方便演示启动，内容轻量 |

## 3. 不进入 Git 的内容

以下内容保留本地或 release 包，不直接进入 Git：

| 类型 | 路径示例 | 处理方式 |
|---|---|---|
| release 阶段证据包 | `release/low_altitude_demo_submission/` | 由 `scripts/prepare_submission_package.ps1` 重新生成 |
| SuperMap 二进制工作空间 | `supermap_file_root/**/*.smwu`、`*.udbx`、`*.udb`、`*.udd` | 本地保留；需要交付时进入 release 或外部附件 |
| iClient3D SDK 静态副本 | `frontend/public/vendor/supermap3d/` | 本地准备，不提交大体积 SDK |
| 临时脚本和缓存 | `.tmp/`、`.pytest_cache/`、`tmp_iobjectspy_probe*/` | 可随时重建 |
| 日志 | `*.log` | 本地排错，不作为稳定证据 |
| 原始截图 dump | `docs/delivery/screenshots/QQ*.png` | 后续复制/重命名为可读证据截图后再纳入 |
| 兼容性重复截图 | `docs/delivery/screenshots/compat_cbd/` | release 可打包，Git 中优先保留主线项目服务证据 |
| 带时间戳配置备份 | `docs/supermap_integration/generated/iserver_config_backups/` | 本地追溯用，Git 中保留稳定摘要和 fragment |

## 4. 提交前建议检查

1. 运行阶段门禁：

```powershell
.\scripts\check_supermap_goal_evidence.ps1 -Strict
.\scripts\prepare_submission_package.ps1
```

2. 运行 Git 归属检查：

```powershell
.\scripts\check_git_artifact_policy.ps1
```

3. 检查工作区：

```powershell
git status --short
```

4. 推荐提交说明：

```text
v0.3-supermap-verified evidence baseline
```

## 5. 当前禁止夸大范围

可以说：

- 已完成 SuperMap scene/map/data 接口级闭环。
- 项目自建 `3D-low_altitude_demo`、`map-low_altitude_demo`、`data-low_altitude_demo` 均有证据支撑。
- 当前 release 可作为阶段证据包和答辩材料整理基线。

不能说：

- 最终比赛提交已经完成。
- 三维效果达到精细建模或真实倾斜摄影级。
- 已具备真实无人机飞控或真实飞行定位闭环。
- PPT、演示视频、三次完整彩排已经完成。
