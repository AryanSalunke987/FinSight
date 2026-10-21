# Financial News Intelligence Platform

An automated financial news processing pipeline that collects, cleans, classifies, scores, and reports news from 6 trusted Indian financial sources — designed for mutual fund advisors, wealth managers, equity research analysts, and retail investors.

## Architecture

```
Scheduler (every 2 hours)
        ↓
News Collection Agent → Scrapes 6 sources
        ↓
Cleaning Agent → Normalize, deduplicate (RapidFuzz)
        ↓
Classification Agent → Rule-based (16 sectors, spaCy NER)
        ↓
Priority Scoring Agent → Weighted 5-factor formula (0–100)
        ↓
Storage Agent → SQLite via SQLAlchemy ORM
        ↓
Streamlit Dashboard → Charts, Search, Export (Excel/PDF)
```

## Sources

| Source | URL | Focus |
|--------|-----|-------|
| Moneycontrol | moneycontrol.com | Markets |
| Economic Times | economictimes.indiatimes.com | Markets |
| LiveMint | livemint.com | Market & Economy |
| Business Standard | business-standard.com | Markets |
| Reuters | reuters.com | Global Business |
| CNBC TV18 | cnbctv18.com | Indian Markets |

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Run

```bash
python run.py
```

This starts:
- **FastAPI backend** on `http://127.0.0.1:8000`
- **Streamlit dashboard** on `http://localhost:8501`

### 3. Access

- **Dashboard**: http://localhost:8501
- **API Docs**: http://127.0.0.1:8000/docs

## Project Structure

```
├── backend/
│   ├── main.py                  # FastAPI application
│   ├── config.py                # Centralized configuration
│   ├── agents/
│   │   ├── news_collection.py   # Orchestrates all scrapers
│   │   ├── cleaning.py          # Normalization + deduplication
│   │   ├── classification.py    # Rule-based sector classification
│   │   ├── priority.py          # Priority scoring engine
│   │   └── storage.py           # Database persistence
│   ├── database/
│   │   ├── database.py          # SQLAlchemy engine + sessions
│   │   └── models.py            # ORM models
│   ├── services/
│   │   ├── scheduler.py         # APScheduler setup
│   │   └── scrapers/            # 6 source scrapers + base class
│   └── exports/
│       ├── excel_export.py      # OpenPyXL reports
│       └── pdf_export.py        # ReportLab reports
├── dashboard/
│   ├── app.py                   # Streamlit entry point
│   ├── pages/                   # Multi-page dashboard
│   └── components/              # Reusable UI components
├── data/                        # SQLite database (auto-created)
├── logs/                        # Application logs (auto-created)
├── run.py                       # Single entry point
└── requirements.txt
```

## Categories (16)

Banking · IT · Pharma · Auto · Energy · Mutual Funds · IPO · Economy · Government Policy · Commodities · Gold · Silver · Global Markets · Corporate Results · Cryptocurrency · Currency

## Priority Scoring

| Factor | Weight | Example |
|--------|--------|---------|
| Keyword Impact | 35% | "Union Budget" = 100, "RBI Policy" = 95 |
| Source Credibility | 20% | Reuters = 1.0, CNBC TV18 = 0.8 |
| Freshness | 20% | < 1 hour = 100%, > 48 hours = 20% |
| Category Importance | 15% | Government Policy = 1.0, General = 0.3 |
| Entity Count | 10% | 5+ companies = 100%, 0 = 10% |

## Optional: AI Summary

To enable Gemini-powered one-line executive summaries:

1. Uncomment `google-generativeai` in `requirements.txt`
2. Set `GEMINI_API_KEY` in `backend/config.py`
3. Articles with priority ≥ 75 will get AI summaries (max 10 per cycle)

## Tech Stack

**Backend**: Python, FastAPI, SQLAlchemy, APScheduler, BeautifulSoup, spaCy, RapidFuzz
**Frontend**: Streamlit, Plotly
**Export**: OpenPyXL, ReportLab
**Database**: SQLite (WAL mode)
