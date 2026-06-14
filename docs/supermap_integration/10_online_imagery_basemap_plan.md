# 在线影像底图接入预案

创建时间：2026-06-14

## 目标

在线影像底图用于大范围动态背景展示，让局部珞珈山高精度三维场景看起来能和周边区域衔接。它不是视觉自主导航的核心数据源。

目标行为：

```text
视角移动
-> SuperMap3D 按可见范围请求在线影像瓦片
-> 珞珈山任务区仍由本地 DEM、正射影像和建筑物覆盖
-> 视觉导航仍读取本地高精度数据和合成视图匹配结果
```

## 需要收集的信息

接入 SuperMap Online、iServer、WMTS、XYZ 或天地图等在线影像服务时，需要记录：

| 字段 | 是否必需 | 说明 |
| --- | --- | --- |
| 服务名称 | 是 | 例如天地图影像、SuperMap Online 影像等 |
| 服务类型 | 是 | `supermap`、`url_template`、`wmts` |
| URL | 是 | 完整服务地址或瓦片模板 |
| token/key | 是 | 记录参数名、有效期、归属账号 |
| 覆盖范围 | 是 | 全球、中国、武汉、指定区域 |
| 坐标/切片体系 | 是 | WGS84、WebMercator、CGCS2000、GCJ-02 等 |
| 影像类型 | 是 | 卫星影像、矢量地图、注记、混合图 |
| 授权 | 是 | 是否允许比赛演示、截图、录屏使用 |
| 浏览器访问 | 是 | 必须能从 `localhost:5173` 调用 |
| 最大级别 | 建议 | 用于设置 `maximum_level` |
| 署名 | 建议 | 如 PPT 或报告需要标注数据来源 |

## 配置写法

正式运行时填写本机配置：

```text
config/supermap_services.local.json
```

该文件不进入 Git。仓库里的模板只保留占位符。

天地图影像 WMTS 推荐写法：

```json
{
  "services": {
    "online_basemap": {
      "name": "天地图影像底图（大范围三维背景）",
      "url": "https://t0.tianditu.gov.cn/img_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=img&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk={token}",
      "token": "填入本机天地图 API 密钥",
      "type": "url_template",
      "provider": "url_template",
      "status": "configured",
      "usage": "regional_3d_context_background_only",
      "minimum_level": 1,
      "maximum_level": 18,
      "alpha": 0.82,
      "regional_preview_level": 13,
      "regional_preview_max_tiles": 36,
      "regional_preview_alpha": 0.92,
      "credit": "天地图影像"
    }
  }
}
```

前端会把 `url` 中的 `{token}`、`{tk}` 或 `{api_key}` 替换为配置中的 `token`、`api_key` 或 `key` 字段。

SuperMap iServer 地图服务写法：

```json
{
  "provider": "supermap",
  "url": "https://.../iserver/services/map-xxx/rest/maps/xxx"
}
```

普通 XYZ 瓦片模板写法：

```json
{
  "provider": "url_template",
  "url": "https://.../{z}/{x}/{y}.png"
}
```

## 验收步骤

1. 复制合适模板为 `config/supermap_services.local.json`。
2. 填写 `services.online_basemap.token`。
3. 启动后端和前端。
4. 打开 `http://localhost:5173`。
5. 确认场景状态或 DOM 证据显示：

```text
online basemap: installed
data-online-basemap-status="installed"
```

6. 切到大范围三维视角。
7. 确认珞珈山区域外能显示在线影像。
8. 确认珞珈山任务区仍由本地 DEM/正射影像/建筑物覆盖。
9. 保存截图：

```text
docs/delivery/screenshots/r9_online_imagery_regional_3d_context.png
```

## 答辩口径

可以说：

```text
平台支持加载在线影像底图作为大范围动态背景；视觉自主导航验证仍以本地珞珈山高精度 DEM、正射影像和建筑物数据为准。
```

不要说：

```text
在线底图已经作为高精度视觉导航输入。
在线影像替代了本地正射影像用于特征匹配。
```
