"""
Abstract base class for all news scrapers.

Every scraper inherits from BaseScraper and implements the `parse()` method.
The base class provides:
  - Retry logic with exponential backoff
  - Rotating user-agent headers
  - Standardized error logging
  - Consistent return format
"""

import logging
import random
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional

import requests
from bs4 import BeautifulSoup

from backend.config import config

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Base class for all financial news scrapers.

    Subclasses must define:
        source_name: str — human-readable source name (e.g., "Moneycontrol")
        base_url: str — the URL to scrape
        parse(soup) -> list[dict] — extract articles from parsed HTML
    """

    source_name: str = ""
    base_url: str = ""

    def __init__(self):
        self.session = requests.Session()

    def _get_headers(self) -> dict:
        """Return request headers with a randomly selected user-agent."""
        return {
            "User-Agent": random.choice(config.USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }

    def fetch(self, url: Optional[str] = None) -> Optional[BeautifulSoup]:
        """Fetch a URL with retry logic and return parsed BeautifulSoup.

        Args:
            url: URL to fetch. Defaults to self.base_url.

        Returns:
            BeautifulSoup object or None if all retries fail.
        """
        target_url = url or self.base_url

        for attempt in range(1, config.MAX_RETRIES + 1):
            try:
                response = self.session.get(
                    target_url,
                    headers=self._get_headers(),
                    timeout=config.REQUEST_TIMEOUT,
                )
                response.raise_for_status()
                soup = BeautifulSoup(response.content, "html.parser")
                logger.debug(
                    "[%s] Fetched %s (attempt %d, %d bytes)",
                    self.source_name, target_url, attempt, len(response.content),
                )
                return soup

            except requests.exceptions.RequestException as e:
                wait_time = config.RETRY_BACKOFF ** attempt
                logger.warning(
                    "[%s] Attempt %d/%d failed for %s: %s. Retrying in %.1fs...",
                    self.source_name, attempt, config.MAX_RETRIES,
                    target_url, str(e), wait_time,
                )
                if attempt < config.MAX_RETRIES:
                    time.sleep(wait_time)

        logger.error(
            "[%s] All %d attempts failed for %s",
            self.source_name, config.MAX_RETRIES, target_url,
        )
        return None

    @abstractmethod
    def parse(self, soup: BeautifulSoup) -> list[dict]:
        """Parse HTML and extract articles.

        Each article dict must contain:
            - headline: str
            - summary: str (can be empty)
            - url: str (full URL)
            - source: str
            - published_time: datetime or None
        """
        ...

    def scrape(self) -> list[dict]:
        """Run the full scrape pipeline: fetch → parse → return.

        Returns:
            List of article dicts. Empty list on failure.
        """
        logger.info("[%s] Starting scrape from %s", self.source_name, self.base_url)

        soup = self.fetch()
        if soup is None:
            return []

        try:
            articles = self.parse(soup)
            # Ensure every article has the source and scraped_time
            for article in articles:
                article.setdefault("source", self.source_name)
                article.setdefault("scraped_time", datetime.now(timezone.utc))
            logger.info(
                "[%s] Successfully scraped %d articles", self.source_name, len(articles)
            )
            return articles

        except Exception as e:
            logger.error(
                "[%s] Parse error: %s", self.source_name, str(e), exc_info=True
            )
            return []
