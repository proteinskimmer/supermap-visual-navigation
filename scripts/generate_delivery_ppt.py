from __future__ import annotations

import html
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "delivery" / "ppt"
SHOT_DIR = ROOT / "docs" / "delivery" / "screenshots"
OUT = OUT_DIR / "final_presentation.pptx"

SLIDE_W = 13.333
SLIDE_H = 7.5
EMU = 914400

C = {
    "navy": "102235",
    "blue": "1F5E8C",
    "cyan": "22B8CF",
    "teal": "1F9D8A",
    "green": "2AA876",
    "amber": "F4A261",
    "red": "E76F51",
    "ink": "172033",
    "muted": "5C6B7A",
    "line": "D7E1EA",
    "pale": "EEF5F9",
    "white": "FFFFFF",
}


def e(v: float) -> int:
    return int(round(v * EMU))


def esc(text: str) -> str:
    return html.escape(str(text), quote=True)


def text_run(text: str, size: int, color: str, bold: bool = False) -> str:
    b = ' b="1"' if bold else ""
    return (
        f'<a:r><a:rPr lang="zh-CN" sz="{size * 100}"{b}>'
        f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
        f'<a:latin typeface="Microsoft YaHei"/><a:ea typeface="Microsoft YaHei"/>'
        f'</a:rPr><a:t>{esc(text)}</a:t></a:r>'
    )


def paragraphs(text: str, size: int, color: str, bold: bool = False) -> str:
    parts = []
    for line in str(text).split("\n"):
        if not line:
            parts.append("<a:p/>")
            continue
        parts.append(
            "<a:p>"
            f"{text_run(line, size, color, bold)}"
            '<a:endParaRPr lang="zh-CN"/></a:p>'
        )
    return "".join(parts)


def text_box(shape_id: int, name: str, x: float, y: float, w: float, h: float, text: str,
             size: int = 14, color: str = C["ink"], bold: bool = False,
             align: str | None = None) -> str:
    align_xml = f' algn="{align}"' if align else ""
    ps = []
    for line in str(text).split("\n"):
        ps.append(
            f"<a:p><a:pPr{align_xml}/>{text_run(line, size, color, bold)}"
            '<a:endParaRPr lang="zh-CN"/></a:p>'
        )
    return f"""
    <p:sp>
      <p:nvSpPr><p:cNvPr id="{shape_id}" name="{esc(name)}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="{e(x)}" y="{e(y)}"/><a:ext cx="{e(w)}" cy="{e(h)}"/></a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>
      <p:txBody><a:bodyPr wrap="square" lIns="0" tIns="0" rIns="0" bIns="0"><a:spAutoFit/></a:bodyPr><a:lstStyle/>
        {''.join(ps)}
      </p:txBody>
    </p:sp>
    """


def rect(shape_id: int, name: str, x: float, y: float, w: float, h: float,
         fill: str = "FFFFFF", line: str = "D7E1EA", radius: str = "roundRect") -> str:
    return f"""
    <p:sp>
      <p:nvSpPr><p:cNvPr id="{shape_id}" name="{esc(name)}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="{e(x)}" y="{e(y)}"/><a:ext cx="{e(w)}" cy="{e(h)}"/></a:xfrm>
        <a:prstGeom prst="{radius}"><a:avLst/></a:prstGeom>
        <a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>
        <a:ln><a:solidFill><a:srgbClr val="{line}"/></a:solidFill></a:ln>
      </p:spPr>
    </p:sp>
    """


def card(shapes: list[str], sid: int, title: str, body: str, x: float, y: float, w: float, h: float,
         fill: str = "FFFFFF") -> int:
    shapes.append(rect(sid, f"card-{sid}", x, y, w, h, fill, C["line"]))
    sid += 1
    shapes.append(text_box(sid, f"title-{sid}", x + 0.18, y + 0.14, w - 0.36, 0.28, title, 13, C["ink"], True))
    sid += 1
    shapes.append(text_box(sid, f"body-{sid}", x + 0.18, y + 0.48, w - 0.36, h - 0.6, body, 9, C["muted"]))
    return sid + 1


