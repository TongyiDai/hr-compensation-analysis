#!/usr/bin/env python3
"""Render the compensation-analysis Geometry Board scenes as local SVG files."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

W, H = 1200, 675
BLACK, GRAY, GUIDE, LIGHT, FILL, BLUE = "#111111", "#666666", "#B8B8B8", "#E8E8E8", "#F5F5F5", "#2F6BFF"
FONT = "-apple-system,BlinkMacSystemFont,'PingFang SC','Noto Sans CJK SC',sans-serif"


def txt(x, y, value, size=16, fill=BLACK, anchor="middle", weight=400):
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="{FONT}" font-size="{size}px" font-weight="{weight}" fill="{fill}">{html.escape(value)}</text>'


def line(x1, y1, x2, y2, color=BLACK, width=1.5, arrow=False, dashed=False):
    marker = ' marker-end="url(#arrow)"' if arrow else ""
    dash = ' stroke-dasharray="5 7"' if dashed else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"{dash}{marker}/>'


def path(d, color=BLACK, width=1.5, arrow=False, dashed=False):
    marker = ' marker-end="url(#arrow)"' if arrow else ""
    dash = ' stroke-dasharray="5 7"' if dashed else ""
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"{dash}{marker}/>'


def heading(scene):
    intent = scene["intent"]
    return "".join([txt(96, 78, intent["core_message"], 32, BLACK, "start", 650), txt(96, 108, intent["subtitle"], 14, GRAY, "start"), line(96, 136, 1104, 136, LIGHT, 1)])


def pay_position(scene):
    body = [heading(scene), txt(185, 214, "带宽下限", 14, GRAY), txt(600, 214, "带宽中点", 14, BLACK, weight=650), txt(1015, 214, "带宽上限", 14, GRAY)]
    body.extend([line(180, 252, 1020, 252, GUIDE, 1), line(180, 232, 180, 276, BLACK, 1.5), line(600, 222, 600, 282, BLUE, 2), line(1020, 232, 1020, 276, BLACK, 1.5)])
    rows = [(336, 365, "P-001", "0.90× 中点"), (438, 622, "P-002", "1.03× 中点"), (540, 850, "P-003", "1.15× 中点")]
    for y, x, ref, note in rows:
        body.extend([txt(122, y + 5, ref, 14, GRAY, "start", 600), line(180, y, 1020, y, LIGHT, 1), line(180, y - 12, 180, y + 12, GUIDE, 1), line(600, y - 12, 600, y + 12, LIGHT, 1), line(1020, y - 12, 1020, y + 12, GUIDE, 1), '<circle cx="%s" cy="%s" r="10" fill="%s"/>' % (x, y, BLUE if ref == "P-002" else "#FFFFFF"), '<circle cx="%s" cy="%s" r="10" fill="none" stroke="%s" stroke-width="1.5"/>' % (x, y, BLUE if ref == "P-002" else BLACK), txt(x, y + 36, note, 12, GRAY)])
    body.extend([txt(600, 618, "每一条记录先回到所属带宽，再进入人工讨论", 14, BLACK, weight=600), '<circle cx="600" cy="590" r="6" fill="#2F6BFF"/>'])
    return "".join(body)


def review_lens(scene):
    body = [heading(scene), '<circle cx="600" cy="366" r="88" fill="#2F6BFF"/>', txt(600, 358, "分析", 20, "#FFFFFF", weight=650), txt(600, 385, "底稿", 20, "#FFFFFF", weight=650)]
    lenses = [(340, 266, "数据完整", "币种 · 周期"), (860, 266, "带宽映射", "岗位 · 职级"), (340, 474, "可比范围", "地点 · 样本"), (860, 474, "市场时效", "来源 · 日期")]
    for x, y, label, detail in lenses:
        body.extend(['<rect x="%s" y="%s" width="156" height="72" fill="none" stroke="#222222" stroke-width="1.5"/>' % (x - 78, y - 36), txt(x, y - 4, label, 16, BLACK, weight=650), txt(x, y + 22, detail, 12, GRAY), path(f"M {x + (82 if x < 600 else -82)} {y} C {500 if x < 600 else 700} {y} {510 if x < 600 else 690} 366 {510 if x < 600 else 690} 366", BLACK, 1.5, True)])
    body.extend([line(600, 230, 600, 254, GUIDE, 1, dashed=True), line(600, 478, 600, 502, GUIDE, 1, dashed=True), txt(600, 594, "少一层核验，数字就不应被当作结论", 14, GRAY)])
    return "".join(body)


def exception_path(scene):
    body = [heading(scene), '<circle cx="230" cy="355" r="52" fill="#FFFFFF" stroke="#222222" stroke-width="1.5"/>', txt(230, 350, "异常", 18, BLACK, weight=650), txt(230, 375, "信号", 18, BLACK, weight=650)]
    body.extend([path("M 285 355 C 390 355 400 250 510 250", BLACK, 1.5, True), path("M 285 355 C 390 355 400 355 510 355", BLACK, 1.5, True), path("M 285 355 C 390 355 400 460 510 460", BLACK, 1.5, True)])
    checks = [(565, 250, "数据核验", "币种 · 周期"), (565, 355, "带宽核验", "映射 · 版本"), (565, 460, "可比核验", "范围 · 样本")]
    for x, y, label, detail in checks:
        body.extend(['<rect x="%s" y="%s" width="160" height="66" fill="#F5F5F5" stroke="#222222" stroke-width="1.2"/>' % (x - 80, y - 33), txt(x, y - 2, label, 16, BLACK, weight=650), txt(x, y + 20, detail, 12, GRAY), path(f"M 650 {y} C 720 {y} 745 355 802 355", GUIDE, 1.2, True)])
    body.extend(['<circle cx="870" cy="355" r="72" fill="#2F6BFF"/>', txt(870, 350, "人工", 19, "#FFFFFF", weight=650), txt(870, 377, "复核", 19, "#FFFFFF", weight=650), line(946, 355, 1042, 355, BLACK, 1.5, True), '<rect x="1042" y="324" width="92" height="62" fill="none" stroke="#222222" stroke-width="1.5"/>', txt(1088, 352, "确认", 16, BLACK, weight=650), txt(1088, 374, "后续动作", 12, GRAY), txt(600, 584, "异常分流，避免把一个数字直接写成结论", 14, GRAY)])
    return "".join(body)


def human_boundary(scene):
    body = [heading(scene), '<rect x="112" y="200" width="452" height="322" fill="#F5F5F5"/>', '<rect x="704" y="200" width="384" height="322" fill="#FFFFFF" stroke="#E8E8E8" stroke-width="1"/>', line(640, 188, 640, 540, GUIDE, 1, dashed=True), txt(338, 232, "Agent", 15, GRAY, weight=650), txt(896, 232, "薪酬负责人", 15, GRAY, weight=650)]
    body.extend(['<circle cx="260" cy="350" r="56" fill="#FFFFFF" stroke="#222222" stroke-width="1.5"/>', txt(260, 345, "整理", 17, BLACK, weight=650), txt(260, 370, "计算", 17, BLACK, weight=650), line(330, 350, 462, 350, BLACK, 1.5, True), '<rect x="466" y="314" width="88" height="72" fill="#FFFFFF" stroke="#222222" stroke-width="1.5"/>', txt(510, 344, "标记", 16, BLACK, weight=650), txt(510, 367, "待核项", 12, GRAY), line(554, 350, 616, 350, BLACK, 1.5, True), '<circle cx="640" cy="350" r="17" fill="#2F6BFF"/>', txt(640, 416, "复核点", 13, BLUE, weight=650), line(664, 350, 756, 350, BLACK, 1.5, True), '<circle cx="870" cy="350" r="72" fill="#FFFFFF" stroke="#222222" stroke-width="1.5"/>', '<circle cx="870" cy="350" r="47" fill="none" stroke="#E8E8E8" stroke-width="1"/>', txt(870, 343, "确认规则", 16, BLACK, weight=650), txt(870, 369, "解释 · 决定", 13, GRAY), txt(338, 488, "只交付数据与提示", 13, GRAY), txt(896, 488, "承担最终薪酬责任", 13, GRAY)])
    return "".join(body)


def render(scene):
    composition = scene["intent"]["composition"]
    functions = {"axis-flow": pay_position, "radial-center": review_lens, "dot-filter": exception_path, "section-space": human_boundary}
    body = functions[composition](scene)
    title = html.escape(scene["intent"]["core_message"])
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<title>{title}</title><desc>Geometry Board for 薪酬结构分析.</desc>
<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto" markerUnits="strokeWidth"><path d="M 0 0 L 8 4 L 0 8 z" fill="#111111"/></marker></defs>
<rect width="1200" height="675" fill="#FFFFFF"/>{body}</svg>\n'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scene_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for scene_path in sorted(args.scene_dir.glob("*.json")):
        scene = json.loads(scene_path.read_text(encoding="utf-8"))
        output = args.output_dir / f"{scene_path.stem}.svg"
        output.write_text(render(scene), encoding="utf-8")
        print(output)


if __name__ == "__main__":
    main()
