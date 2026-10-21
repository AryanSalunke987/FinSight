"""
Scheduler — runs the full news processing pipeline on a recurring schedule.

Uses APScheduler BackgroundScheduler to trigger scraping every N hours.
Also provides a function to run the pipeline on-demand.
"""

import logging
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from backend.config import config

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def run_pipeline() -> dict:
    """Execute the full news processing pipeline.

    Pipeline stages:
        1. Collect → scrape all sources
        2. Clean   → normalize, deduplicate
        3. Classify → rule-based sector classification
        4. Score   → priority scoring
        5. Store   → persist to SQLite

    Returns:
        Dict with pipeline statistics.
    """
    start_time = datetime.now(timezone.utc)
    logger.info("============================================")
    logger.info("  PIPELINE STARTED: %s", start_time.strftime("%Y-%m-%d %H:%M UTC"))
    logger.info("============================================")

    # Import here to avoid circular imports at module level
    from backend.agents.news_collection import collect_news
    from backend.agents.cleaning import clean_and_deduplicate
    from backend.agents.classification import classify_articles
    from backend.agents.priority import score_articles
    from backend.agents.storage import store_articles

    # Stage 1: Collect
    raw_articles = collect_news()

    # Stage 2: Clean & Deduplicate
    cleaned_articles = clean_and_deduplicate(raw_articles)

    # Stage 3: Classify
    classified_articles = classify_articles(cleaned_articles)

    # Stage 4: Score
    scored_articles = score_articles(classified_articles)

    # Stage 5: Store
    storage_result = store_articles(scored_articles)

    elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()

    result = {
        "raw_count": len(raw_articles),
        "cleaned_count": len(cleaned_articles),
        "inserted": storage_result["inserted"],
        "skipped": storage_result["skipped"],
        "errors": storage_result["errors"],
        "elapsed_seconds": round(elapsed, 1),
        "timestamp": start_time.isoformat(),
    }

    logger.info("============================================")
    logger.info("  PIPELINE COMPLETE")
    logger.info("  Raw: %3d -> Cleaned: %3d -> Stored: %3d",
                result["raw_count"], result["cleaned_count"], result["inserted"])
    logger.info("  Elapsed: %.1fs", elapsed)
    logger.info("============================================")

    return result


def start_scheduler():
    """Start the background scheduler that runs the pipeline periodically."""
    global _scheduler

    if _scheduler is not None and _scheduler.running:
        logger.warning("[Scheduler] Already running. Skipping start.")
        return

    _scheduler = BackgroundScheduler(
        job_defaults={"coalesce": True, "max_instances": 1}
    )

    _scheduler.add_job(
        run_pipeline,
        trigger=IntervalTrigger(hours=config.SCRAPE_INTERVAL_HOURS),
        id="news_pipeline",
        name="News Processing Pipeline",
        replace_existing=True,
    )

    _scheduler.start()

    next_run = _scheduler.get_job("news_pipeline").next_run_time
    logger.info(
        "[Scheduler] Started. Pipeline runs every %d hours. Next run: %s",
        config.SCRAPE_INTERVAL_HOURS,
        next_run.strftime("%Y-%m-%d %H:%M") if next_run else "unknown",
    )


def stop_scheduler():
    """Gracefully shutdown the scheduler."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("[Scheduler] Stopped.")
        _scheduler = None


def get_scheduler_status() -> dict:
    """Return current scheduler status for the dashboard."""
    if _scheduler is None or not _scheduler.running:
        return {"running": False, "next_run": None}

    job = _scheduler.get_job("news_pipeline")
    next_run = job.next_run_time if job else None

    return {
        "running": True,
        "next_run": next_run.isoformat() if next_run else None,
        "interval_hours": config.SCRAPE_INTERVAL_HOURS,
    }