def bullet_text(items: list[str]) -> str:
    return "\n".join(f"• {item}" for item in items)


def metric(shapes: list[str], sid: int, value: str, label: str, x: float, y: float, w: float,
           color: str = C["blue"]) -> int:
    shapes.append(rect(sid, f"metric-{sid}", x, y, w, 0.78, "FFFFFF", C["line"]))
    sid += 1
    shapes.append(text_box(sid, f"metric-value-{sid}", x, y + 0.12, w, 0.26, value, 19, color, True, "ctr"))
    sid += 1
    shapes.append(text_box(sid, f"metric-label-{sid}", x + 0.05, y + 0.49, w - 0.1, 0.2, label, 7, C["muted"], False, "ctr"))
    return sid + 1


def image_pic(pic_id: int, name: str, rid: str, x: float, y: float, w: float, h: float) -> str:
    return f"""
    <p:pic>
      <p:nvPicPr><p:cNvPr id="{pic_id}" name="{esc(name)}"/><p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr>
      <p:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>
      <p:spPr><a:xfrm><a:off x="{e(x)}" y="{e(y)}"/><a:ext cx="{e(w)}" cy="{e(h)}"/></a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>
    </p:pic>
    """


def flow(shapes: list[str], sid: int, items: list[str], x: float, y: float, w: float) -> int:
    gap = 0.08
    box_w = (w - gap * (len(items) - 1)) / len(items)
    for i, item in enumerate(items):
        bx = x + i * (box_w + gap)
        shapes.append(rect(sid, f"flow-{sid}", bx, y, box_w, 0.68, "EAF2FA" if i % 2 == 0 else "EAF7F5", "9BC2E6"))
        sid += 1
        shapes.append(text_box(sid, f"flow-text-{sid}", bx + 0.06, y + 0.2, box_w - 0.12, 0.22, item, 8, C["ink"], True, "ctr"))
        sid += 1
        if i < len(items) - 1:
            shapes.append(text_box(sid, f"flow-arrow-{sid}", bx + box_w - 0.01, y + 0.25, 0.18, 0.2, ">", 10, C["muted"], True, "ctr"))
            sid += 1
    return sid


