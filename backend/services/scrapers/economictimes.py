"""
Economic Times RSS scraper.

RSS feeds: economictimes.indiatimes.com provides multiple feeds.
"""

import logging
from bs4 import BeautifulSoup
from backend.services.scrapers.base_scraper import BaseScraper
from backend.services.scrapers.rss_fetcher import fetch_rss

logger = logging.getLogger(__name__)


class EconomicTimesScraper(BaseScraper):
    source_name = "Economic Times"
    base_url = "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"

    RSS_FEEDS = [
        "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",   # Markets
        "https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.cms",  # Stocks
        "https://economictimes.indiatimes.com/news/economy/rssfeeds/897228639.cms",  # Economy
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
                logger.error("[EconomicTimes] RSS feed %s failed: %s", feed_url, e)

        logger.info("[EconomicTimes] RSS total: %d articles", len(articles))
        return articles
