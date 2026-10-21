"""
Reuters RSS scraper.

Uses Reuters RSS feeds instead of the blocked HTML pages.
"""

import logging
from bs4 import BeautifulSoup
from backend.services.scrapers.base_scraper import BaseScraper
from backend.services.scrapers.rss_fetcher import fetch_rss

logger = logging.getLogger(__name__)


class ReutersScraper(BaseScraper):
    source_name = "Reuters"
    base_url = "https://feeds.reuters.com/reuters/businessNews"

    RSS_FEEDS = [
        "https://feeds.reuters.com/reuters/businessNews",       # may vary by region
        "https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best",
        "https://news.google.com/rss/search?q=india+stock+market+mutual+funds&hl=en-IN&gl=IN&ceid=IN:en",
    ]

    def parse(self, soup: BeautifulSoup) -> list[dict]:
        return []

    def scrape(self) -> list[dict]:
        articles = []
        seen_urls = set()

        for feed_url in self.RSS_FEEDS:
            try:
                items = fetch_rss(feed_url, self.source_name, max_items=25)
                for item in items:
                    if item["url"] not in seen_urls:
                        seen_urls.add(item["url"])
                        articles.append(item)
            except Exception as e:
                logger.error("[Reuters] RSS feed %s failed: %s", feed_url, e)

        logger.info("[Reuters] RSS total: %d articles", len(articles))
        return articles
