"""
RSS-based news scraper base class.

All modern Indian financial news sites provide RSS feeds.
RSS is plain XML — no JavaScript rendering, no anti-bot blocks,
freely accessible, and designed for programmatic consumption.

This replaces the HTML scraper approach for sites that serve
JS-rendered pages to HTTP clients.
"""

import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# Shared session for RSS fetches
_session: Optional[requests.Session] = None


def _get_session() -> requests.Session:
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; RSSReader/1.0)",
            "Accept": "application/rss+xml,application/xml,text/xml;q=0.9,*/*;q=0.8",
        })
    return _session


def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse RFC 2822 date from RSS into UTC datetime."""
    if not date_str:
        return None
    try:
        dt = parsedate_to_datetime(date_str.strip())
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    except Exception:
        try:
            # Fallback: try ISO format
            return datetime.fromisoformat(date_str.strip())
        except Exception:
            return None


def fetch_rss(url: str, source_name: str, max_items: int = 50) -> list[dict]:
    """Fetch and parse an RSS feed, returning standardized article dicts.

    Args:
        url: RSS feed URL.
        source_name: Display name for the source.
        max_items: Maximum number of articles to return.

    Returns:
        List of article dicts with keys:
        headline, summary, url, source, published_time, scraped_time.
    """
    session = _get_session()
    articles = []

    try:
        resp = session.get(url, timeout=20)
        resp.raise_for_status()
        content = resp.content

        # Parse XML
        root = ET.fromstring(content)

        # Handle both RSS 2.0 and Atom feeds
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        items = root.findall(".//item")  # RSS 2.0
        if not items:
            items = root.findall(".//atom:entry", ns)  # Atom

        now = datetime.now(timezone.utc).replace(tzinfo=None)

        for item in items[:max_items]:
            try:
                # Title
                title_el = item.find("title")
                if title_el is None:
                    continue
                title = (title_el.text or "").strip()
                # Strip CDATA if present
                if title.startswith("<![CDATA["):
                    title = title[9:-3].strip()
                if not title or len(title) < 10:
                    continue

                # Link
                link_el = item.find("link")
                link = (link_el.text or "").strip() if link_el is not None else ""
                if not link:
                    # Atom style
                    link_el = item.find("atom:link", ns)
                    if link_el is not None:
                        link = link_el.get("href", "")
                if not link:
                    continue

                # Description / Summary
                desc_el = item.find("description")
                summary = ""
                if desc_el is not None and desc_el.text:
                    raw = desc_el.text.strip()
                    if raw.startswith("<![CDATA["):
                        raw = raw[9:-3].strip()
                    # Strip HTML tags from summary
                    import re
                    summary = re.sub(r"<[^>]+>", "", raw).strip()[:500]

                # Published time
                pub_date_el = item.find("pubDate")
                pub_date = None
                if pub_date_el is not None:
                    pub_date = _parse_date(pub_date_el.text)
                if pub_date is None:
                    # Atom
                    updated_el = item.find("atom:updated", ns)
                    if updated_el is not None:
                        pub_date = _parse_date(updated_el.text)

                articles.append({
                    "headline": title,
                    "summary": summary,
                    "url": link,
                    "source": source_name,
                    "published_time": pub_date,
                    "scraped_time": now,
                })

            except Exception as e:
                logger.debug("[RSS:%s] Skipped item: %s", source_name, e)
                continue

        logger.info("[RSS:%s] Fetched %d articles", source_name, len(articles))

    except requests.RequestException as e:
        logger.error("[RSS:%s] Fetch failed: %s", source_name, e)
    except ET.ParseError as e:
        logger.error("[RSS:%s] XML parse error: %s", source_name, e)
    except Exception as e:
        logger.error("[RSS:%s] Unexpected error: %s", source_name, e)

    return articles
