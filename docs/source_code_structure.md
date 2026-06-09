# 源代码目录说明

```text
E:\supermap_project
  backend/
    app/
      api/                 FastAPI 路由
      core/                配置
      models/              Pydantic 请求模型
      services/            数据、几何、规划、风险、视觉、SuperMap 配置服务
      main.py              应用入口
    tests/
      test_mock_api.py     mock API 契约测试
      test_supermap_contracts.py SuperMap 配置接口和统一错误契约测试
    requirements.txt       后端 pip 依赖
  frontend/
    public/
      demo/               视觉样例演示占位图
    src/
      components/
        EmptyState.vue     通用空状态
        ElevationProfile.vue 高程剖面图和统计
        InspectorPanel.vue 右侧航线、风险、视觉面板
        MockMissionMap.vue   mock SVG 态势图，保底演示用
        ReportPage.vue     独立任务报告视图
        SuperMapScene.vue    SuperMap iClient3D 接入边界
        TaskSidebar.vue    左侧任务、图层、控制面板
        TimelinePanel.vue  底部仿真时间轴和事件日志
      services/api.js      前端 API 客户端
      services/supermap3d.js iClient3D SDK 加载、Viewer 创建和三维实体绘制工具
      App.vue              mock 工作台主页面
      styles.css           页面样式
    public/
      supermap-minimal.html iClient3D 最小浏览器验证页
      vendor/supermap3d/   本机 SDK 复制目标，已被 .gitignore 忽略
    package.json           前端依赖和脚本
  demo_data/
    task_demo.json         固定演示数据
    gis_export/            iDesktopX 可导入 GeoJSON demo 数据包
  docs/
    project_management/    项目计划管理文档
    supermap_integration/  SuperMap 接入预案和服务记录模板
    delivery/              PPT、答辩、视频、截图、提交包材料
    deploy_guide.md        部署说明
    system_design.md       系统设计说明
    vision_matching_framework.md
    data_description.md    数据说明
    source_code_structure.md
  scripts/
    start_backend.ps1      后端启动脚本
    start_frontend.ps1     前端启动脚本
    check_backend_smoke.ps1
    check_backend_smoke_full.ps1
    check_project_runtime.ps1 非材料侧综合 runtime 检查
    check_low_altitude_demo_publish_ready.ps1 项目 demo 服务发布前检查
    check_supermap_iclient3d.ps1
    check_supermap_idesktopx.ps1
    export_demo_geojson.ps1
    prepare_iclient3d_public.ps1
  config/
    supermap_services.example.json  SuperMap 服务配置模板
    supermap_services.low_altitude_demo.example.json 项目自建 demo 服务目标模板
  environment.yml          Conda 环境定义
```

## 2026-06-09 Frontend SuperMap service status panel

- `frontend/src/components/SuperMapServicePanel.vue`: reads the loaded SuperMap config and displays scene/map/data service status plus dataset bindings.
- `frontend/src/components/TaskSidebar.vue`: renders the SuperMap service status panel in the left workflow sidebar.
- `frontend/src/App.vue`: passes `supermapConfig` into the sidebar so the UI can show project-owned map/data verification status.