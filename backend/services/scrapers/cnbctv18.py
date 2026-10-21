"""
CNBC TV18 RSS scraper.

Uses CNBC TV18 RSS instead of JS-rendered HTML.
"""

import logging
from bs4 import BeautifulSoup
from backend.services.scrapers.base_scraper import BaseScraper
from backend.services.scrapers.rss_fetcher import fetch_rss

logger = logging.getLogger(__name__)


class CNBCTV18Scraper(BaseScraper):
    source_name = "CNBC TV18"
    base_url = "https://www.cnbctv18.com/commonfeeds/v1/cne/rss/market.xml"

    RSS_FEEDS = [
        "https://www.cnbctv18.com/commonfeeds/v1/cne/rss/market.xml",
        "https://www.cnbctv18.com/commonfeeds/v1/cne/rss/finance.xml",
        "https://www.cnbctv18.com/commonfeeds/v1/cne/rss/economy.xml",
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
                logger.error("[CNBCTV18] RSS feed %s failed: %s", feed_url, e)

        logger.info("[CNBCTV18] RSS total: %d articles", len(articles))
        return articles
