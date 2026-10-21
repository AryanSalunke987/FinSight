"""
Business Standard RSS scraper.

Uses RSS instead of direct HTML scraping to bypass 403 blocks.
"""

import logging
from bs4 import BeautifulSoup
from backend.services.scrapers.base_scraper import BaseScraper
from backend.services.scrapers.rss_fetcher import fetch_rss

logger = logging.getLogger(__name__)


class BusinessStandardScraper(BaseScraper):
    source_name = "Business Standard"
    base_url = "https://www.business-standard.com/rss/markets-106.rss"

    RSS_FEEDS = [
        "https://www.business-standard.com/rss/markets-106.rss",
        "https://www.business-standard.com/rss/finance-103.rss",
        "https://www.business-standard.com/rss/economy-policy-102.rss",
    ]

    def parse(self, soup: BeautifulSoup) -> list[dict]:
        return []

    def scrape(self) -> list[dict]:
        articles = []
        seen_urls = set()

        for feed_url in self.RSS_FEEDS:
            try:
                items = fetch_rss(feed_url, self.source_name, max_items=30)
                for item in items:
                    if item["url"] not in seen_urls:
                        seen_urls.add(item["url"])
                        articles.append(item)
            except Exception as e:
                logger.error("[BusinessStandard] RSS feed %s failed: %s", feed_url, e)

        logger.info("[BusinessStandard] RSS total: %d articles", len(articles))
        return articles
