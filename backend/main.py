"""
FastAPI application — provides REST API for the dashboard and exports.

Endpoints:
    GET  /api/articles  — paginated articles with filtering
    GET  /api/stats     — dashboard statistics
    GET  /api/trending  — trending companies and sectors
    POST /api/scrape    — trigger manual pipeline run
    GET  /api/export/excel — download filtered articles as Excel
    GET  /api/export/pdf   — download filtered articles as PDF
    GET  /api/scheduler    — scheduler status
"""

import logging
import sys
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, desc, case, and_

from backend.config import config
from backend.database.database import init_db, session_scope
from backend.database.models import Article
from backend.services.scheduler import (
    start_scheduler,
    stop_scheduler,
    run_pipeline,
    get_scheduler_status,
)

# ── Logging setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(config.LOG_FILE, encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


# ── Application lifespan ─────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init DB + start scheduler. Shutdown: stop scheduler."""
    logger.info("Starting Financial News Intelligence Platform...")
    init_db()
    start_scheduler()
    # Run pipeline once on startup
    logger.info("Running initial pipeline on startup...")
    try:
        run_pipeline()
    except Exception as e:
        logger.error("Initial pipeline run failed: %s", e, exc_info=True)
    yield
    stop_scheduler()
    logger.info("Application shutdown complete.")


app = FastAPI(
    title="Financial News Intelligence Platform",
    description="Automated financial news collection, classification, and reporting",
    version="1.0.0",
    lifespan=lifespan,
)


# ── Helper: build query with filters ─────────────────────────────────────────
def _build_filtered_query(session, **filters):
    """Build a SQLAlchemy query with optional filters.

    Supported filters: keyword, category, source, company,
    sector, date_from, date_to, priority_min, priority_max,
    hide_duplicates.
    """
    query = session.query(Article)

    keyword = filters.get("keyword")
    if keyword:
        pattern = f"%{keyword}%"
        query = query.filter(
            Article.headline.ilike(pattern) | Article.summary.ilike(pattern)
        )

    category = filters.get("category")
    if category:
        query = query.filter(Article.category == category)

    source = filters.get("source")
    if source:
        query = query.filter(Article.source == source)

    company = filters.get("company")
    if company:
        query = query.filter(Article.companies.ilike(f"%{company}%"))

    sector = filters.get("sector")
    if sector:
        query = query.filter(Article.sector == sector)

    date_from = filters.get("date_from")
    if date_from:
        query = query.filter(Article.scraped_time >= date_from)

    date_to = filters.get("date_to")
    if date_to:
        query = query.filter(Article.scraped_time <= date_to)

    priority_min = filters.get("priority_min")
    if priority_min is not None:
        query = query.filter(Article.priority_score >= priority_min)

    priority_max = filters.get("priority_max")
    if priority_max is not None:
        query = query.filter(Article.priority_score <= priority_max)

    hide_duplicates = filters.get("hide_duplicates", True)
    if hide_duplicates:
        query = query.filter(Article.duplicate_flag == False)  # noqa: E712

    return query


# ══════════════════════════════════════════════════════════════════════════════
# API ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════


@app.get("/api/articles")
def get_articles(
    keyword: Optional[str] = None,
    category: Optional[str] = None,
    source: Optional[str] = None,
    company: Optional[str] = None,
    sector: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    priority_min: Optional[int] = None,
    priority_max: Optional[int] = None,
    hide_duplicates: bool = True,
    sort_by: str = "priority_score",
    sort_order: str = "desc",
    page: int = 1,
    page_size: int = 25,
):
    """Get paginated articles with optional filters."""
    with session_scope() as session:
        # Parse dates
        parsed_date_from = None
        parsed_date_to = None
        if date_from:
            try:
                parsed_date_from = datetime.fromisoformat(date_from)
            except ValueError:
                pass
        if date_to:
            try:
                parsed_date_to = datetime.fromisoformat(date_to)
            except ValueError:
                pass

        query = _build_filtered_query(
            session,
            keyword=keyword,
            category=category,
            source=source,
            company=company,
            sector=sector,
            date_from=parsed_date_from,
            date_to=parsed_date_to,
            priority_min=priority_min,
            priority_max=priority_max,
            hide_duplicates=hide_duplicates,
        )

        # Total count before pagination
        total = query.count()

        # Sorting
        sort_column = getattr(Article, sort_by, Article.priority_score)
        if sort_order == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        # Pagination
        offset = (page - 1) * page_size
        articles = query.offset(offset).limit(page_size).all()

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "articles": [a.to_dict() for a in articles],
        }