slides = [
    {
        "title": "基于 SuperMap GIS 底座的\n低空视觉自主导航与三维仿真规划系统",
        "subtitle": "UAV 影像帧 -> ORB 视觉定位 -> 后端融合导航状态 -> SuperMap 三维连续飞行",
        "image": "frontend_luojia_scene_headless.png",
        "kind": "cover",
    },
    {
        "title": "低空任务不能只看航线",
        "subtitle": "核心问题是：无人机如何根据视觉影像判断自己在哪里，并解释定位质量。",
        "cards": [
            ("二维航线不足以解释导航", "固定航线动画只能说明路线存在，无法说明 UAV 视觉帧如何更新当前位置。"),
            ("低空空间约束复杂", "地形、建筑、风险区和临时事件共同影响任务安全。"),
            ("需要可量化证据", "输出视觉位置、置信度、误差半径、轨迹偏差和回退帧。"),
        ],
        "flow": ["UAV 影像帧", "视觉地理重定位", "融合导航状态", "三维连续飞行", "质量报告"],
    },
    {
        "title": "项目定位与边界",
        "subtitle": "面向低空巡检、应急推演和训练验证的软件仿真系统。",
        "bullets": [
            "项目定位：视觉自主导航仿真平台，聚焦 UAV 影像帧、视觉定位、融合状态和三维演示。",
            "能力边界：不接真实飞控，不下发真实飞行控制指令。",
            "数据边界：当前 UAV 帧为半真实演示帧，不等同于真实飞行相机数据。",
            "场景边界：SuperMap 三维场景用于空间关系验证，不包装为精细倾斜摄影级建模。",
        ],
        "side_cards": [
            ("推荐表述", "v0.5a 已形成 ORB 真实特征匹配最小原型，并可驱动后端融合导航时间线。"),
            ("避免表述", "已完成真实飞行视觉自主导航；系统能够直接控制真实无人机。"),
        ],
    },
    {
        "title": "总体闭环",
        "subtitle": "后端统一生成导航状态，前端只负责消费和展示。",
        "flow": ["珞珈山 GIS", "参考航线", "UAV 影像帧", "ORB 匹配", "视觉位置", "融合位置", "三维飞行"],
        "cards": [
            ("后端权威时间线", "VisualNavigationService 输出 reference、visual、fused、telemetry、mode 和 event。"),
            ("前端指挥舱", "SuperMapScene、视觉面板、遥测、事件流和报告消费同一条时间线。"),
            ("支撑服务", "航线规划、风险校验和动态重规划围绕 fused_position 提供安全约束。"),
        ],
    },
    {
        "title": "SuperMap GIS 底座",
        "subtitle": "珞珈山 scene/map/data 服务已发布并通过脚本门禁。",
        "image": "frontend_luojia_scene_headless.png",
        "bullets": [
            "iDesktopX 构建珞珈山工作空间。",
            "iServer 发布 3D/map/data 服务。",
            "iClient3D 承载正射影像、DEM、建筑和轨迹。",
            "后端实时探测 SuperMap 服务状态。",
        ],
        "metrics": [("3", "scene/map/data verified"), ("4", "珞珈山图层"), ("0", "真实飞控接入")],
    },
    {
        "title": "视觉定位 v0.5a：OpenCV ORB",
        "subtitle": "半真实 UAV 帧与候选合成视图进行真实特征匹配。",
        "bullets": [
            "半真实 UAV 帧：航向旋转、FOV 裁剪、镜头畸变、光照扰动。",
            "候选合成视图：正射影像瓦片结合 DEM、建筑和相机上下文。",
            "ORB 关键点和描述子，BFMatcher/Hamming 匹配。",
            "RANSAC 估计几何关系，输出位置、置信度、误差半径。",
        ],
        "metrics": [("6/6", "半真实帧定位成功"), ("27", "ORB 视觉观测"), ("0.775", "平均置信度"), ("40.6m", "平均误差半径")],
    },
    {
        "title": "后端融合导航状态",
        "subtitle": "fused_position 是三维无人机和遥测面板的唯一权威位置。",
        "cards": [
            ("reference_position", "参考航线位置，用于任务目标、偏差计算和安全约束。"),
            ("visual_position", "来自 ORB 视觉定位，包含置信度、误差半径和匹配证据。"),
            ("fused_position", "后端融合后的导航位置，驱动 UAV 连续飞行和遥测状态。"),
        ],
        "flow": ["距离参数化", "圆角平滑", "视觉修正渐入", "限速与航向门禁", "连续播放"],
        "metrics": [("14.48°", "最大单步航向变化"), ("9.03m/s", "最大速度"), ("0", "硬转向次数")],
    },
    {
        "title": "视觉自主导航指挥舱",
        "subtitle": "三维飞行、实时影像、遥测、事件流和报告同步推进。",
        "image": "frontend_luojia_scene_headless.png",
        "cards": [
            ("核心展示", "中央三维场景展示参考轨迹与融合轨迹；右侧展示 UAV 影像、飞行遥测和视觉定位状态。"),
            ("演示价值", "无人机不是按固定路线动画播放，而是由后端融合导航时间线驱动连续飞行。"),
        ],
    },
    {
        "title": "规划、风险与重规划支撑",
        "subtitle": "航线规划是视觉自主导航任务的安全约束服务。",
        "image": "v05_report_page_summary_route_risk_profile.png",
        "bullets": [
            "生成最短、最安全、综合最优三类参考航线。",
            "输出风险评分、风险航段、风险原因和高程剖面。",
            "基于当前 fused_position 判断偏航、接近风险区或进入复核状态。",
            "临时风险出现时，从当前融合位置接续重规划。",
            "报告统一汇总航线、风险、视觉导航质量和事件日志。",
        ],
    },
    {
        "title": "当前验收结果",
        "subtitle": "v0.5a 软件仿真链路已通过一键门禁。",
        "metrics": [
            ("12", "backend tests passed"), ("6/6", "ORB 定位成功"), ("36", "导航时间线帧"),
            ("27", "视觉观测帧"), ("0.775", "平均置信度"), ("40.6m", "平均误差半径"),
            ("2.1m", "融合轨迹平均偏差"), ("8.6m", "终点误差"), ("0", "回退帧"),
            ("demo", "quality verified"),
        ],
        "note": "门禁覆盖：前端构建、后端 pytest/smoke、ORB 证据生成、导航/报告接口、Luojia DOM 证据和截图证据。",
    },
    {
        "title": "项目创新点",
        "subtitle": "从“航线展示”升级为“视觉定位驱动的导航状态仿真”。",
        "cards": [
            ("SuperMap 三维空间底座", "scene/map/data 服务承载影像、DEM、建筑、风险和轨迹。"),
            ("ORB 视觉定位入链", "真实特征匹配结果进入 visual_position 并参与 fused_position。"),
            ("后端权威状态机", "前端不自行推演 UAV 状态，统一消费后端导航时间线。"),
            ("可量化质量报告", "输出置信度、误差半径、轨迹偏差、终点误差和回退帧。"),
            ("风险重规划接续", "临时风险从当前 fused_position 接续重规划。"),
            ("Provider 可扩展", "后续可接入 SIFT、LoFTR、LightGlue 或外部深度匹配器。"),
        ],
    },
    {
        "title": "总结与下一步",
        "subtitle": "已具备比赛演示闭环，下一步补真实数据和彩排证据。",
        "bullets": [
            "已完成：SuperMap 珞珈山 scene/map/data、ORB 半真实视觉定位、后端融合导航时间线、前端三维指挥舱和质量报告。",
            "正在收尾：PPT、视频脚本、截图证据和完整彩排记录。",
            "后续扩展：真实 UAV 相机数据、SIFT/LoFTR/LightGlue provider、更真实的相机标定和误差评估。",
            "长期方向：在安全审批和硬件条件满足后，再研究真实飞控对接。",
        ],
        "note": "答辩底线：软件仿真验证，不接真实飞控；半真实 UAV 帧，不等同真实飞行数据。",
    },
]


