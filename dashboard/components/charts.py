"""
Plotly chart builder functions for the dashboard.

All charts use a consistent dark professional theme.
"""

import plotly.express as px
import plotly.graph_objects as go

# ── Consistent theme ─────────────────────────────────────────────────────────
CHART_COLORS = [
    "#2196F3", "#FF9800", "#4CAF50", "#E91E63", "#9C27B0",
    "#00BCD4", "#FF5722", "#607D8B", "#8BC34A", "#3F51B5",
    "#FFC107", "#795548", "#009688", "#F44336", "#673AB7",
    "#CDDC39",
]

LAYOUT_DEFAULTS = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, Calibri, sans-serif", color="#333333"),
    margin=dict(l=20, r=20, t=40, b=20),
    hoverlabel=dict(
        bgcolor="#1B2A4A",
        font_color="white",
        font_size=12,
        bordercolor="rgba(0,0,0,0)",
    ),
)


def articles_by_sector(categories: dict) -> go.Figure:
    """Horizontal bar chart of articles by sector/category.

    Args:
        categories: Dict of {category_name: count}.

    Returns:
        Plotly Figure.
    """
    if not categories:
        return _empty_chart("No category data yet")

    sorted_cats = sorted(categories.items(), key=lambda x: x[1])
    names = [c[0] for c in sorted_cats]
    values = [c[1] for c in sorted_cats]

    fig = go.Figure(go.Bar(
        x=values,
        y=names,
        orientation="h",
        marker=dict(
            color=values,
            colorscale=[[0, "#2196F3"], [1, "#1B2A4A"]],
            cornerradius=4,
        ),
        text=values,
        textposition="outside",
        textfont=dict(size=11, color="#333"),
    ))

    fig.update_layout(
        title=dict(text="Articles by Sector", font=dict(size=16)),
        xaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.06)"),
        yaxis=dict(showgrid=False),
        height=max(300, len(names) * 32 + 80),
        **LAYOUT_DEFAULTS,
    )
    return fig


def articles_by_source(sources: dict) -> go.Figure:
    """Donut chart of articles by source.

    Args:
        sources: Dict of {source_name: count}.

    Returns:
        Plotly Figure.
    """
    if not sources:
        return _empty_chart("No source data yet")

    names = list(sources.keys())
    values = list(sources.values())

    fig = go.Figure(go.Pie(
        labels=names,
        values=values,
        hole=0.55,
        marker=dict(colors=CHART_COLORS[:len(names)]),
        textinfo="label+percent",
        textposition="outside",
        textfont=dict(size=11),
        hovertemplate="<b>%{label}</b><br>Articles: %{value}<br>Share: %{percent}<extra></extra>",
    ))

    fig.update_layout(
        title=dict(text="Articles by Source", font=dict(size=16)),
        showlegend=False,
        height=400,
        **LAYOUT_DEFAULTS,
    )
    return fig


def trending_companies(companies: list[dict]) -> go.Figure:
    """Bar chart of top trending companies.

    Args:
        companies: List of {"name": str, "count": int}.

    Returns:
        Plotly Figure.
    """
    if not companies:
        return _empty_chart("No trending companies yet")

    names = [c["name"] for c in companies]
    counts = [c["count"] for c in companies]

    fig = go.Figure(go.Bar(
        x=names,
        y=counts,
        marker=dict(
            color=counts,
            colorscale=[[0, "#4CAF50"], [0.5, "#2196F3"], [1, "#E91E63"]],
            cornerradius=6,
        ),
        text=counts,
        textposition="outside",
        textfont=dict(size=11),
    ))

    fig.update_layout(
        title=dict(text="Trending Companies (24h)", font=dict(size=16)),
        xaxis=dict(showgrid=False, tickangle=-45),
        yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.06)"),
        height=400,
        **LAYOUT_DEFAULTS,
    )
    return fig


def priority_distribution(articles: list[dict]) -> go.Figure:
    """Histogram of priority score distribution.

    Args:
        articles: List of article dicts with 'priority_score'.

    Returns:
        Plotly Figure.
    """
    if not articles:
        return _empty_chart("No articles yet")

    scores = [a.get("priority_score", 0) for a in articles]

    fig = go.Figure(go.Histogram(
        x=scores,
        nbinsx=20,
        marker=dict(
            color="#2196F3",
            line=dict(color="#1B2A4A", width=1),
            cornerradius=3,
        ),
        hovertemplate="Score range: %{x}<br>Count: %{y}<extra></extra>",
    ))

    # Add vertical lines for threshold markers
    fig.add_vline(x=80, line_dash="dash", line_color="#EF5350",
                  annotation_text="High", annotation_position="top")
    fig.add_vline(x=50, line_dash="dash", line_color="#FF9800",
                  annotation_text="Medium", annotation_position="top")

    fig.update_layout(
        title=dict(text="Priority Score Distribution", font=dict(size=16)),
        xaxis=dict(title="Priority Score", showgrid=False),
        yaxis=dict(title="Count", showgrid=True, gridcolor="rgba(0,0,0,0.06)"),
        height=350,
        **LAYOUT_DEFAULTS,
    )
    return fig


def articles_over_time(articles: list[dict]) -> go.Figure:
    """Line chart showing article volume over time.

    Args:
        articles: List of article dicts with 'scraped_time'.

    Returns:
        Plotly Figure.
    """
    if not articles:
        return _empty_chart("No articles yet")

    from datetime import datetime
    from collections import Counter

    # Group by date
    date_counts: dict[str, int] = Counter()
    for a in articles:
        ts = a.get("scraped_time", "")
        if ts:
            try:
                if isinstance(ts, str):
                    dt = datetime.fromisoformat(ts)
                else:
                    dt = ts
                date_str = dt.strftime("%Y-%m-%d")
                date_counts[date_str] += 1
            except (ValueError, TypeError):
                continue

    if not date_counts:
        return _empty_chart("No time data available")

    sorted_dates = sorted(date_counts.items())
    dates = [d[0] for d in sorted_dates]
    counts = [d[1] for d in sorted_dates]

    fig = go.Figure(go.Scatter(
        x=dates,
        y=counts,
        mode="lines+markers",
        line=dict(color="#2196F3", width=3),
        marker=dict(size=8, color="#1B2A4A"),
        fill="tozeroy",
        fillcolor="rgba(33, 150, 243, 0.1)",
        hovertemplate="<b>%{x}</b><br>Articles: %{y}<extra></extra>",
    ))

    fig.update_layout(
        title=dict(text="Articles Over Time", font=dict(size=16)),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.06)"),
        height=350,
        **LAYOUT_DEFAULTS,
    )
    return fig


def _empty_chart(message: str) -> go.Figure:
    """Create an empty chart with a centered message."""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=16, color="#999"),
    )
    fig.update_layout(
        height=300,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        **LAYOUT_DEFAULTS,
    )
    return fig
