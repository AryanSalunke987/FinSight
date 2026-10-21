"""
Search Page — filter and browse articles with combined filters.
"""

import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Search | FNIP", page_icon="🔍", layout="wide")

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
    .article-card {
        background: white; border-radius: 12px; padding: 18px 22px;
        margin-bottom: 12px; border: 1px solid #e8ecf1;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        transition: box-shadow 0.2s ease, border-color 0.2s ease;
    }
    .article-card:hover {
        box-shadow: 0 4px 16px rgba(0,0,0,0.08);
        border-color: #2196F3;
    }
    .article-title {
        font-size: 15px; font-weight: 600; color: #1B2A4A;
        margin-bottom: 6px; line-height: 1.4;
    }
    .article-meta {
        font-size: 12px; color: #888; display: flex;
        gap: 16px; flex-wrap: wrap; margin-top: 8px;
    }
    .article-meta span { display: inline-flex; align-items: center; gap: 4px; }
    .priority-badge {
        display: inline-block; padding: 2px 10px; border-radius: 10px;
        font-size: 11px; font-weight: 700; color: white;
    }
    .priority-high { background: #EF5350; }
    .priority-med { background: #FF9800; }
    .priority-low { background: #66BB6A; }
    .category-tag {
        display: inline-block; background: #E3F2FD; color: #1565C0;
        padding: 2px 10px; border-radius: 10px; font-size: 11px; font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🔍 Search & Filter Articles</h1>
    <p>Find exactly what you need with powerful combined filters</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar Filters ──────────────────────────────────────────────────────────
categories = api_get("/api/categories") or []
sources = api_get("/api/sources") or []

from dashboard.components.filters import render_filters
filters = render_filters(categories, sources)

# ── Sort Options ──────────────────────────────────────────────────────────────
sort_cols = st.columns([2, 2, 6])
with sort_cols[0]:
    sort_by = st.selectbox(
        "Sort By",
        options=["priority_score", "scraped_time", "headline", "source"],
        format_func=lambda x: {
            "priority_score": "📊 Priority",
            "scraped_time": "🕐 Date",
            "headline": "📰 Headline",
            "source": "🌐 Source",
        }.get(x, x),
    )
with sort_cols[1]:
    sort_order = st.selectbox(
        "Order", options=["desc", "asc"],
        format_func=lambda x: "⬇️ Descending" if x == "desc" else "⬆️ Ascending",
    )

# ── Pagination ────────────────────────────────────────────────────────────────
page_size = 25

if "search_page" not in st.session_state:
    st.session_state.search_page = 1

# ── Fetch Articles ────────────────────────────────────────────────────────────
params = {
    "page": st.session_state.search_page,
    "page_size": page_size,
    "sort_by": sort_by,
    "sort_order": sort_order,
}

# Add active filters to params
for key, value in filters.items():
    if value is not None:
        params[key] = value

result = api_get("/api/articles", params)

if result:
    total = result.get("total", 0)
    total_pages = result.get("total_pages", 1)
    articles = result.get("articles", [])

    # Results summary
    st.markdown(f"**{total:,}** articles found — Page {st.session_state.search_page} of {total_pages}")

    # ── Article Cards ─────────────────────────────────────────────────────
    for article in articles:
        priority = article.get("priority_score", 0)
        priority_class = "priority-high" if priority >= 80 else "priority-med" if priority >= 50 else "priority-low"

        companies = article.get("companies", [])
        companies_str = ", ".join(companies[:3]) if companies else "—"

        scraped = article.get("scraped_time", "")
        if scraped:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(scraped)
                scraped = dt.strftime("%b %d, %H:%M")
            except (ValueError, TypeError):
                pass

        url = article.get("url", "#")
        headline = article.get("headline", "Untitled")
        summary = article.get("summary", "")
        source = article.get("source", "Unknown")
        category = article.get("category", "General")

        st.markdown(f"""
        <div class="article-card">
            <div style="display:flex; justify-content:space-between; align-items:start;">
                <div class="article-title">
                    <a href="{url}" target="_blank" style="text-decoration:none; color:#1B2A4A;">
                        {headline}
                    </a>
                </div>
                <span class="priority-badge {priority_class}">{priority}</span>
            </div>
            <div style="font-size:13px; color:#555; margin-top:4px; line-height:1.5;">
                {summary[:200] + '...' if len(summary) > 200 else summary}
            </div>
            <div class="article-meta">
                <span>🌐 {source}</span>
                <span><span class="category-tag">{category}</span></span>
                <span>🏢 {companies_str}</span>
                <span>🕐 {scraped}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Pagination Controls ───────────────────────────────────────────────
    if total_pages > 1:
        st.markdown("---")
        page_cols = st.columns([1, 2, 1])

        with page_cols[0]:
            if st.button("← Previous", disabled=(st.session_state.search_page <= 1)):
                st.session_state.search_page -= 1
                st.rerun()

        with page_cols[1]:
            st.markdown(
                f"<div style='text-align:center; padding:8px; color:#666;'>"
                f"Page {st.session_state.search_page} of {total_pages}</div>",
                unsafe_allow_html=True,
            )

        with page_cols[2]:
            if st.button("Next →", disabled=(st.session_state.search_page >= total_pages)):
                st.session_state.search_page += 1
                st.rerun()

else:
    st.info("No articles found. Try adjusting your filters or run a scrape first.")
