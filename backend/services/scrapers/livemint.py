"""
LiveMint RSS scraper.

RSS feeds: livemint.com provides structured RSS.
"""

import logging
from bs4 import BeautifulSoup
from backend.services.scrapers.base_scraper import BaseScraper
from backend.services.scrapers.rss_fetcher import fetch_rss

logger = logging.getLogger(__name__)


class LiveMintScraper(BaseScraper):
    source_name = "LiveMint"
    base_url = "https://www.livemint.com/rss/markets"

    RSS_FEEDS = [
        "https://www.livemint.com/rss/markets",
        "https://www.livemint.com/rss/companies",
        "https://www.livemint.com/rss/economy",
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
                logger.error("[LiveMint] RSS feed %s failed: %s", feed_url, e)

        logger.info("[LiveMint] RSS total: %d articles", len(articles))
        return articles
