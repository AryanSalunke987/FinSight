"""
Reusable filter widgets for the dashboard sidebar.

Returns a filter dict that can be passed directly to the API.
"""

import streamlit as st
from datetime import datetime, timedelta


def render_filters(categories: list[str], sources: list[str]) -> dict:
    """Render sidebar filter widgets and return selected values.

    Args:
        categories: List of available category names.
        sources: List of available source names.

    Returns:
        Dict with filter values (any None value means "no filter").
    """
    st.sidebar.markdown("### 🔎 Filters")

    keyword = st.sidebar.text_input(
        "Keyword Search",
        placeholder="e.g. RBI, Infosys, merger...",
        key="filter_keyword",
    )

    company = st.sidebar.text_input(
        "Company Name",
        placeholder="e.g. Tata Motors",
        key="filter_company",
    )

    category = st.sidebar.selectbox(
        "Category",
        options=["All"] + sorted(categories),
        key="filter_category",
    )

    source = st.sidebar.selectbox(
        "Source",
        options=["All"] + sorted(sources),
        key="filter_source",
    )

    # Priority range
    st.sidebar.markdown("**Priority Range**")
    priority_min, priority_max = st.sidebar.slider(
        "Priority Score",
        min_value=0,
        max_value=100,
        value=(0, 100),
        key="filter_priority",
        label_visibility="collapsed",
    )

    # Date range
    st.sidebar.markdown("**Date Range**")
    date_cols = st.sidebar.columns(2)
    with date_cols[0]:
        date_from = st.date_input(
            "From",
            value=datetime.now() - timedelta(days=7),
            key="filter_date_from",
        )
    with date_cols[1]:
        date_to = st.date_input(
            "To",
            value=datetime.now(),
            key="filter_date_to",
        )

    # Hide duplicates toggle
    hide_duplicates = st.sidebar.checkbox(
        "Hide Duplicates",
        value=True,
        key="filter_hide_dupes",
    )

    return {
        "keyword": keyword if keyword else None,
        "company": company if company else None,
        "category": category if category != "All" else None,
        "source": source if source != "All" else None,
        "priority_min": priority_min if priority_min > 0 else None,
        "priority_max": priority_max if priority_max < 100 else None,
        "date_from": datetime.combine(date_from, datetime.min.time()).isoformat() if date_from else None,
        "date_to": datetime.combine(date_to, datetime.max.time()).isoformat() if date_to else None,
        "hide_duplicates": hide_duplicates,
    }
