"""
Centralized configuration for the Financial News Intelligence Platform.

All configurable values are defined here. To change behavior,
modify this file — no .env parsing needed for a local project.
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Config:
    """Application configuration."""

    # ── Paths ──────────────────────────────────────────────────────────
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR: str = field(init=False)
    LOG_DIR: str = field(init=False)
    DB_PATH: str = field(init=False)
    LOG_FILE: str = field(init=False)

    # ── Database ───────────────────────────────────────────────────────
    DB_ECHO: bool = False  # Set True to log SQL statements

    # ── Scraping ───────────────────────────────────────────────────────
    SCRAPE_INTERVAL_HOURS: int = 2
    REQUEST_TIMEOUT: int = 15  # seconds
    MAX_RETRIES: int = 3
    RETRY_BACKOFF: float = 2.0  # exponential backoff base
    USER_AGENTS: list = field(default_factory=lambda: [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/17.4 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
    ])

    # ── Deduplication ──────────────────────────────────────────────────
    FUZZY_DUPLICATE_THRESHOLD: int = 85  # RapidFuzz similarity (0–100)

    # ── Priority Scoring Weights ───────────────────────────────────────
    WEIGHT_KEYWORD: float = 0.35
    WEIGHT_SOURCE: float = 0.20
    WEIGHT_FRESHNESS: float = 0.20
    WEIGHT_CATEGORY: float = 0.15
    WEIGHT_ENTITY: float = 0.10

    # ── Source Credibility Scores (0.0 – 1.0) ─────────────────────────
    SOURCE_CREDIBILITY: dict = field(default_factory=lambda: {
        "Reuters": 1.0,
        "Moneycontrol": 0.9,
        "Economic Times": 0.9,
        "LiveMint": 0.85,
        "Business Standard": 0.85,
        "CNBC TV18": 0.8,
    })

    # ── API ────────────────────────────────────────────────────────────
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000

    # ── AI Summary (Optional) ─────────────────────────────────────────
    GEMINI_API_KEY: Optional[str] = None  # Set to enable AI summaries
    AI_SUMMARY_MIN_PRIORITY: int = 75
    AI_SUMMARY_MAX_PER_CYCLE: int = 10

    # ── Logging ────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"

    def __post_init__(self):
        self.DATA_DIR = os.path.join(self.BASE_DIR, "data")
        self.LOG_DIR = os.path.join(self.BASE_DIR, "logs")
        self.DB_PATH = os.path.join(self.DATA_DIR, "news.db")
        self.LOG_FILE = os.path.join(self.LOG_DIR, "app.log")

        # Ensure directories exist
        os.makedirs(self.DATA_DIR, exist_ok=True)
        os.makedirs(self.LOG_DIR, exist_ok=True)


# Singleton config instance used throughout the application
config = Config()
