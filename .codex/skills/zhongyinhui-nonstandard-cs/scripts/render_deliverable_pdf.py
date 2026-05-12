#!/usr/bin/env python3
"""Render Zhongyinhui CS Markdown deliverables to a clean PDF document.

This renderer deliberately keeps the layout conservative: normal A4 document,
clear headings, readable paragraphs, simple lists, and a light summary block.
It supports the compact Markdown subset used by this skill's templates.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


PAGE_WIDTH, PAGE_HEIGHT = A4

COLORS = {
    "ink": "#1F2937",
    "body": "#374151",
    "muted": "#6B7280",
    "line": "#D1D5DB",
    "soft": "#F8FAFC",
    "blue": "#1F4E79",
    "yellow": "#B45309",
    "green": "#047857",
    "red": "#B91C1C",
}


def color(name: str):
    return colors.HexColor(COLORS[name])


def find_cjk_font() -> tuple[str, str]:
    candidates = [
        (Path(r"C:\Windows\Fonts\msyh.ttc"), "MicrosoftYaHei"),
        (Path(r"C:\Windows\Fonts\simhei.ttf"), "SimHei"),
        (Path(r"C:\Windows\Fonts\simsun.ttc"), "SimSun"),
        (Path("/System/Library/Fonts/PingFang.ttc"), "PingFangSC"),
        (Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"), "NotoSansCJK"),
        (Path("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"), "WenQuanYiMicroHei"),
    ]
    for path, name in candidates:
        if path.exists():
            pdfmetrics.registerFont(TTFont(name, str(path)))
            return name, str(path)
    raise RuntimeError("No CJK font found. Install a Chinese font or update font candidates.")


def inline_markup(text: str) -> str:
    escaped = xml_escape(text.strip())
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)


def split_label_value(text: str) -> tuple[str | None, str]:
    for sep in ("：", ":"):
        if sep in text:
            label, value = text.split(sep, 1)
            label = label.strip()
            value = value.strip()
            if 1 <= len(label) <= 16 and not re.match(r"^\d+$", label):
                return label, value
    return None, text.strip()


def extract_meta(markdown: str) -> dict[str, str]:
    meta = {
        "title": "技术路线与执行方案",
        "status": "待评估",
        "recommendation": "建议补充关键信息后继续评估。",
    }
    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if line.startswith("# ") and meta["title"] == "技术路线与执行方案":
            meta["title"] = line[2:].strip()
        elif line.startswith("当前判断"):
            match = re.search(r"(绿灯|黄灯|红灯)", line)
            if match:
                meta["status"] = match.group(1)
        elif line.startswith("推荐结论"):
            _, value = split_label_value(line)
            if value:
                meta["recommendation"] = value
    return meta


def build_styles(font_name: str) -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "ZYHTitle",
            parent=base["Title"],
            fontName=font_name,
            fontSize=18,
            leading=27,
            alignment=TA_CENTER,
            wordWrap="CJK",
            textColor=color("ink"),
            spaceAfter=6 * mm,
        ),
        "subtitle": ParagraphStyle(
            "ZYHSubtitle",
            parent=base["BodyText"],
            fontName=font_name,
            fontSize=9,
            leading=13,
            alignment=TA_CENTER,
            wordWrap="CJK",
            textColor=color("muted"),
            spaceAfter=8 * mm,
        ),
        "h2": ParagraphStyle(
            "ZYHH2",
            parent=base["Heading2"],
            fontName=font_name,
            fontSize=13.5,
            leading=20,
            wordWrap="CJK",
            textColor=color("blue"),
            spaceBefore=6 * mm,
            spaceAfter=2 * mm,
        ),
        "h3": ParagraphStyle(
            "ZYHH3",
            parent=base["Heading3"],
            fontName=font_name,
            fontSize=11.5,
            leading=17,
            wordWrap="CJK",
            textColor=color("ink"),
            spaceBefore=4 * mm,
            spaceAfter=1.5 * mm,
        ),
        "body": ParagraphStyle(
            "ZYHBody",
            parent=base["BodyText"],
            fontName=font_name,
            fontSize=10.5,
            leading=18,
            alignment=TA_LEFT,
            wordWrap="CJK",
            textColor=color("body"),
            spaceAfter=2.5 * mm,
        ),
        "list": ParagraphStyle(
            "ZYHList",
            parent=base["BodyText"],
            fontName=font_name,
            fontSize=10.2,
            leading=17,
            leftIndent=10 * mm,
            firstLineIndent=0,
            bulletFontName=font_name,
            bulletFontSize=10.2,
            bulletIndent=2 * mm,
            wordWrap="CJK",
            textColor=color("body"),
            spaceAfter=1.5 * mm,
        ),
        "summaryLabel": ParagraphStyle(
            "ZYHSummaryLabel",
            parent=base["BodyText"],
            fontName=font_name,
            fontSize=9,
            leading=14,
            wordWrap="CJK",
            textColor=color("muted"),
        ),
        "summaryValue": ParagraphStyle(
            "ZYHSummaryValue",
            parent=base["BodyText"],
            fontName=font_name,
            fontSize=10.5,
            leading=17,
            wordWrap="CJK",
            textColor=color("body"),
        ),
        "small": ParagraphStyle(
            "ZYHSmall",
            parent=base["BodyText"],
            fontName=font_name,
            fontSize=8,
            leading=11,
            wordWrap="CJK",
            textColor=color("muted"),
        ),
    }


def status_markup(status: str) -> str:
    status_color = {
        "绿灯": COLORS["green"],
        "黄灯": COLORS["yellow"],
        "红灯": COLORS["red"],
    }.get(status, COLORS["body"])
    return f'<font color="{status_color}"><b>{inline_markup(status)}</b></font>'


def make_summary(meta: dict[str, str], styles: dict[str, ParagraphStyle]):
    data = [
        [
            Paragraph("当前判断", styles["summaryLabel"]),
            Paragraph(status_markup(meta["status"]), styles["summaryValue"]),
        ],
        [
            Paragraph("推荐结论", styles["summaryLabel"]),
            Paragraph(inline_markup(meta["recommendation"]), styles["summaryValue"]),
        ],
    ]
    table = Table(data, colWidths=[28 * mm, 124 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), color("soft")),
                ("BOX", (0, 0), (-1, -1), 0.5, color("line")),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, color("line")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return KeepTogether([table, Spacer(1, 6 * mm)])


def decorate_page(canvas, doc, font_name: str) -> None:
    canvas.saveState()
    canvas.setStrokeColor(color("line"))
    canvas.setLineWidth(0.4)
    canvas.line(22 * mm, PAGE_HEIGHT - 15 * mm, PAGE_WIDTH - 22 * mm, PAGE_HEIGHT - 15 * mm)
    canvas.line(22 * mm, 15 * mm, PAGE_WIDTH - 22 * mm, 15 * mm)

    canvas.setFont(font_name, 8)
    canvas.setFillColor(color("muted"))
    canvas.drawString(22 * mm, PAGE_HEIGHT - 10 * mm, "中隐会 · 非标技术方案")
    canvas.drawRightString(PAGE_WIDTH - 22 * mm, PAGE_HEIGHT - 10 * mm, date.today().isoformat())
    canvas.drawRightString(PAGE_WIDTH - 22 * mm, 9 * mm, f"第 {doc.page} 页")
    canvas.restoreState()


def make_heading(text: str, styles: dict[str, ParagraphStyle]):
    match = re.match(r"^(\d+(?:\.\d+)*)\.\s*(.+)$", text)
    label = f"{match.group(1)}. {match.group(2)}" if match else text
    return KeepTogether(
        [
            Paragraph(inline_markup(label), styles["h2"]),
            HRFlowable(width="100%", thickness=0.5, color=color("line"), spaceAfter=3 * mm),
        ]
    )


def format_label_line(text: str) -> str:
    label, value = split_label_value(text)
    if label and value:
        return f"<b>{inline_markup(label)}：</b>{inline_markup(value)}"
    return inline_markup(text)


def markdown_to_flowables(markdown: str, styles: dict[str, ParagraphStyle]):
    meta = extract_meta(markdown)
    flowables = [
        Spacer(1, 8 * mm),
        Paragraph(inline_markup(meta["title"]), styles["title"]),
        Paragraph("客户交付说明 / 技术路线与执行方案", styles["subtitle"]),
        make_summary(meta, styles),
    ]

    in_fence = False
    skipped_first_title = False

    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not line:
            flowables.append(Spacer(1, 1.2 * mm))
            continue
        if line == "---":
            flowables.append(PageBreak())
            continue

        if line.startswith("# "):
            if not skipped_first_title:
                skipped_first_title = True
                continue
            flowables.append(Paragraph(inline_markup(line[2:].strip()), styles["title"]))
        elif line.startswith("## "):
            flowables.append(make_heading(line[3:].strip(), styles))
        elif line.startswith("### "):
            flowables.append(Paragraph(inline_markup(line[4:].strip()), styles["h3"]))
        elif line.startswith(("当前判断", "推荐结论")):
            continue
        elif line.startswith(">"):
            flowables.append(Paragraph(format_label_line(line[1:].strip()), styles["body"]))
        elif re.match(r"^[-*]\s+", line):
            flowables.append(Paragraph(format_label_line(line[2:].strip()), styles["list"], bulletText="•"))
        elif ordered_match := re.match(r"^(\d+)\.\s+(.+)$", line):
            flowables.append(
                Paragraph(
                    format_label_line(ordered_match.group(2).strip()),
                    styles["list"],
                    bulletText=f"{ordered_match.group(1)}.",
                )
            )
        else:
            flowables.append(Paragraph(format_label_line(line), styles["body"]))

    return flowables


def render(markdown_path: Path, output_path: Path) -> None:
    font_name, _ = find_cjk_font()
    styles = build_styles(font_name)
    content = markdown_path.read_text(encoding="utf-8")
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=24 * mm,
        leftMargin=24 * mm,
        topMargin=22 * mm,
        bottomMargin=22 * mm,
        title=markdown_path.stem,
    )
    page_decorator = lambda canvas, current_doc: decorate_page(canvas, current_doc, font_name)
    doc.build(markdown_to_flowables(content, styles), onFirstPage=page_decorator, onLaterPages=page_decorator)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Render Zhongyinhui CS deliverable Markdown to PDF.")
    parser.add_argument("markdown", help="Input UTF-8 Markdown file")
    parser.add_argument("output", help="Output PDF file")
    args = parser.parse_args(argv)

    markdown_path = Path(args.markdown)
    output_path = Path(args.output)
    if not markdown_path.exists():
        parser.error(f"Input file does not exist: {markdown_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    render(markdown_path, output_path)
    print(str(output_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
