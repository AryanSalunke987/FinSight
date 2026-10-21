"""
Dashboard Page — comprehensive analytics overview.

Shows stat cards, multiple interactive charts, and trending data.
"""

import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Dashboard | FNIP", page_icon="📊", layout="wide")

# ── API helper ────────────────────────────────────────────────────────────────
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
    .section-divider {
        border: none; height: 1px;
        background: linear-gradient(90deg, transparent, #d0d4db, transparent);
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>📊 Analytics Dashboard</h1>
    <p>Real-time overview of financial news intelligence</p>
</div>
""", unsafe_allow_html=True)

# ── Load Data ─────────────────────────────────────────────────────────────────
stats = api_get("/api/stats")
trending = api_get("/api/trending")
all_articles = api_get("/api/articles", {"page_size": 500, "hide_duplicates": True})

if not stats:
    st.stop()

# ── Stat Cards ────────────────────────────────────────────────────────────────
from dashboard.components.cards import render_stat_cards
render_stat_cards(stats)

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

# ── Charts Row 1: Source + Sector ─────────────────────────────────────────────
from dashboard.components.charts import (
    articles_by_source,
    articles_by_sector,
    trending_companies,
    priority_distribution,
    articles_over_time,
)

col1, col2 = st.columns(2)

with col1:
    fig = articles_by_source(stats.get("sources", {}))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = articles_by_sector(stats.get("categories", {}))
    st.plotly_chart(fig, use_container_width=True)

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

# ── Charts Row 2: Trending + Priority ────────────────────────────────────────
col3, col4 = st.columns(2)

with col3:
    companies_data = trending.get("trending_companies", []) if trending else []
    fig = trending_companies(companies_data)
    st.plotly_chart(fig, use_container_width=True)

with col4:
    articles_list = all_articles.get("articles", []) if all_articles else []
    fig = priority_distribution(articles_list)
    st.plotly_chart(fig, use_container_width=True)

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

# ── Chart Row 3: Articles Over Time ──────────────────────────────────────────
articles_list = all_articles.get("articles", []) if all_articles else []
fig = articles_over_time(articles_list)
st.plotly_chart(fig, use_container_width=True)

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

# ── Trending Sectors Table ────────────────────────────────────────────────────
st.markdown("### 📈 Trending Sectors (Last 24h)")

if trending and trending.get("trending_sectors"):
    sectors = trending["trending_sectors"]
    df = pd.DataFrame(sectors)
    df.columns = ["Sector", "Article Count"]

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Article Count": st.column_config.ProgressColumn(
                "Article Count",
                min_value=0,
                max_value=max(s["count"] for s in sectors) if sectors else 1,
                format="%d",
            ),
        },
    )
else:
    st.info("No trending sector data yet. Run a scrape first!")
