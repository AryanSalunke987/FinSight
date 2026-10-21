"""
News Collection Agent — orchestrates all scrapers.

Iterates through the scraper registry, runs each scraper,
aggregates results, and logs per-source statistics.
"""

import logging
from datetime import datetime, timezone

from backend.services.scrapers import SCRAPER_REGISTRY

logger = logging.getLogger(__name__)


def collect_news() -> list[dict]:
    """Run all registered scrapers and return aggregated raw articles.

    Returns:
        List of article dicts from all sources. Each dict contains:
        headline, summary, url, source, published_time, scraped_time.
    """
    all_articles = []
    source_counts = {}
    errors = []

    scrape_start = datetime.now(timezone.utc)
    logger.info(
        "=== News Collection started at %s ===",
        scrape_start.strftime("%Y-%m-%d %H:%M:%S UTC"),
    )

    for scraper_class in SCRAPER_REGISTRY:
        scraper_name = scraper_class.source_name
        try:
            scraper = scraper_class()
            articles = scraper.scrape()
            source_counts[scraper_name] = len(articles)
            all_articles.extend(articles)
        except Exception as e:
            errors.append(scraper_name)
            source_counts[scraper_name] = 0
            logger.error(
                "[Collection] %s failed entirely: %s", scraper_name, str(e),
                exc_info=True,
            )

    # Log summary
    total = len(all_articles)
    elapsed = (datetime.now(timezone.utc) - scrape_start).total_seconds()

    logger.info("=== News Collection Summary ===")
    for source, count in source_counts.items():
        status = "[OK]" if source not in errors else "[FAIL]"
        logger.info("  %s %s: %d articles", status, source, count)
    logger.info("  Total: %d articles in %.1f seconds", total, elapsed)
    if errors:
        logger.warning("  Failed sources: %s", ", ".join(errors))
    logger.info("===============================")

    return all_articles
