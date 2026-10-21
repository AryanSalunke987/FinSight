"""
Financial News Intelligence Platform — Streamlit Dashboard Entry Point.

Multi-page app with sidebar navigation, global styling, and
connection to the FastAPI backend.
"""

import sys
import os

# Add project root to path so imports work
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
import requests

# ── Page Configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Financial News Intelligence Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* Global font */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Header bar styling */
    .main-header {
        background: linear-gradient(135deg, #1B2A4A 0%, #2C3E6B 50%, #1a237e 100%);
        padding: 28px 36px;
        border-radius: 18px;
        margin-bottom: 28px;
        box-shadow: 0 6px 30px rgba(27, 42, 74, 0.3);
        border: 1px solid rgba(255,255,255,0.08);
    }
    .main-header h1 {
        color: white;
        font-size: 28px;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .main-header p {
        color: rgba(255,255,255,0.75);
        font-size: 14px;
        margin: 6px 0 0 0;
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f1623 0%, #141e30 60%, #1a2540 100%);
        border-right: 1px solid rgba(255,255,255,0.08);
    }
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #e2e8f0;
        font-weight: 700;
    }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown li,
    section[data-testid="stSidebar"] label {
        color: #a0aec0 !important;
    }
    section[data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.1);
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Dataframe styling */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }

    /* Button styling */
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.2s ease;
        border: none;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        font-weight: 600;
    }

    /* Section divider */
    .section-divider {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent 0%, #d0d4db 50%, transparent 100%);
        margin: 24px 0;
    }
</style>
""", unsafe_allow_html=True)

# ── API base URL ──────────────────────────────────────────────────────────────
API_BASE = "http://127.0.0.1:8000"


def api_get(endpoint: str, params: dict = None) -> dict | list | None:
    """Make a GET request to the FastAPI backend.

    Args:
        endpoint: API endpoint (e.g., "/api/stats").
        params: Optional query parameters.

    Returns:
        Parsed JSON response or None on error.
    """
    try:
        resp = requests.get(f"{API_BASE}{endpoint}", params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error(
            "⚠️ Cannot connect to the backend API. "
            "Make sure the FastAPI server is running on port 8000.\n\n"
            "Run: `python run.py` or `uvicorn backend.main:app --reload`"
        )
        return None
    except Exception as e:
        st.error(f"API Error: {e}")
        return None


def api_post(endpoint: str, data: dict = None) -> dict | None:
    """Make a POST request to the FastAPI backend."""
    try:
        resp = requests.post(f"{API_BASE}{endpoint}", json=data, timeout=120)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Cannot connect to the backend API.")
        return None
    except Exception as e:
        st.error(f"API Error: {e}")
        return None


# ── Sidebar: Branding & Controls ─────────────────────────────────────────────
st.sidebar.markdown("""
<div style="text-align:center; padding: 16px 0;">
    <div style="font-size: 40px;">📊</div>
    <div style="font-size: 16px; font-weight: 700; color: #e2e8f0;
                margin-top: 6px;">Financial News</div>
    <div style="font-size: 12px; color: #a0aec0;">Intelligence Platform</div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")

# Scheduler status
scheduler = api_get("/api/scheduler")
if scheduler and scheduler.get("running"):
    next_run = scheduler.get("next_run", "Unknown")
    if next_run and next_run != "Unknown":
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(next_run)
            next_run = dt.strftime("%H:%M")
        except (ValueError, TypeError):
            pass
    st.sidebar.success(f"🟢 Scheduler Active — Next: {next_run}")
else:
    st.sidebar.warning("🔴 Scheduler Inactive")

# Manual scrape button
if st.sidebar.button("🔄 Scrape Now", use_container_width=True, type="primary"):
    with st.sidebar:
        with st.spinner("Running pipeline..."):
            result = api_post("/api/scrape")
            if result and result.get("status") == "success":
                r = result["result"]
                st.success(
                    f"✅ Done! Scraped {r['raw_count']} → "
                    f"Stored {r['inserted']} new articles "
                    f"({r['elapsed_seconds']}s)"
                )
                st.rerun()
            elif result:
                st.error(f"Failed: {result.get('message', 'Unknown error')}")

st.sidebar.markdown("---")

# ── Page routing is handled by Streamlit's multi-page structure ──────────────
# The actual pages are in dashboard/pages/
# This file serves as the landing page

# ── Landing/Home Content ─────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>📊 Financial News Intelligence Platform</h1>
    <p>Automated collection, classification, and reporting of financial news from 6 trusted sources</p>
</div>
""", unsafe_allow_html=True)

# Quick stats on landing page
stats = api_get("/api/stats")
if stats:
    from dashboard.components.cards import render_stat_cards
    render_stat_cards(stats)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # Quick overview charts
    col1, col2 = st.columns(2)

    with col1:
        from dashboard.components.charts import articles_by_source
        fig = articles_by_source(stats.get("sources", {}))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        from dashboard.components.charts import articles_by_sector
        fig = articles_by_sector(stats.get("categories", {}))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # Latest high-priority articles
    st.markdown("### 🔥 Latest High-Priority Articles")
    articles_resp = api_get("/api/articles", {
        "priority_min": 70,
        "hide_duplicates": True,
        "sort_by": "priority_score",
        "sort_order": "desc",
        "page_size": 10,
    })

    if articles_resp and articles_resp.get("articles"):
        from dashboard.components.cards import render_priority_badge
        import pandas as pd

        articles = articles_resp["articles"]
        display_data = []
        for a in articles:
            display_data.append({
                "Priority": a.get("priority_score", 0),
                "Headline": a.get("headline", ""),
                "Source": a.get("source", ""),
                "Category": a.get("category", ""),
                "Companies": ", ".join(a.get("companies", [])),
            })

        df = pd.DataFrame(display_data)
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Priority": st.column_config.ProgressColumn(
                    "Priority",
                    min_value=0,
                    max_value=100,
                    format="%d",
                ),
                "Headline": st.column_config.TextColumn(
                    "Headline", width="large"
                ),
            },
        )
    else:
        st.info("No high-priority articles yet. Trigger a scrape to get started!")

else:
    st.markdown("""
    ### 🚀 Getting Started

    1. Make sure the **FastAPI backend** is running:
       ```
       python run.py
       ```

    2. The system will automatically scrape news from 6 sources every 2 hours.

    3. Use the **"Scrape Now"** button in the sidebar to trigger an immediate scrape.

    4. Navigate to the **Dashboard**, **Search**, and **Export** pages using the sidebar.
    """)
