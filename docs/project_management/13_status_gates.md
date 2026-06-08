# 严格状态门禁

本文件用于避免把“代码初稿”“mock 演示”“真实运行”“SuperMap 接入”和“可交付”混在一起。

## 状态定义

| 状态 | 含义 | 可对外口径 |
|---|---|---|
| `Todo` | 未开始 | 不宣传 |
| `Doing` | 正在做 | 不宣传为能力 |
| `Mock Done` | mock 数据或代码初稿已完成，未完成真实运行验收 | 可说“已完成 mock 原型/代码初稿” |
| `Runtime Verified` | 已安装依赖，后端测试/前端构建/本地页面运行通过 | 可说“本地可运行” |
| `SuperMap Verified` | 真实 iServer 服务发布，前端三维场景加载通过 | 可说“已接入 SuperMap 三维服务” |
| `Delivery Draft` | 文档、PPT 脚本、视频脚本等底稿完成 | 可说“材料底稿已完成” |
| `Delivery Ready` | PPT、视频、截图、提交包完成并彩排通过 | 可说“具备提交条件” |
| `Blocked` | 被环境、数据、软件或接口阻塞 | 必须说明阻塞原因 |

## 当前宣传边界

截至当前状态，本项目只能对外描述为：

> 已完成方案设计、mock 演示闭环初稿、视觉预计算演示框架、SuperMap 接入预案和交付材料底稿，正在进行真实运行验收和 SuperMap 服务接入。

不能描述为：

- 已完成可交付系统。
- 已完成 SuperMap 三维接入。
- 已具备真实无人机自主导航能力。
- 已完成真实视觉定位闭环。
- 已完成比赛提交包。

## 升级条件

### 从 Mock Done 到 Runtime Verified

必须满足：

- 后端依赖安装完成。
- `pytest backend/tests` 通过。
- 前端依赖安装完成。
- `npm run build` 通过。
- 前端页面可打开并完成一次 mock 演示流程。

### 从 Runtime Verified 到 SuperMap Verified

必须满足：

- iDesktopX 工作空间完成。
- iServer 三维服务和数据服务发布成功。
- 服务 URL 已记录。
- 前端加载真实三维场景。
- 航线、风险区、视觉候选区在真实场景中位置正确。

### 从 Delivery Draft 到 Delivery Ready

必须满足：

- PPT 文件完成。
- 演示视频完成。
- 截图素材齐全。
- 提交包整理完成。
- 完成 3 次连续彩排。

