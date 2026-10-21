"""
Export Page — preview and download filtered articles as Excel or PDF.
"""

import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Export | FNIP", page_icon="📥", layout="wide")

API_BASE = "http://127.0.0.1:8000"


def api_get(endpoint, params=None):
    try:
        resp = requests.get(f"{API_BASE}{endpoint}", params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Backend not running. Start with: `python run.py`")
        return None
    except Exception as e:
        st.error(f"API Error: {e}")
        return None


def api_download(endpoint, params=None):
    """Download a file from the API and return raw bytes."""
    try:
        resp = requests.get(
            f"{API_BASE}{endpoint}", params=params, timeout=60, stream=True
        )
        resp.raise_for_status()
        return resp.content, resp.headers.get("Content-Disposition", "")
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Backend not running.")
        return None, ""
    except Exception as e:
        st.error(f"Download Error: {e}")
        return None, ""


# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .main-header {
        background: linear-gradient(135deg, #1B2A4A 0%, #2C3E6B 50%, #1a237e 100%);
        padding: 24px 32px; border-radius: 16px; margin-bottom: 24px;
        box-shadow: 0 4px 20px rgba(27, 42, 74, 0.25);
    }
    .main-header h1 { color: white; font-size: 24px; font-weight: 800; margin: 0; }
    .main-header p { color: rgba(255,255,255,0.7); font-size: 13px; margin: 4px 0 0; }
    .export-card {
        background: white; border: 2px solid #e8ecf1; border-radius: 16px;
        padding: 28px; text-align: center;
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }
    .export-card:hover {
        border-color: #2196F3;
        box-shadow: 0 4px 16px rgba(33, 150, 243, 0.15);
    }
    .export-icon { font-size: 48px; margin-bottom: 12px; }
    .export-title { font-size: 18px; font-weight: 700; color: #1B2A4A; }
    .export-desc { font-size: 13px; color: #666; margin-top: 6px; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>📥 Export Reports</h1>
    <p>Generate and download professional reports from filtered articles</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar Filters ──────────────────────────────────────────────────────────
categories = api_get("/api/categories") or []
sources = api_get("/api/sources") or []

from dashboard.components.filters import render_filters
filters = render_filters(categories, sources)

# ── Build API params from filters ─────────────────────────────────────────────
export_params = {}
for key, value in filters.items():
    if value is not None:
        export_params[key] = value

# ── Preview Section ───────────────────────────────────────────────────────────
st.markdown("### 📋 Export Preview")

preview_params = {**export_params, "page": 1, "page_size": 50, "sort_by": "priority_score", "sort_order": "desc"}
result = api_get("/api/articles", preview_params)

if result:
    total = result.get("total", 0)
    articles = result.get("articles", [])

    # Summary bar
    active_filters = [f"**{k}**: {v}" for k, v in filters.items() if v is not None and k != "hide_duplicates"]
    filter_text = " | ".join(active_filters) if active_filters else "No filters applied"

    st.info(f"📊 **{total}** articles match your filters. {filter_text}")

    if articles:
        # Preview table
        display_data = []
        for a in articles:
            companies = a.get("companies", [])
            display_data.append({
                "Priority": a.get("priority_score", 0),
                "Headline": a.get("headline", "")[:80],
                "Source": a.get("source", ""),
                "Category": a.get("category", ""),
                "Companies": ", ".join(companies[:2]) if companies else "—",
            })

        df = pd.DataFrame(display_data)

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            height=400,
            column_config={
                "Priority": st.column_config.ProgressColumn(
                    "Priority", min_value=0, max_value=100, format="%d",
                ),
            },
        )

        if total > 50:
            st.caption(f"Showing first 50 of {total} articles. Full export will include up to 500 (Excel) or 200 (PDF).")

    st.markdown("---")

    # ── Export Buttons ────────────────────────────────────────────────────
    st.markdown("### 📦 Download Report")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="export-card">
            <div class="export-icon">📗</div>
            <div class="export-title">Excel Report</div>
            <div class="export-desc">
                Full data table with color-coded priorities,<br>
                auto-filters, and formatted columns (max 500 articles)
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("")  # spacer

        if st.button("⬇️ Download Excel", use_container_width=True, type="primary", key="dl_excel"):
            with st.spinner("Generating Excel report..."):
                content, disposition = api_download("/api/export/excel", export_params)
                if content:
                    from datetime import datetime
                    filename = f"financial_news_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
                    st.download_button(
                        label="💾 Save Excel File",
                        data=content,
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="save_excel",
                    )
                    st.success("✅ Excel report ready!")

    with col2:
        st.markdown("""
        <div class="export-card">
            <div class="export-icon">📕</div>
            <div class="export-title">PDF Report</div>
            <div class="export-desc">
                Professional report with summary stats,<br>
                priority coloring, and page numbers (max 200 articles)
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("")  # spacer

        if st.button("⬇️ Download PDF", use_container_width=True, type="primary", key="dl_pdf"):
            with st.spinner("Generating PDF report..."):
                content, disposition = api_download("/api/export/pdf", export_params)
                if content:
                    from datetime import datetime
                    filename = f"financial_news_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                    st.download_button(
                        label="💾 Save PDF File",
                        data=content,
                        file_name=filename,
                        mime="application/pdf",
                        key="save_pdf",
                    )
                    st.success("✅ PDF report ready!")
else:
    st.info("No articles found. Try adjusting your filters or run a scrape first.")
