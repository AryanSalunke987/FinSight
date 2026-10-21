"""
PDF Export — generates a professional PDF report using ReportLab.

Features:
  - Report title and generation timestamp
  - Filter summary
  - Article table with priority color coding
  - Page numbers in footer
"""

import io
import logging
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    PageBreak,
)

logger = logging.getLogger(__name__)

# ── Color palette ─────────────────────────────────────────────────────────────
PRIMARY_COLOR = colors.HexColor("#1B2A4A")
ACCENT_COLOR = colors.HexColor("#2196F3")
HEADER_BG = colors.HexColor("#1B2A4A")
HEADER_TEXT = colors.white
ROW_ALT = colors.HexColor("#F5F7FA")
PRIORITY_HIGH = colors.HexColor("#FFCDD2")
PRIORITY_MED = colors.HexColor("#FFE0B2")
PRIORITY_LOW = colors.HexColor("#E8F5E9")


def _add_page_number(canvas, doc):
    """Add page number to footer."""
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.gray)
    page_num = f"Page {canvas.getPageNumber()}"
    canvas.drawRightString(
        doc.pagesize[0] - 30 * mm,
        15 * mm,
        page_num,
    )
    canvas.drawString(
        30 * mm,
        15 * mm,
        "Financial News Intelligence Platform",
    )
    canvas.restoreState()


def generate_pdf(articles: list[dict], filters_summary: str = "None") -> io.BytesIO:
    """Generate a PDF report from a list of article dicts.

    Args:
        articles: List of article dicts (from Article.to_dict()).
        filters_summary: String describing the applied filters.

    Returns:
        BytesIO buffer containing the PDF file.
    """
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        topMargin=25 * mm,
        bottomMargin=25 * mm,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        title="Financial News Intelligence Report",
        author="Financial News Intelligence Platform",
    )

    # ── Styles ────────────────────────────────────────────────────────────
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=20,
        textColor=PRIMARY_COLOR,
        spaceAfter=6,
        alignment=TA_LEFT,
    )

    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.gray,
        spaceAfter=3,
    )

    section_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=PRIMARY_COLOR,
        spaceBefore=12,
        spaceAfter=6,
    )

    cell_style = ParagraphStyle(
        "CellText",
        parent=styles["Normal"],
        fontSize=7,
        leading=9,
    )

    # ── Build document elements ───────────────────────────────────────────
    elements = []

    # Title block
    elements.append(Paragraph("Financial News Intelligence Report", title_style))
    elements.append(
        Paragraph(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            subtitle_style,
        )
    )
    elements.append(
        Paragraph(f"Total Articles: {len(articles)}", subtitle_style)
    )
    elements.append(
        Paragraph(f"Filters Applied: {filters_summary}", subtitle_style)
    )
    elements.append(Spacer(1, 10 * mm))

    # ── Summary statistics ────────────────────────────────────────────────
    if articles:
        high_count = sum(1 for a in articles if a.get("priority_score", 0) >= 80)
        med_count = sum(
            1 for a in articles if 50 <= a.get("priority_score", 0) < 80
        )
        low_count = sum(1 for a in articles if a.get("priority_score", 0) < 50)

        # Source distribution
        source_counts: dict[str, int] = {}
        for a in articles:
            src = a.get("source", "Unknown")
            source_counts[src] = source_counts.get(src, 0) + 1

        elements.append(Paragraph("Summary", section_style))
        summary_data = [
            ["Priority", "Count"],
            ["High (≥80)", str(high_count)],
            ["Medium (50-79)", str(med_count)],
            ["Low (<50)", str(low_count)],
        ]
        summary_table = Table(summary_data, colWidths=[80 * mm, 40 * mm])
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), HEADER_TEXT),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.gray),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ROW_ALT]),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 8 * mm))

    # ── Articles table ────────────────────────────────────────────────────
    elements.append(Paragraph("Articles", section_style))

    if not articles:
        elements.append(Paragraph("No articles match the selected filters.", cell_style))
    else:
        # Table headers
        table_data = [["#", "Priority", "Headline", "Source", "Category", "Companies"]]

        for idx, article in enumerate(articles, 1):
            companies = article.get("companies", [])
            if isinstance(companies, list):
                companies_str = ", ".join(companies[:3])
                if len(companies) > 3:
                    companies_str += f" +{len(companies) - 3}"
            else:
                companies_str = str(companies)

            headline_text = article.get("headline", "")
            # Truncate long headlines for PDF
            if len(headline_text) > 100:
                headline_text = headline_text[:97] + "..."

            table_data.append([
                str(idx),
                str(article.get("priority_score", 0)),
                Paragraph(headline_text, cell_style),
                article.get("source", ""),
                article.get("category", ""),
                Paragraph(companies_str, cell_style),
            ])

        col_widths = [
            12 * mm,   # #
            18 * mm,   # Priority
            110 * mm,  # Headline
            30 * mm,   # Source
            28 * mm,   # Category
            60 * mm,   # Companies
        ]

        article_table = Table(table_data, colWidths=col_widths, repeatRows=1)

        # Base table style
        style_commands = [
            ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), HEADER_TEXT),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("FONTSIZE", (0, 1), (-1, -1), 7),
            ("ALIGN", (0, 0), (1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D0D0D0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ROW_ALT]),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]

        # Color-code priority cells
        for idx, article in enumerate(articles, 1):
            priority = article.get("priority_score", 0)
            if priority >= 80:
                style_commands.append(
                    ("BACKGROUND", (1, idx), (1, idx), PRIORITY_HIGH)
                )
            elif priority >= 50:
                style_commands.append(
                    ("BACKGROUND", (1, idx), (1, idx), PRIORITY_MED)
                )
            else:
                style_commands.append(
                    ("BACKGROUND", (1, idx), (1, idx), PRIORITY_LOW)
                )

        article_table.setStyle(TableStyle(style_commands))
        elements.append(article_table)

    # ── Build PDF ─────────────────────────────────────────────────────────
    doc.build(elements, onFirstPage=_add_page_number, onLaterPages=_add_page_number)
    buffer.seek(0)

    logger.info("[PDF Export] Generated report with %d articles.", len(articles))
    return buffer
