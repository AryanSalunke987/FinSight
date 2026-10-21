"""
Priority Scoring Agent.

Every article receives a priority score (0–100) based on a weighted formula:

  Priority = (keyword_impact  × 0.35)
           + (source_cred     × 0.20)
           + (freshness       × 0.20)
           + (category_import × 0.15)
           + (entity_signal   × 0.10)

No LLMs involved — purely rule-based scoring.
"""

import json
import logging
import re
from datetime import datetime, timezone

from backend.config import config

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════════
# KEYWORD IMPACT SCORES — high-impact financial events
# ══════════════════════════════════════════════════════════════════════════════
# Each tuple: (pattern, score)  — pattern is matched case-insensitively
KEYWORD_IMPACT: list[tuple[str, int]] = [
    # Tier 1: Market-moving events (90–100)
    (r"union budget", 100),
    (r"rbi.*polic", 95),
    (r"monetary policy", 95),
    (r"repo rate", 93),
    (r"interest rate.*cut", 93),
    (r"interest rate.*hike", 93),
    (r"quarterly (result|earning)", 90),
    (r"q[1-4]\s*(result|earning)", 90),

    # Tier 2: Significant events (80–89)
    (r"sebi.*circular", 88),
    (r"sebi.*order", 88),
    (r"sebi.*regulation", 85),
    (r"merger.*acqui", 85),
    (r"acquisition", 85),
    (r"takeover", 85),
    (r"delisting", 83),
    (r"bankruptcy", 82),
    (r"gdp.*growth", 80),
    (r"inflation.*data", 80),
    (r"fiscal deficit", 80),

    # Tier 3: Notable events (70–79)
    (r"ipo.*open", 78),
    (r"ipo.*listing", 78),
    (r"ipo.*launch", 75),
    (r"block deal", 75),
    (r"bulk deal", 75),
    (r"fii.*buy", 74),
    (r"fii.*sell", 74),
    (r"dividend", 72),
    (r"bonus.*share", 72),
    (r"stock split", 72),
    (r"share buyback", 72),
    (r"fund raise", 70),
    (r"qip", 70),
    (r"rights issue", 70),

    # Tier 4: Moderate events (55–69)
    (r"ceo.*appoint", 60),
    (r"cfo.*appoint", 58),
    (r"board.*appoint", 55),
    (r"management.*change", 55),
    (r"rating.*upgrade", 65),
    (r"rating.*downgrade", 65),
    (r"target price", 60),
    (r"buy.*recommend", 58),
    (r"sell.*recommend", 58),
    (r"analyst.*call", 55),

    # Tier 5: Routine items (20–50)
    (r"market.*open", 45),
    (r"market.*close", 45),
    (r"sensex.*nifty", 40),
    (r"top.*gainer", 35),
    (r"top.*loser", 35),
    (r"technical.*analysis", 30),
    (r"chart.*pattern", 25),
    (r"opinion", 20),
    (r"commentary", 20),
    (r"blog", 15),
]

# ── Category importance scores (0.0 – 1.0) ───────────────────────────────────
CATEGORY_IMPORTANCE: dict[str, float] = {
    "Government Policy": 1.0,
    "Economy": 1.0,
    "Banking": 0.9,
    "Corporate Results": 0.9,
    "IPO": 0.85,
    "Mutual Funds": 0.85,
    "Energy": 0.8,
    "IT": 0.8,
    "Pharma": 0.8,
    "Auto": 0.75,
    "Global Markets": 0.75,
    "Currency": 0.75,
    "Commodities": 0.7,
    "Gold": 0.65,
    "Silver": 0.6,
    "Cryptocurrency": 0.55,
    "General": 0.3,
}


def _score_keyword_impact(text: str) -> float:
    """Score article text based on high-impact keyword matches.

    Returns a value between 0 and 100.
    """
    text_lower = text.lower()
    max_score = 0

    for pattern, score in KEYWORD_IMPACT:
        if re.search(pattern, text_lower, re.IGNORECASE):
            max_score = max(max_score, score)

    return float(max_score)