def make_slide_xml(idx: int, spec: dict, media_rels: list[tuple[str, str]]) -> str:
    shapes: list[str] = []
    sid = 2

    if spec.get("kind") == "cover":
        img_name = spec.get("image")
        if img_name and (SHOT_DIR / img_name).exists():
            rid = "rId2"
            media_rels.append((rid, img_name))
            shapes.append(image_pic(sid, img_name, rid, 0, 0, SLIDE_W, SLIDE_H))
            sid += 1
        shapes.append(rect(sid, "cover-overlay", 0, 0, SLIDE_W, SLIDE_H, C["navy"], C["navy"], "rect"))
        sid += 1
        shapes.append(text_box(sid, "cover-title", 0.65, 0.95, 10.3, 1.15, spec["title"], 30, C["white"], True))
        sid += 1
        shapes.append(text_box(sid, "cover-subtitle", 0.68, 2.25, 10.1, 0.35, spec["subtitle"], 13, "DDEAF2"))
        sid += 1
        for i, label in enumerate(["软件仿真验证", "不接真实飞控", "v0.5a ORB 门禁通过"]):
            shapes.append(rect(sid, f"pill-{i}", 0.72 + i * 1.75, 2.95, 1.55 if i < 2 else 2.0, 0.36, [C["teal"], C["red"], C["blue"]][i], [C["teal"], C["red"], C["blue"]][i]))
            sid += 1
            shapes.append(text_box(sid, f"pill-text-{i}", 0.78 + i * 1.75, 3.04, 1.42 if i < 2 else 1.85, 0.15, label, 8, C["white"], True, "ctr"))
            sid += 1
    else:
        shapes.append(rect(sid, "top-line", 0, 0, SLIDE_W, 0.16, C["blue"], C["blue"], "rect"))
        sid += 1
        shapes.append(text_box(sid, "title", 0.45, 0.34, 12.1, 0.4, spec["title"], 24, C["ink"], True))
        sid += 1
        shapes.append(text_box(sid, "subtitle", 0.48, 0.82, 11.7, 0.25, spec.get("subtitle", ""), 9, C["muted"]))
        sid += 1

        if "flow" in spec:
            sid = flow(shapes, sid, spec["flow"], 0.65, 1.25 if idx in (4,) else 4.65, 12.0 if idx == 4 else 11.6)

        if "cards" in spec:
            cards = spec["cards"]
            if idx in (2, 4):
                for i, (t, b) in enumerate(cards):
                    sid = card(shapes, sid, t, b, 0.65 + i * 4.2, 1.45 if idx == 2 else 2.75, 3.75, 1.7, "FFFFFF")
            elif idx == 11:
                for i, (t, b) in enumerate(cards):
                    sid = card(shapes, sid, t, b, 0.75 + (i % 3) * 4.05, 1.35 + (i // 3) * 2.0, 3.7, 1.35, "FFFFFF" if i != 1 else "ECF8F5")
            elif idx == 7:
                for i, (t, b) in enumerate(cards):
                    sid = card(shapes, sid, t, b, 0.75 + i * 4.1, 1.35, 3.6, 1.28, "ECF8F5" if i == 2 else "FFFFFF")
            else:
                x = 8.35 if "image" in spec else 8.45
                for i, (t, b) in enumerate(cards):
                    sid = card(shapes, sid, t, b, x, 1.35 + i * 2.0, 3.95, 1.55, "ECF8F5" if i == 1 else "FFFFFF")

        if "bullets" in spec:
            has_image = "image" in spec and idx != 5
            x, y, w, h = (0.85, 1.35, 6.1, 3.9) if has_image else (0.8, 1.35, 7.2, 4.1)
            if idx == 12:
                x, y, w, h = 0.85, 1.35, 8.0, 3.6
            shapes.append(text_box(sid, "bullets", x, y, w, h, bullet_text(spec["bullets"]), 14 if idx != 3 else 13, C["ink"]))
            sid += 1

        if "side_cards" in spec:
            for i, (t, b) in enumerate(spec["side_cards"]):
                sid = card(shapes, sid, t, b, 8.45, 1.4 + i * 1.8, 3.95, 1.45, "ECF8F5" if i == 0 else "FFF2EE")

        if "image" in spec:
            img_name = spec["image"]
            if (SHOT_DIR / img_name).exists():
                rid = "rId2"
                media_rels.append((rid, img_name))
                if idx in (5, 8):
                    shapes.append(image_pic(sid, img_name, rid, 0.65, 1.22, 7.3, 4.85))
                else:
                    shapes.append(image_pic(sid, img_name, rid, 7.3, 1.35, 5.25, 4.2))
                sid += 1

        if "metrics" in spec:
            metrics = spec["metrics"]
            colors = [C["green"], C["blue"], C["teal"], C["amber"], C["red"]]
            if idx == 10:
                for i, (v, lab) in enumerate(metrics):
                    row, col = divmod(i, 5)
                    sid = metric(shapes, sid, v, lab, 0.75 + col * 2.45, 1.45 + row * 1.25, 1.8, colors[i % len(colors)])
            elif idx == 6:
                for i, (v, lab) in enumerate(metrics):
                    sid = metric(shapes, sid, v, lab, 0.9 + i * 1.75, 5.4, 1.55, colors[i % len(colors)])
            elif idx == 7:
                for i, (v, lab) in enumerate(metrics):
                    sid = metric(shapes, sid, v, lab, 2.4 + i * 2.6, 5.15, 2.0, colors[i % len(colors)])
            else:
                for i, (v, lab) in enumerate(metrics):
                    sid = metric(shapes, sid, v, lab, 8.45 + i * 1.4, 4.25, 1.2, colors[i % len(colors)])

        if "note" in spec:
            fill = "FFF2EE" if idx == 12 else "FFFFFF"
            sid = card(shapes, sid, "说明", spec["note"], 1.0 if idx == 10 else 9.15, 4.75 if idx == 10 else 1.45, 11.3 if idx == 10 else 3.35, 1.25 if idx == 10 else 2.1, fill)

        shapes.append(text_box(sid, "footer", 10.75, 7.08, 2.15, 0.18, f"视觉自主导航仿真系统  |  {idx}/12", 7, "8CA0AF", False, "r"))

    sp_tree = """
    <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
    <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
    """ + "\n".join(shapes)
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
       xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:bg><p:bgPr><a:solidFill><a:srgbClr val="F7FAFC"/></a:solidFill><a:effectLst/></p:bgPr></p:bg>
    <p:spTree>{sp_tree}</p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>"""


def content_types() -> str:
    slide_overrides = "\n".join(
        f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
        for i in range(1, len(slides) + 1)
    )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Default Extension="png" ContentType="image/png"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
  <Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
  <Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
  <Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
  {slide_overrides}
</Types>"""


ROOT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>"""


def presentation_xml() -> str:
    ids = "\n".join(
        f'<p:sldId id="{255 + i}" r:id="rId{i + 1}"/>' for i in range(1, len(slides) + 1)
    )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
 xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>
  <p:sldIdLst>{ids}</p:sldIdLst>
  <p:sldSz cx="{e(SLIDE_W)}" cy="{e(SLIDE_H)}" type="wide"/>
  <p:notesSz cx="6858000" cy="9144000"/>
  <p:defaultTextStyle><a:defPPr><a:defRPr lang="zh-CN"/></a:defPPr></p:defaultTextStyle>
</p:presentation>"""


def presentation_rels() -> str:
    rels = ['<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>']
    for i in range(1, len(slides) + 1):
        rels.append(
            f'<Relationship Id="rId{i + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i}.xml"/>'
        )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  {' '.join(rels)}
</Relationships>"""


SLIDE_MASTER = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
 xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld><p:spTree>
    <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
    <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
  </p:spTree></p:cSld>
  <p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
  <p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>
  <p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles>
</p:sldMaster>"""

SLIDE_MASTER_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>
</Relationships>"""

SLIDE_LAYOUT = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
 xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank" preserve="1">
  <p:cSld name="Blank"><p:spTree>
    <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
    <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
  </p:spTree></p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sldLayout>"""

SLIDE_LAYOUT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>
</Relationships>"""

THEME = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="DeliveryTheme">
  <a:themeElements>
    <a:clrScheme name="Delivery"><a:dk1><a:srgbClr val="172033"/></a:dk1><a:lt1><a:srgbClr val="FFFFFF"/></a:lt1><a:dk2><a:srgbClr val="102235"/></a:dk2><a:lt2><a:srgbClr val="F7FAFC"/></a:lt2><a:accent1><a:srgbClr val="1F5E8C"/></a:accent1><a:accent2><a:srgbClr val="1F9D8A"/></a:accent2><a:accent3><a:srgbClr val="22B8CF"/></a:accent3><a:accent4><a:srgbClr val="F4A261"/></a:accent4><a:accent5><a:srgbClr val="E76F51"/></a:accent5><a:accent6><a:srgbClr val="5C6B7A"/></a:accent6><a:hlink><a:srgbClr val="1F5E8C"/></a:hlink><a:folHlink><a:srgbClr val="5C6B7A"/></a:folHlink></a:clrScheme>
    <a:fontScheme name="YaHei"><a:majorFont><a:latin typeface="Microsoft YaHei"/><a:ea typeface="Microsoft YaHei"/></a:majorFont><a:minorFont><a:latin typeface="Microsoft YaHei"/><a:ea typeface="Microsoft YaHei"/></a:minorFont></a:fontScheme>
    <a:fmtScheme name="Default"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst><a:lnStyleLst><a:ln w="6350"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst><a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst><a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst></a:fmtScheme>
  </a:themeElements>
</a:theme>"""


def slide_rels(media_rels: list[tuple[str, str]]) -> str:
    rels = ['<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>']
    for rid, img_name in media_rels:
        rels.append(f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/{esc(img_name)}"/>')
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  {' '.join(rels)}
</Relationships>"""


def core_xml() -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
 xmlns:dc="http://purl.org/dc/elements/1.1/"
 xmlns:dcterms="http://purl.org/dc/terms/"
 xmlns:dcmitype="http://purl.org/dc/dcmitype/"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>基于 SuperMap GIS 底座的低空视觉自主导航与三维仿真规划系统</dc:title>
  <dc:creator>supermap_project</dc:creator>
  <cp:lastModifiedBy>supermap_project</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>
</cp:coreProperties>"""


APP_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
 xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Microsoft PowerPoint</Application>
  <PresentationFormat>On-screen Show (16:9)</PresentationFormat>
  <Slides>12</Slides>
  <Company>supermap_project</Company>
</Properties>"""


def write_pptx() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tmp = OUT_DIR / "_pptx_build"
    if tmp.exists():
        shutil.rmtree(tmp)
    (tmp / "_rels").mkdir(parents=True)
    (tmp / "docProps").mkdir()
    (tmp / "ppt" / "_rels").mkdir(parents=True)
    (tmp / "ppt" / "slides" / "_rels").mkdir(parents=True)
    (tmp / "ppt" / "slideMasters" / "_rels").mkdir(parents=True)
    (tmp / "ppt" / "slideLayouts" / "_rels").mkdir(parents=True)
    (tmp / "ppt" / "theme").mkdir(parents=True)
    (tmp / "ppt" / "media").mkdir(parents=True)

    (tmp / "[Content_Types].xml").write_text(content_types(), encoding="utf-8")
    (tmp / "_rels" / ".rels").write_text(ROOT_RELS, encoding="utf-8")
    (tmp / "docProps" / "core.xml").write_text(core_xml(), encoding="utf-8")
    (tmp / "docProps" / "app.xml").write_text(APP_XML, encoding="utf-8")
    (tmp / "ppt" / "presentation.xml").write_text(presentation_xml(), encoding="utf-8")
    (tmp / "ppt" / "_rels" / "presentation.xml.rels").write_text(presentation_rels(), encoding="utf-8")
    (tmp / "ppt" / "slideMasters" / "slideMaster1.xml").write_text(SLIDE_MASTER, encoding="utf-8")
    (tmp / "ppt" / "slideMasters" / "_rels" / "slideMaster1.xml.rels").write_text(SLIDE_MASTER_RELS, encoding="utf-8")
    (tmp / "ppt" / "slideLayouts" / "slideLayout1.xml").write_text(SLIDE_LAYOUT, encoding="utf-8")
    (tmp / "ppt" / "slideLayouts" / "_rels" / "slideLayout1.xml.rels").write_text(SLIDE_LAYOUT_RELS, encoding="utf-8")
    (tmp / "ppt" / "theme" / "theme1.xml").write_text(THEME, encoding="utf-8")

    copied = set()
    for i, spec in enumerate(slides, start=1):
        rels: list[tuple[str, str]] = []
        xml = make_slide_xml(i, spec, rels)
        (tmp / "ppt" / "slides" / f"slide{i}.xml").write_text(xml, encoding="utf-8")
        (tmp / "ppt" / "slides" / "_rels" / f"slide{i}.xml.rels").write_text(slide_rels(rels), encoding="utf-8")
        for _, img_name in rels:
            if img_name not in copied:
                src = SHOT_DIR / img_name
                if src.exists():
                    shutil.copy2(src, tmp / "ppt" / "media" / img_name)
                    copied.add(img_name)

    if OUT.exists():
        OUT.unlink()
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for file in tmp.rglob("*"):
            if file.is_file():
                z.write(file, file.relative_to(tmp).as_posix())
    shutil.rmtree(tmp)


if __name__ == "__main__":
    write_pptx()
    print(OUT)
