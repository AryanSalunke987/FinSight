"""
Cleaning & Deduplication Agent.

Responsibilities:
  1. Normalize whitespace, URLs (remove tracking params), and text encoding
  2. Remove articles with empty headlines or summaries
  3. Exact dedup: skip articles whose URL already exists in the database
  4. Fuzzy dedup: use RapidFuzz to detect near-duplicate headlines
     and flag the newer article as duplicate
"""

import logging
import re
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

from rapidfuzz import fuzz

from backend.config import config
from backend.database.database import session_scope
from backend.database.models import Article

logger = logging.getLogger(__name__)

# URL tracking parameters to strip during normalization
_TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term",
    "ref", "source", "fbclid", "gclid", "mc_cid", "mc_eid",
}

# Patterns that indicate promotional / ad content
_AD_PATTERNS = [
    re.compile(r"sponsored", re.IGNORECASE),
    re.compile(r"advertisement", re.IGNORECASE),
    re.compile(r"partner content", re.IGNORECASE),
    re.compile(r"promoted story", re.IGNORECASE),
    re.compile(r"brand(ed)? (content|post|story)", re.IGNORECASE),
]


def _normalize_whitespace(text: str) -> str:
    """Collapse multiple whitespace characters into single spaces."""
    if not text:
        return ""
    return " ".join(text.split()).strip()


def _normalize_url(url: str) -> str:
    """Remove tracking parameters and normalize URL structure."""
    try:
        parsed = urlparse(url)
        # Filter out tracking query params
        query_params = parse_qs(parsed.query, keep_blank_values=False)
        clean_params = {
            k: v for k, v in query_params.items()
            if k.lower() not in _TRACKING_PARAMS
        }
        clean_query = urlencode(clean_params, doseq=True)
        # Remove fragment and rebuild
        clean_url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path.rstrip("/"),
            parsed.params,
            clean_query,
            "",  # no fragment
        ))
        return clean_url
    except Exception:
        return url


def _is_ad_content(headline: str, summary: str) -> bool:
    """Check if article is likely an advertisement."""
    combined = f"{headline} {summary}"
    return any(pattern.search(combined) for pattern in _AD_PATTERNS)


def _get_existing_urls() -> set[str]:
    """Fetch all existing article URLs from the database."""
    with session_scope() as session:
        rows = session.query(Article.url).all()
        return {row[0] for row in rows}


def _get_recent_headlines() -> list[tuple[int, str]]:
    """Fetch recent non-duplicate article headlines for fuzzy matching.

    Returns list of (id, headline) tuples from the last 500 articles.
    """
    with session_scope() as session:
        rows = (
            session.query(Article.id, Article.headline)
            .filter(Article.duplicate_flag == False)  # noqa: E712
            .order_by(Article.scraped_time.desc())
            .limit(500)
            .all()
        )
        return [(row[0], row[1]) for row in rows]


def clean_and_deduplicate(raw_articles: list[dict]) -> list[dict]:
    """Clean, normalize, and deduplicate raw articles.

    Args:
        raw_articles: List of article dicts from the collection agent.

    Returns:
        List of cleaned, deduplicated article dicts ready for classification.
        Each dict has an additional 'duplicate_flag' key.
    """
    if not raw_articles:
        logger.info("[Cleaning] No articles to process.")
        return []

    logger.info("[Cleaning] Processing %d raw articles...", len(raw_articles))

    # Step 1: Normalize text fields
    for article in raw_articles:
        article["headline"] = _normalize_whitespace(article.get("headline", ""))
        article["summary"] = _normalize_whitespace(article.get("summary", ""))
        article["url"] = _normalize_url(article.get("url", ""))

    # Step 2: Remove empty / ad content
    filtered = []
    removed_empty = 0
    removed_ads = 0

    for article in raw_articles:
        if not article["headline"] or not article["url"]:
            removed_empty += 1
            continue
        if _is_ad_content(article["headline"], article["summary"]):
            removed_ads += 1
            continue
        filtered.append(article)

    if removed_empty:
        logger.info("[Cleaning] Removed %d articles with empty headline/URL", removed_empty)
    if removed_ads:
        logger.info("[Cleaning] Removed %d ad/promotional articles", removed_ads)

    # Step 3: Exact dedup — skip articles already in the database (by URL)
    existing_urls = _get_existing_urls()
    new_articles = []
    skipped_exact = 0

    # Also track URLs within this batch to avoid intra-batch duplicates
    batch_urls = set()

    for article in filtered:
        url = article["url"]
        if url in existing_urls or url in batch_urls:
            skipped_exact += 1
            continue
        batch_urls.add(url)
        new_articles.append(article)

    if skipped_exact:
        logger.info("[Cleaning] Skipped %d exact duplicate URLs", skipped_exact)

    # Step 4: Fuzzy dedup — compare new headlines against existing DB headlines
    existing_headlines = _get_recent_headlines()
    threshold = config.FUZZY_DUPLICATE_THRESHOLD
    fuzzy_dupes = 0

    for article in new_articles:
        article["duplicate_flag"] = False
        headline = article["headline"]

        # Check against existing DB headlines
        for _existing_id, existing_headline in existing_headlines:
            similarity = fuzz.token_sort_ratio(headline, existing_headline)
            if similarity >= threshold:
                article["duplicate_flag"] = True
                fuzzy_dupes += 1
                logger.debug(
                    "[Cleaning] Fuzzy duplicate (%.0f%%): '%s' ~ '%s'",
                    similarity, headline[:60], existing_headline[:60],
                )
                break

        # Also check against other new articles in this batch (if not already flagged)
        if not article["duplicate_flag"]:
            for other in new_articles:
                if other is article or other.get("duplicate_flag"):
                    continue
                similarity = fuzz.token_sort_ratio(headline, other["headline"])
                if similarity >= threshold:
                    article["duplicate_flag"] = True
                    fuzzy_dupes += 1
                    break

    if fuzzy_dupes:
        logger.info("[Cleaning] Flagged %d fuzzy duplicate articles", fuzzy_dupes)

    clean_count = sum(1 for a in new_articles if not a["duplicate_flag"])
    logger.info(
        "[Cleaning] Result: %d new articles (%d clean, %d fuzzy duplicates)",
        len(new_articles), clean_count, fuzzy_dupes,
    )
    return new_articles