def _score_source_credibility(source: str) -> float:
    """Score based on source credibility.

    Returns a value between 0 and 100.
    """
    cred = config.SOURCE_CREDIBILITY.get(source, 0.5)
    return cred * 100


def _score_freshness(published_time, scraped_time) -> float:
    """Score based on article freshness.

    Returns a value between 0 and 100.
    """
    now = datetime.now(timezone.utc)

    # Use published_time if available, else scraped_time
    reference_time = published_time or scraped_time or now

    # Ensure timezone-aware comparison
    if reference_time.tzinfo is None:
        reference_time = reference_time.replace(tzinfo=timezone.utc)

    hours_old = (now - reference_time).total_seconds() / 3600

    if hours_old < 1:
        return 100.0
    elif hours_old < 3:
        return 90.0
    elif hours_old < 6:
        return 80.0
    elif hours_old < 12:
        return 60.0
    elif hours_old < 24:
        return 50.0
    elif hours_old < 48:
        return 30.0
    else:
        return 20.0


def _score_category_importance(category: str) -> float:
    """Score based on category importance.

    Returns a value between 0 and 100.
    """
    importance = CATEGORY_IMPORTANCE.get(category, 0.3)
    return importance * 100


def _score_entity_count(companies_json: str) -> float:
    """Score based on the number of named entities (companies).

    More companies mentioned = more relevant / broader impact.
    Returns a value between 0 and 100.
    """
    try:
        companies = json.loads(companies_json) if companies_json else []
    except (json.JSONDecodeError, TypeError):
        companies = []

    count = len(companies)
    if count >= 5:
        return 100.0
    elif count >= 3:
        return 80.0
    elif count >= 2:
        return 60.0
    elif count == 1:
        return 40.0
    else:
        return 10.0


def score_article(article: dict) -> dict:
    """Compute the priority score for a single article.

    Modifies the article dict in-place, adding 'priority_score'.

    Args:
        article: Dict with headline, summary, source, category, companies, etc.

    Returns:
        The same dict with priority_score added.
    """
    text = f"{article.get('headline', '')} {article.get('summary', '')}"

    keyword_score = _score_keyword_impact(text)
    source_score = _score_source_credibility(article.get("source", ""))
    freshness_score = _score_freshness(
        article.get("published_time"),
        article.get("scraped_time"),
    )
    category_score = _score_category_importance(article.get("category", "General"))
    entity_score = _score_entity_count(article.get("companies", "[]"))

    # Weighted sum
    priority = (
        keyword_score * config.WEIGHT_KEYWORD
        + source_score * config.WEIGHT_SOURCE
        + freshness_score * config.WEIGHT_FRESHNESS
        + category_score * config.WEIGHT_CATEGORY
        + entity_score * config.WEIGHT_ENTITY
    )

    # Clamp to 0–100 and round to integer
    article["priority_score"] = max(0, min(100, round(priority)))

    return article


def score_articles(articles: list[dict]) -> list[dict]:
    """Compute priority scores for a batch of articles.

    Args:
        articles: List of classified article dicts.

    Returns:
        Same list with priority_score added to each article.
    """
    if not articles:
        return articles

    logger.info("[Priority] Scoring %d articles...", len(articles))

    for article in articles:
        score_article(article)

    # Log priority distribution
    high = sum(1 for a in articles if a.get("priority_score", 0) >= 80)
    medium = sum(1 for a in articles if 50 <= a.get("priority_score", 0) < 80)
    low = sum(1 for a in articles if a.get("priority_score", 0) < 50)

    logger.info(
        "[Priority] Distribution -- High (>=80): %d | Medium (50-79): %d | Low (<50): %d",
        high, medium, low,
    )

    return articles
