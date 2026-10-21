"""
Dashboard stat card components.

Renders styled metric cards with custom CSS for a premium look.
"""

import streamlit as st


def render_stat_cards(stats: dict):
    """Render a row of 4 statistic cards.

    Args:
        stats: Dict with keys: total_articles, today_articles,
               high_priority, active_sources
    """
    st.markdown("""
    <style>
    .stat-card {
        background: linear-gradient(135deg, #1B2A4A 0%, #2C3E6B 100%);
        border-radius: 16px;
        padding: 24px 20px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(27, 42, 74, 0.25);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        border: 1px solid rgba(255,255,255,0.08);
    }
    .stat-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 30px rgba(27, 42, 74, 0.35);
    }
    .stat-icon {
        font-size: 32px;
        margin-bottom: 8px;
    }
    .stat-value {
        font-size: 36px;
        font-weight: 800;
        color: #FFFFFF;
        margin: 4px 0;
        letter-spacing: -1px;
    }
    .stat-label {
        font-size: 13px;
        color: rgba(255,255,255,0.7);
        text-transform: uppercase;
        letter-spacing: 1.2px;
        font-weight: 500;
    }
    </style>
    """, unsafe_allow_html=True)

    cols = st.columns(4)

    cards = [
        {
            "icon": "📰",
            "value": stats.get("total_articles", 0),
            "label": "Total Articles",
        },
        {
            "icon": "📅",
            "value": stats.get("today_articles", 0),
            "label": "Today's Articles",
        },
        {
            "icon": "🔥",
            "value": stats.get("high_priority", 0),
            "label": "High Priority",
        },
        {
            "icon": "🌐",
            "value": stats.get("active_sources", 0),
            "label": "Active Sources",
        },
    ]

    for col, card in zip(cols, cards):
        with col:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-icon">{card['icon']}</div>
                <div class="stat-value">{card['value']:,}</div>
                <div class="stat-label">{card['label']}</div>
            </div>
            """, unsafe_allow_html=True)


def render_priority_badge(score: int) -> str:
    """Return an HTML priority badge string.

    Args:
        score: Priority score (0–100).

    Returns:
        HTML string for the badge.
    """
    if score >= 80:
        bg = "#EF5350"
        label = "HIGH"
    elif score >= 50:
        bg = "#FF9800"
        label = "MED"
    else:
        bg = "#66BB6A"
        label = "LOW"

    return (
        f'<span style="background:{bg}; color:white; padding:3px 10px; '
        f'border-radius:12px; font-size:11px; font-weight:700; '
        f'letter-spacing:0.5px;">{score} {label}</span>'
    )
