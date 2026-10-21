"""
SQLAlchemy ORM models for the Financial News Intelligence Platform.

Single table design — Article stores all scraped, classified, and scored data.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Article(Base):
    """Represents a single scraped news article with classification and scoring."""

    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    headline = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=True)  # full article body (optional)
    source = Column(String(100), nullable=False)
    url = Column(String(500), unique=True, nullable=False)

    # Classification
    category = Column(String(50), default="General", nullable=False)
    companies = Column(Text, nullable=True)  # JSON array: '["TCS", "Infosys"]'
    sector = Column(String(50), nullable=True)
    country = Column(String(50), default="India")

    # Scoring
    priority_score = Column(Integer, default=0)

    # Timestamps
    published_time = Column(DateTime, nullable=True)
    scraped_time = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Deduplication
    duplicate_flag = Column(Boolean, default=False, nullable=False)

    # AI Summary (optional — populated only when Gemini API key is configured)
    executive_summary = Column(Text, nullable=True)

    # ── Indexes for fast queries ──────────────────────────────────────
    __table_args__ = (
        Index("idx_articles_category", "category"),
        Index("idx_articles_source", "source"),
        Index("idx_articles_priority", priority_score.desc()),
        Index("idx_articles_published", published_time.desc()),
        Index("idx_articles_scraped", scraped_time.desc()),
        Index("idx_articles_duplicate", "duplicate_flag"),
    )

    def __repr__(self):
        return (
            f"<Article(id={self.id}, source='{self.source}', "
            f"priority={self.priority_score}, category='{self.category}')>"
        )

    def to_dict(self) -> dict:
        """Serialize article to a dictionary for API responses."""
        import json

        return {
            "id": self.id,
            "headline": self.headline,
            "summary": self.summary,
            "content": self.content,
            "source": self.source,
            "url": self.url,
            "category": self.category,
            "companies": json.loads(self.companies) if self.companies else [],
            "sector": self.sector,
            "country": self.country,
            "priority_score": self.priority_score,
            "published_time": self.published_time.isoformat() if self.published_time else None,
            "scraped_time": self.scraped_time.isoformat() if self.scraped_time else None,
            "duplicate_flag": self.duplicate_flag,
            "executive_summary": self.executive_summary,
        }
