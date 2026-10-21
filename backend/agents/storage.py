"""
Storage Agent — persists processed articles to SQLite via SQLAlchemy.

Receives cleaned, classified, and scored articles and performs
inserts one at a time, each in its own session, so a failure on
one article never aborts the entire batch.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError

from backend.database.database import get_session
from backend.database.models import Article

logger = logging.getLogger(__name__)


def _store_single(article_data: dict) -> str:
    """Insert a single article in its own session.

    Returns:
        'inserted', 'skipped', or 'error'.
    """
    session = get_session()
    try:
        article = Article(
            headline=article_data.get("headline", ""),
            summary=article_data.get("summary"),
            content=article_data.get("content"),
            source=article_data.get("source", "Unknown"),
            url=article_data.get("url", ""),
            category=article_data.get("category", "General"),
            companies=article_data.get("companies", "[]"),
            sector=article_data.get("sector"),
            country=article_data.get("country", "India"),
            priority_score=article_data.get("priority_score", 0),
            published_time=article_data.get("published_time"),
            scraped_time=article_data.get(
                "scraped_time", datetime.now(timezone.utc)
            ),
            duplicate_flag=article_data.get("duplicate_flag", False),
            executive_summary=article_data.get("executive_summary"),
        )
        session.add(article)
        session.commit()
        return "inserted"
    except IntegrityError:
        session.rollback()
        logger.debug(
            "[Storage] Skipped duplicate URL: %s",
            article_data.get("url", "")[:80],
        )
        return "skipped"
    except Exception as e:
        session.rollback()
        logger.error(
            "[Storage] Error storing article '%s': %s",
            article_data.get("headline", "")[:60],
            str(e),
        )
        return "error"
    finally:
        session.close()


def store_articles(articles: list[dict]) -> dict:
    """Store processed articles into the database.

    Each article is inserted in its own session so that a duplicate
    or error on one row never rolls back the whole batch.

    Args:
        articles: List of fully processed article dicts.

    Returns:
        Dict with keys: inserted, skipped, errors.
    """
    if not articles:
        logger.info("[Storage] No articles to store.")
        return {"inserted": 0, "skipped": 0, "errors": 0}

    logger.info("[Storage] Storing %d articles...", len(articles))

    inserted = skipped = errors = 0
    for article_data in articles:
        result = _store_single(article_data)
        if result == "inserted":
            inserted += 1
        elif result == "skipped":
            skipped += 1
        else:
            errors += 1

    logger.info(
        "[Storage] Complete -- Inserted: %d | Skipped: %d | Errors: %d",
        inserted, skipped, errors,
    )
    return {"inserted": inserted, "skipped": skipped, "errors": errors}
