"""Document Exporter: converts Markdown documents to DOCX and PDF formats."""

import re
from pathlib import Path

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer


def export_markdown_to_docx(markdown_content: str, output_path: str, title: str = "Dokumen Inception") -> str:
    """Convert markdown content to a formatted .docx file."""
    doc = Document()

    # Set basic margins
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # Document Title
    title_para = doc.add_heading(title, level=0)
    title_para.paragraph_format.space_after = Pt(12)

    # Separate YAML frontmatter if exists
    content_to_parse = markdown_content
    if markdown_content.startswith("---"):
        parts = markdown_content.split("---", 2)
        if len(parts) >= 3:
            yaml_meta = parts[1].strip()
            content_to_parse = parts[2].strip()

            # Add metadata block
            meta_para = doc.add_paragraph()
            meta_para.paragraph_format.space_after = Pt(14)
            meta_run = meta_para.add_run("Informasi Metadata Proyek:\n" + yaml_meta)
            meta_run.font.size = Pt(9)
            meta_run.font.italic = True
            meta_run.font.color.rgb = RGBColor(100, 100, 100)

    lines = content_to_parse.split("\n")
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        if stripped.startswith("# "):
            doc.add_heading(stripped[2:], level=1)
        elif stripped.startswith("## "):
            doc.add_heading(stripped[3:], level=2)
        elif stripped.startswith("### "):
            doc.add_heading(stripped[4:], level=3)
        elif stripped.startswith("#### "):
            doc.add_heading(stripped[5:], level=4)
        elif stripped.startswith("- ") or stripped.startswith("* "):
            p = doc.add_paragraph(style="List Bullet")
            _add_formatted_text_to_docx(p, stripped[2:])
        elif re.match(r"^\d+\.\s", stripped):
            prefix_len = len(stripped.split(" ", 1)[0]) + 1
            p = doc.add_paragraph(style="List Number")
            _add_formatted_text_to_docx(p, stripped[prefix_len:])
        elif stripped.startswith(">"):
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.4)
            run = p.add_run(stripped.lstrip("> ").strip())
            run.font.italic = True
            run.font.color.rgb = RGBColor(80, 80, 80)
        else:
            p = doc.add_paragraph()
            _add_formatted_text_to_docx(p, stripped)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_path)
    return output_path


def _add_formatted_text_to_docx(paragraph, text: str):
    """Parse basic bold (**text**) and italic (*text*) into docx runs."""
    # Simple regex parsing for bold
    tokens = re.split(r"(\*\*.*?\*\*)", text)
    for token in tokens:
        if token.startswith("**") and token.endswith("**") and len(token) > 4:
            run = paragraph.add_run(token[2:-2])
            run.bold = True
        else:
            # Check for inline code `code`
            sub_tokens = re.split(r"(`.*?`)", token)
            for sub_tok in sub_tokens:
                if sub_tok.startswith("`") and sub_tok.endswith("`") and len(sub_tok) > 2:
                    r = paragraph.add_run(sub_tok[1:-1])
                    r.font.name = "Consolas"
                    r.font.size = Pt(9.5)
                else:
                    paragraph.add_run(sub_tok)


def export_markdown_to_pdf(markdown_content: str, output_path: str, title: str = "Dokumen Inception") -> str:
    """Convert markdown content to a styled PDF using ReportLab."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=14,
    )
    h1_style = ParagraphStyle(
        "DocH1",
        parent=styles["Heading2"],
        fontSize=15,
        leading=18,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=14,
        spaceAfter=6,
    )
    h2_style = ParagraphStyle(
        "DocH2",
        parent=styles["Heading3"],
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#334155"),
        spaceBefore=10,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "DocBody",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=6,
    )
    bullet_style = ParagraphStyle(
        "DocBullet",
        parent=styles["Normal"],
        fontSize=10,
        leading=13,
        leftIndent=15,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=3,
    )
    meta_style = ParagraphStyle(
        "DocMeta",
        parent=styles["Normal"],
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=12,
    )

    elements = []
    elements.append(Paragraph(title, title_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=12))

    content_to_parse = markdown_content
    if markdown_content.startswith("---"):
        parts = markdown_content.split("---", 2)
        if len(parts) >= 3:
            yaml_meta = parts[1].strip().replace("\n", "<br/>")
            content_to_parse = parts[2].strip()
            elements.append(Paragraph(f"<b>Metadata Dokumen:</b><br/>{yaml_meta}", meta_style))
            elements.append(Spacer(1, 10))

    lines = content_to_parse.split("\n")
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Convert markdown formatting to html tags for ReportLab Paragraph
        formatted = _format_md_for_reportlab(stripped)

        if stripped.startswith("# "):
            elements.append(Paragraph(formatted[2:], h1_style))
        elif stripped.startswith("## "):
            elements.append(Paragraph(formatted[3:], h1_style))
        elif stripped.startswith("### "):
            elements.append(Paragraph(formatted[4:], h2_style))
        elif stripped.startswith("- ") or stripped.startswith("* "):
            elements.append(Paragraph(f"&bull; {formatted[2:]}", bullet_style))
        elif re.match(r"^\d+\.\s", stripped):
            elements.append(Paragraph(formatted, bullet_style))
        else:
            elements.append(Paragraph(formatted, body_style))

    doc.build(elements)
    return output_path


def _format_md_for_reportlab(text: str) -> str:
    """Clean and replace markdown bold/italic/code with ReportLab XML tags."""
    # XML escape & < > first
    t = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # Bold **text** -> <b>text</b>
    t = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", t)
    # Italic *text* -> <i>text</i>
    t = re.sub(r"\*(.*?)\*", r"<i>\1</i>", t)
    # Code `code` -> <font name="Courier">\1</font>
    t = re.sub(r"`(.*?)`", r'<font name="Courier">\1</font>', t)
    return t
