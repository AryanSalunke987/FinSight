"""
Moneycontrol RSS scraper.

RSS feed: https://www.moneycontrol.com/rss/marketreports.xml
Provides real-time markets news without any JS rendering.
"""

import logging
from bs4 import BeautifulSoup
from backend.services.scrapers.base_scraper import BaseScraper
from backend.services.scrapers.rss_fetcher import fetch_rss

logger = logging.getLogger(__name__)


class MoneycontrolScraper(BaseScraper):
    source_name = "Moneycontrol"
    base_url = "https://www.moneycontrol.com/rss/marketreports.xml"

    # Multiple RSS feeds to maximize coverage
    RSS_FEEDS = [
        "https://www.moneycontrol.com/rss/marketreports.xml",
        "https://www.moneycontrol.com/rss/business.xml",
        "https://www.moneycontrol.com/rss/economy.xml",
    ]

    def parse(self, soup: BeautifulSoup) -> list[dict]:
        """Not used — RSS fetcher overrides scrape() directly."""
        return []

    def scrape(self) -> list[dict]:
        """Fetch from multiple RSS feeds and deduplicate by URL."""
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
                logger.error("[Moneycontrol] RSS feed %s failed: %s", feed_url, e)

        logger.info("[Moneycontrol] RSS total: %d articles", len(articles))
        return articles
