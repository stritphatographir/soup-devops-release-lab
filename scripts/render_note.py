"""Render the short submission note; requires requirements/docs.lock."""

import argparse
import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]


def inline(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"\[([^]]+)\]\(([^)]+)\)", r'<link href="\2" color="#086A70">\1</link>', text)
    return re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)


def render(source: Path, output: Path) -> None:
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="NoteTitle", fontName="Helvetica-Bold", fontSize=19, leading=22,
        textColor=colors.HexColor("#142D3A"), spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="NoteHeading", fontName="Helvetica-Bold", fontSize=10.7, leading=13,
        textColor=colors.HexColor("#086A70"), spaceBefore=9, spaceAfter=4,
        keepWithNext=True,
    ))
    styles.add(ParagraphStyle(
        name="NoteBody", fontName="Helvetica", fontSize=9.3, leading=12.1,
        textColor=colors.HexColor("#253440"), spaceAfter=6, alignment=TA_LEFT,
    ))
    styles.add(ParagraphStyle(
        name="NoteCell", parent=styles["NoteBody"], fontSize=8.4, leading=10.6,
        spaceAfter=0,
    ))
    output.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(output), pagesize=A4, rightMargin=40, leftMargin=40,
        topMargin=34, bottomMargin=36, title="Soup - Python Release Trust Note",
        author="Amir; prepared with disclosed AI assistance",
    )
    story = []
    blocks = source.read_text(encoding="utf-8").strip().split("\n\n")
    for block in blocks:
        if block == "<!-- pagebreak -->":
            story.append(PageBreak())
        elif block.startswith("# "):
            story.append(Paragraph(inline(block[2:]), styles["NoteTitle"]))
            story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#086A70")))
            story.append(Spacer(1, 7))
        elif block.startswith("## "):
            story.append(Paragraph(inline(block[3:]), styles["NoteHeading"]))
        elif block.startswith("| "):
            rows = []
            for line in block.splitlines():
                if re.fullmatch(r"[| :\-]+", line):
                    continue
                rows.append([Paragraph(inline(cell.strip()), styles["NoteCell"])
                             for cell in line.strip("|").split("|")])
            table = Table(rows, colWidths=[91, 198, document.width - 289], repeatRows=1)
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E5F0F0")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.HexColor("#086A70")),
                ("LINEBELOW", (0, 1), (-1, -1), 0.3, colors.HexColor("#DAE1E5")),
            ]))
            story.extend([table, Spacer(1, 7)])
        else:
            story.append(Paragraph(inline(block.replace("\n", " ")), styles["NoteBody"]))

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#D5DFE3"))
        canvas.line(40, 28, A4[0] - 40, 28)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#5C6D76"))
        canvas.drawString(40, 17, "SOUP / DEVOPS RELEASE LAB / 12 NOV 2026")
        canvas.drawRightString(A4[0] - 40, 17, str(doc.page))
        canvas.restoreState()

    document.build(story, onFirstPage=footer, onLaterPages=footer)
    print(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "docs/NOTE.md")
    parser.add_argument("--out", type=Path,
                        default=ROOT / "output/pdf/Soup-DevOps-Release-Note.pdf")
    args = parser.parse_args()
    render(args.source, args.out)