@app.get("/api/stats")
def get_stats():
    """Get dashboard statistics."""
    with session_scope() as session:
        total = session.query(func.count(Article.id)).scalar() or 0

        # Today's articles (UTC)
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        today_count = (
            session.query(func.count(Article.id))
            .filter(Article.scraped_time >= today_start)
            .filter(Article.duplicate_flag == False)  # noqa: E712
            .scalar()
            or 0
        )

        # High priority (>=80)
        high_priority = (
            session.query(func.count(Article.id))
            .filter(Article.priority_score >= 80)
            .filter(Article.duplicate_flag == False)  # noqa: E712
            .scalar()
            or 0
        )

        # Source counts
        source_counts = (
            session.query(Article.source, func.count(Article.id))
            .filter(Article.duplicate_flag == False)  # noqa: E712
            .group_by(Article.source)
            .all()
        )

        # Category counts
        category_counts = (
            session.query(Article.category, func.count(Article.id))
            .filter(Article.duplicate_flag == False)  # noqa: E712
            .group_by(Article.category)
            .all()
        )

        # Active sources (sources with articles in last 24h)
        from datetime import timedelta
        day_ago = datetime.now(timezone.utc) - timedelta(hours=24)
        active_sources = (
            session.query(func.count(func.distinct(Article.source)))
            .filter(Article.scraped_time >= day_ago)
            .scalar()
            or 0
        )

        return {
            "total_articles": total,
            "today_articles": today_count,
            "high_priority": high_priority,
            "active_sources": active_sources,
            "sources": {s: c for s, c in source_counts},
            "categories": {c: n for c, n in category_counts},
        }


@app.get("/api/trending")
def get_trending():
    """Get trending companies and sectors from the last 24 hours."""
    with session_scope() as session:
        from datetime import timedelta

        day_ago = datetime.now(timezone.utc) - timedelta(hours=24)

        # Get recent non-duplicate articles
        recent = (
            session.query(Article.companies, Article.sector, Article.category)
            .filter(Article.scraped_time >= day_ago)
            .filter(Article.duplicate_flag == False)  # noqa: E712
            .all()
        )

        # Count company mentions
        import json
        company_counts: dict[str, int] = {}
        sector_counts: dict[str, int] = {}
        category_counts: dict[str, int] = {}

        for companies_json, sector, category in recent:
            # Companies
            try:
                companies = json.loads(companies_json) if companies_json else []
                for company in companies:
                    company_counts[company] = company_counts.get(company, 0) + 1
            except (json.JSONDecodeError, TypeError):
                pass

            # Sectors
            if sector:
                sector_counts[sector] = sector_counts.get(sector, 0) + 1

            # Categories
            if category:
                category_counts[category] = category_counts.get(category, 0) + 1

        # Sort by count, take top 10
        trending_companies = sorted(
            company_counts.items(), key=lambda x: -x[1]
        )[:10]
        trending_sectors = sorted(
            sector_counts.items(), key=lambda x: -x[1]
        )[:10]
        trending_categories = sorted(
            category_counts.items(), key=lambda x: -x[1]
        )[:10]

        return {
            "trending_companies": [
                {"name": c, "count": n} for c, n in trending_companies
            ],
            "trending_sectors": [
                {"name": s, "count": n} for s, n in trending_sectors
            ],
            "trending_categories": [
                {"name": c, "count": n} for c, n in trending_categories
            ],
        }


@app.post("/api/scrape")
def trigger_scrape():
    """Trigger an immediate pipeline run."""
    logger.info("Manual scrape triggered via API.")
    try:
        result = run_pipeline()
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error("Manual scrape failed: %s", e, exc_info=True)
        return {"status": "error", "message": str(e)}


@app.get("/api/scheduler")
def scheduler_status():
    """Get scheduler status."""
    return get_scheduler_status()


@app.get("/api/export/excel")
def export_excel(
    keyword: Optional[str] = None,
    category: Optional[str] = None,
    source: Optional[str] = None,
    company: Optional[str] = None,
    priority_min: Optional[int] = None,
    hide_duplicates: bool = True,
):
    """Export filtered articles as Excel file."""
    from backend.exports.excel_export import generate_excel

    with session_scope() as session:
        query = _build_filtered_query(
            session,
            keyword=keyword,
            category=category,
            source=source,
            company=company,
            priority_min=priority_min,
            hide_duplicates=hide_duplicates,
        )
        articles = query.order_by(Article.priority_score.desc()).limit(500).all()
        articles_data = [a.to_dict() for a in articles]

    buffer = generate_excel(articles_data)
    filename = f"financial_news_report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.get("/api/export/pdf")
def export_pdf(
    keyword: Optional[str] = None,
    category: Optional[str] = None,
    source: Optional[str] = None,
    company: Optional[str] = None,
    priority_min: Optional[int] = None,
    hide_duplicates: bool = True,
):
    """Export filtered articles as PDF report."""
    from backend.exports.pdf_export import generate_pdf

    with session_scope() as session:
        query = _build_filtered_query(
            session,
            keyword=keyword,
            category=category,
            source=source,
            company=company,
            priority_min=priority_min,
            hide_duplicates=hide_duplicates,
        )
        articles = query.order_by(Article.priority_score.desc()).limit(200).all()
        articles_data = [a.to_dict() for a in articles]

    filters_summary = ", ".join(
        f"{k}={v}" for k, v in {
            "keyword": keyword,
            "category": category,
            "source": source,
            "company": company,
            "priority_min": priority_min,
        }.items() if v is not None
    ) or "None"

    buffer = generate_pdf(articles_data, filters_summary)
    filename = f"financial_news_report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.get("/api/categories")
def get_categories():
    """Get list of all categories in the database."""
    with session_scope() as session:
        rows = (
            session.query(Article.category)
            .distinct()
            .order_by(Article.category)
            .all()
        )
        return [r[0] for r in rows if r[0]]


@app.get("/api/sources")
def get_sources():
    """Get list of all sources in the database."""
    with session_scope() as session:
        rows = (
            session.query(Article.source)
            .distinct()
            .order_by(Article.source)
            .all()
        )
        return [r[0] for r in rows if r[0]]
