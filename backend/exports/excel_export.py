"""
Excel Export — generates professionally formatted .xlsx reports.

Uses OpenPyXL to create a spreadsheet with:
  - Styled header row
  - Auto-sized columns
  - Color-coded priority cells
  - Report metadata row
"""

import io
import logging
from datetime import datetime

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

logger = logging.getLogger(__name__)

# ── Color palette ─────────────────────────────────────────────────────────────
HEADER_FILL = PatternFill(start_color="1B2A4A", end_color="1B2A4A", fill_type="solid")
HEADER_FONT = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
DATA_FONT = Font(name="Calibri", size=10)
TITLE_FONT = Font(name="Calibri", size=14, bold=True, color="1B2A4A")
SUBTITLE_FONT = Font(name="Calibri", size=10, italic=True, color="666666")

# Priority colors
PRIORITY_HIGH = PatternFill(start_color="FFCDD2", end_color="FFCDD2", fill_type="solid")  # Red tint
PRIORITY_MED = PatternFill(start_color="FFE0B2", end_color="FFE0B2", fill_type="solid")   # Orange tint
PRIORITY_LOW = PatternFill(start_color="E8F5E9", end_color="E8F5E9", fill_type="solid")   # Green tint

THIN_BORDER = Border(
    left=Side(style="thin", color="D0D0D0"),
    right=Side(style="thin", color="D0D0D0"),
    top=Side(style="thin", color="D0D0D0"),
    bottom=Side(style="thin", color="D0D0D0"),
)


def generate_excel(articles: list[dict]) -> io.BytesIO:
    """Generate an Excel report from a list of article dicts.

    Args:
        articles: List of article dicts (from Article.to_dict()).

    Returns:
        BytesIO buffer containing the .xlsx file.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Financial News Report"

    # ── Report title rows ─────────────────────────────────────────────────
    ws.merge_cells("A1:H1")
    title_cell = ws["A1"]
    title_cell.value = "Financial News Intelligence Report"
    title_cell.font = TITLE_FONT
    title_cell.alignment = Alignment(horizontal="left", vertical="center")

    ws.merge_cells("A2:H2")
    subtitle_cell = ws["A2"]
    subtitle_cell.value = (
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | "
        f"Articles: {len(articles)}"
    )
    subtitle_cell.font = SUBTITLE_FONT

    ws.append([])  # blank row

    # ── Header row ────────────────────────────────────────────────────────
    headers = [
        "Priority", "Headline", "Source", "Category",
        "Companies", "Sector", "Published", "URL",
    ]
    ws.append(headers)
    header_row = ws.max_row

    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=header_row, column=col_idx)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = THIN_BORDER

    # ── Data rows ─────────────────────────────────────────────────────────
    for article in articles:
        companies = article.get("companies", [])
        if isinstance(companies, list):
            companies_str = ", ".join(companies)
        else:
            companies_str = str(companies)

        published = article.get("published_time", "")
        if published and isinstance(published, str) and "T" in published:
            try:
                published = datetime.fromisoformat(published).strftime("%Y-%m-%d %H:%M")
            except (ValueError, TypeError):
                pass

        row_data = [
            article.get("priority_score", 0),
            article.get("headline", ""),
            article.get("source", ""),
            article.get("category", ""),
            companies_str,
            article.get("sector", ""),
            published or "",
            article.get("url", ""),
        ]
        ws.append(row_data)

        # Style data cells
        current_row = ws.max_row
        priority = article.get("priority_score", 0)

        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=current_row, column=col_idx)
            cell.font = DATA_FONT
            cell.border = THIN_BORDER
            cell.alignment = Alignment(
                vertical="center",
                wrap_text=(col_idx == 2),  # wrap headline
            )

        # Color-code priority column
        priority_cell = ws.cell(row=current_row, column=1)
        priority_cell.alignment = Alignment(horizontal="center", vertical="center")
        if priority >= 80:
            priority_cell.fill = PRIORITY_HIGH
        elif priority >= 50:
            priority_cell.fill = PRIORITY_MED
        else:
            priority_cell.fill = PRIORITY_LOW

    # ── Auto-size columns ─────────────────────────────────────────────────
    column_widths = [10, 60, 18, 18, 30, 15, 20, 50]
    for idx, width in enumerate(column_widths, 1):
        ws.column_dimensions[get_column_letter(idx)].width = width

    # Freeze header row
    ws.freeze_panes = f"A{header_row + 1}"

    # ── Auto-filter ───────────────────────────────────────────────────────
    ws.auto_filter.ref = f"A{header_row}:H{ws.max_row}"

    # ── Write to buffer ───────────────────────────────────────────────────
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    logger.info("[Excel Export] Generated report with %d articles.", len(articles))
    return buffer
