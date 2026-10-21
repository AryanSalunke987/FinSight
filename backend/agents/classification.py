"""
Classification Agent — rule-based sector classification and entity extraction.

NO LLMs used. Classification relies on:
  1. Keyword dictionaries for 16 financial sectors
  2. URL path hinting (e.g., /pharma/ → Pharma)
  3. spaCy NER for company/country extraction
  4. Company-to-sector mapping for known Indian companies
"""

import json
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# ── Lazy-loaded spaCy model ──────────────────────────────────────────────────
_nlp = None


def _get_nlp():
    """Lazy-load spaCy model to avoid import-time cost."""
    global _nlp
    if _nlp is None:
        try:
            import spacy
            _nlp = spacy.load("en_core_web_sm")
            logger.info("[Classification] spaCy model loaded successfully.")
        except OSError:
            logger.warning(
                "[Classification] spaCy model 'en_core_web_sm' not found. "
                "Run: python -m spacy download en_core_web_sm"
            )
            _nlp = False  # sentinel to avoid repeated attempts
    return _nlp if _nlp is not False else None


# ══════════════════════════════════════════════════════════════════════════════
# KEYWORD DICTIONARIES — 16 categories
# ══════════════════════════════════════════════════════════════════════════════

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "Banking": [
        "rbi", "reserve bank", "repo rate", "interest rate", "npa",
        "non-performing", "bank", "banking", "hdfc bank", "sbi",
        "icici bank", "axis bank", "kotak", "lending", "credit growth",
        "deposit", "nbfc", "psu bank", "private bank", "loan",
        "casa", "net interest margin", "nim", "base rate", "mclr",
        "monetary policy", "credit policy", "bank nifty", "banking sector",
        "current account", "savings account", "fixed deposit",
        "rbi governor", "rbi policy", "rbi circular",
    ],
    "IT": [
        "infosys", "tcs", "wipro", "hcl tech", "tech mahindra",
        "software", "saas", "cloud", "digital", "it sector",
        "information technology", "it services", "cybersecurity",
        "artificial intelligence", "ai", "machine learning", "automation",
        "outsourcing", "bpo", "it spending", "tech layoffs", "hiring freeze",
        "cognizant", "mphasis", "ltimindtree", "persistent systems",
        "coforge", "nifty it", "it stocks",
    ],
    "Pharma": [
        "pharma", "pharmaceutical", "drug", "fda", "usfda",
        "sun pharma", "dr reddy", "cipla", "lupin", "aurobindo",
        "divi's lab", "biocon", "healthcare", "hospital",
        "apollo hospital", "max health", "fortis", "generic drug",
        "api", "bulk drug", "clinical trial", "biosimilar", "vaccine",
        "nifty pharma", "pharma sector", "drug approval", "anda",
    ],
    "Auto": [
        "auto", "automobile", "vehicle", "car", "ev", "electric vehicle",
        "tata motors", "maruti", "mahindra", "bajaj auto", "hero moto",
        "eicher motors", "ashok leyland", "tvs motor", "ola electric",
        "ather energy", "automotive", "nifty auto", "auto sector",
        "passenger vehicle", "commercial vehicle", "two-wheeler",
        "suv", "sedan", "hatchback", "auto sales", "vehicle sales",
        "emission", "bs6", "hybrid",
    ],
    "Energy": [
        "energy", "oil", "gas", "petroleum", "ongc", "reliance",
        "bpcl", "hpcl", "ioc", "indian oil", "petrol", "diesel",
        "crude oil", "brent", "wti", "natural gas", "lng",
        "solar", "wind energy", "renewable", "green energy",
        "power", "ntpc", "power grid", "adani power", "adani green",
        "tata power", "coal", "coal india", "thermal",
        "electricity", "nifty energy", "energy sector",
    ],
    "Mutual Funds": [
        "mutual fund", "mf", "sip", "systematic investment",
        "amc", "asset management", "nav", "net asset value",
        "aum", "assets under management", "nfo", "new fund offer",
        "equity fund", "debt fund", "hybrid fund", "index fund",
        "etf", "exchange traded fund", "amfi", "sebi mutual fund",
        "elss", "tax saving fund", "large cap fund", "mid cap fund",
        "small cap fund", "flexi cap", "multi cap", "thematic fund",
        "sector fund", "fund manager", "fund house",
    ],
    "IPO": [
        "ipo", "initial public offering", "listing", "listed",
        "debut", "premium", "discount", "gmp", "grey market premium",
        "allotment", "subscription", "oversubscribed", "book running",
        "anchor investor", "price band", "lot size", "ipo date",
        "drhp", "draft red herring", "red herring prospectus",
        "merchant banker", "registrar", "ipo review",
        "sme ipo", "mainboard ipo",
    ],
    "Economy": [
        "gdp", "inflation", "cpi", "wpi", "fiscal deficit",
        "current account deficit", "trade deficit", "export", "import",
        "iip", "industrial production", "pmi", "manufacturing",
        "economic growth", "recession", "slowdown", "recovery",
        "unemployment", "employment", "labour", "gst collection",
        "tax revenue", "economic survey", "niti aayog", "economic data",
    ],
    "Government Policy": [
        "union budget", "budget", "finance minister", "fm nirmala",
        "fiscal policy", "tax", "income tax", "corporate tax",
        "gst", "goods and services tax", "sebi", "rbi regulation",
        "government", "ministry", "cabinet", "parliament",
        "policy", "regulation", "reform", "disinvestment",
        "privatization", "pli scheme", "production linked",
        "make in india", "atmanirbhar", "startup india",
        "sebi circular", "sebi regulation", "compliance",
    ],
    "Commodities": [
        "commodity", "commodities", "mcx", "ncdex",
        "copper", "aluminum", "aluminium", "zinc", "nickel", "lead",
        "steel", "iron ore", "base metal", "industrial metal",
        "cotton", "sugar", "wheat", "soybean", "palm oil",
        "agri commodity", "rubber", "crude palm oil",
    ],
    "Gold": [
        "gold", "gold price", "gold rate", "sovereign gold bond",
        "sgb", "gold etf", "hallmark", "gold import",
        "gold futures", "mcx gold", "yellow metal",
        "24 carat", "22 carat", "gold jewellery",
    ],
    "Silver": [
        "silver", "silver price", "silver rate", "silver futures",
        "mcx silver", "silver etf", "white metal",
    ],
    "Global Markets": [
        "wall street", "nasdaq", "dow jones", "s&p 500", "s&p500",
        "fed", "federal reserve", "us fed", "powell", "ecb",
        "bank of japan", "boj", "bank of england",
        "global market", "world market", "asia market", "europe market",
        "us market", "china market", "hang seng", "nikkei",
        "ftse", "dax", "shanghai", "kospi", "global cue",
        "fii", "foreign institutional", "dii", "domestic institutional",
        "foreign investor", "capital flow",
    ],
    "Corporate Results": [
        "quarterly result", "q1 result", "q2 result", "q3 result", "q4 result",
        "earnings", "quarterly earnings", "net profit", "revenue",
        "ebitda", "operating profit", "profit after tax", "pat",
        "profit before tax", "pbt", "topline", "bottomline",
        "year-on-year", "yoy", "quarter-on-quarter", "qoq",
        "annual result", "financial result", "board meeting",
        "dividend", "bonus", "buyback", "share buyback",
        "eps", "earnings per share",
    ],
    "Cryptocurrency": [
        "crypto", "cryptocurrency", "bitcoin", "btc", "ethereum", "eth",
        "blockchain", "defi", "nft", "web3", "altcoin",
        "binance", "coinbase", "crypto exchange", "digital currency",
        "cbdc", "central bank digital", "crypto regulation",
        "dogecoin", "solana", "ripple", "xrp",
    ],
    "Currency": [
        "rupee", "dollar", "usd", "inr", "forex", "foreign exchange",
        "currency", "exchange rate", "rupee depreciation", "rupee appreciation",
        "usdinr", "eur", "gbp", "yen", "yuan",
        "rbi intervention", "forex reserve", "dollar index", "dxy",
    ],
}

# ── URL path hints for category inference ─────────────────────────────────────
URL_CATEGORY_HINTS: dict[str, str] = {
    "/pharma/": "Pharma",
    "/auto/": "Auto",
    "/banking/": "Banking",
    "/finance/": "Banking",
    "/it/": "IT",
    "/technology/": "IT",
    "/energy/": "Energy",
    "/oil-gas/": "Energy",
    "/mutual-fund/": "Mutual Funds",
    "/ipo/": "IPO",
    "/economy/": "Economy",
    "/policy/": "Government Policy",
    "/commodity/": "Commodities",
    "/commodities/": "Commodities",
    "/gold/": "Gold",
    "/silver/": "Silver",
    "/cryptocurrency/": "Cryptocurrency",
    "/crypto/": "Cryptocurrency",
    "/forex/": "Currency",
    "/currency/": "Currency",
    "/corporate/": "Corporate Results",
    "/earnings/": "Corporate Results",
    "/results/": "Corporate Results",
    "/global/": "Global Markets",
    "/world/": "Global Markets",
}

# ── Company-to-sector mapping (top Indian companies) ─────────────────────────
COMPANY_SECTOR_MAP: dict[str, str] = {
    # Banking
    "HDFC Bank": "Banking", "SBI": "Banking", "ICICI Bank": "Banking",
    "Axis Bank": "Banking", "Kotak Mahindra": "Banking", "Bank of Baroda": "Banking",
    "Punjab National Bank": "Banking", "IndusInd Bank": "Banking",
    "Bandhan Bank": "Banking", "Federal Bank": "Banking",
    # IT
    "Infosys": "IT", "TCS": "IT", "Wipro": "IT", "HCL Tech": "IT",
    "Tech Mahindra": "IT", "LTIMindtree": "IT", "Mphasis": "IT",
    "Persistent Systems": "IT", "Coforge": "IT",
    # Pharma
    "Sun Pharma": "Pharma", "Dr Reddy": "Pharma", "Cipla": "Pharma",
    "Lupin": "Pharma", "Aurobindo Pharma": "Pharma", "Divi's Lab": "Pharma",
    "Biocon": "Pharma",
    # Auto
    "Tata Motors": "Auto", "Maruti Suzuki": "Auto", "Mahindra": "Auto",
    "Bajaj Auto": "Auto", "Hero MotoCorp": "Auto", "Eicher Motors": "Auto",
    "Ashok Leyland": "Auto", "TVS Motor": "Auto",
    # Energy
    "Reliance Industries": "Energy", "ONGC": "Energy", "BPCL": "Energy",
    "HPCL": "Energy", "Indian Oil": "Energy", "NTPC": "Energy",
    "Power Grid": "Energy", "Adani Green": "Energy", "Tata Power": "Energy",
    "Coal India": "Energy", "Adani Power": "Energy",
    # Conglomerates
    "Reliance": "Energy", "L&T": "Economy", "Larsen & Toubro": "Economy",
}


def _classify_by_keywords(text: str) -> tuple[str, float]:
    """Score text against all category keyword dictionaries.

    Returns:
        Tuple of (best_category, confidence_score).
    """
    text_lower = text.lower()
    scores: dict[str, int] = {}

    for category, keywords in CATEGORY_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            # Count occurrences — use word boundary for short keywords
            if len(keyword) <= 3:
                pattern = rf"\b{re.escape(keyword)}\b"
                score += len(re.findall(pattern, text_lower, re.IGNORECASE))
            else:
                score += text_lower.count(keyword.lower())
        if score > 0:
            scores[category] = score

    if not scores:
        return "General", 0.0

    best_category = max(scores, key=scores.get)
    total_matches = sum(scores.values())
    confidence = scores[best_category] / total_matches if total_matches > 0 else 0.0

    return best_category, confidence


def _classify_by_url(url: str) -> Optional[str]:
    """Infer category from URL path."""
    url_lower = url.lower()
    for path_fragment, category in URL_CATEGORY_HINTS.items():
        if path_fragment in url_lower:
            return category
    return None


def _extract_entities(text: str) -> dict:
    """Extract named entities using spaCy NER.

    Returns:
        Dict with keys: companies (list), countries (list), sector (str or None).
    """
    nlp = _get_nlp()
    result = {"companies": [], "countries": [], "sector": None}

    if nlp is None or not text:
        return result

    doc = nlp(text[:1000])  # limit text length to avoid slow processing

    companies = set()
    countries = set()

    for ent in doc.ents:
        if ent.label_ == "ORG":
            company = ent.text.strip()
            if len(company) > 1:  # skip single-char entities
                companies.add(company)
        elif ent.label_ in ("GPE", "LOC"):
            countries.add(ent.text.strip())

    result["companies"] = sorted(companies)
    result["countries"] = sorted(countries)

    # Try to infer sector from known company names
    for company in companies:
        for known_company, sector in COMPANY_SECTOR_MAP.items():
            if known_company.lower() in company.lower() or company.lower() in known_company.lower():
                result["sector"] = sector
                break
        if result["sector"]:
            break

    return result


def classify_article(article: dict) -> dict:
    """Classify a single article and extract entities.

    Modifies the article dict in-place, adding:
        category, companies, sector, country

    Args:
        article: Dict with at least 'headline', 'summary', 'url'.

    Returns:
        The same dict with classification fields added.
    """
    headline = article.get("headline", "")
    summary = article.get("summary", "")
    url = article.get("url", "")
    full_text = f"{headline} {summary}"

    # 1. Keyword-based classification (primary method)
    category, confidence = _classify_by_keywords(full_text)

    # 2. URL hint (used as tiebreaker or if keywords give low confidence)
    url_category = _classify_by_url(url)
    if category == "General" and url_category:
        category = url_category
    elif url_category and confidence < 0.5:
        # URL hint overrides low-confidence keyword classification
        category = url_category

    # 3. Entity extraction
    entities = _extract_entities(full_text)

    # If keyword classification gave General but we found a known company,
    # use the company's sector as the category
    if category == "General" and entities.get("sector"):
        category = entities["sector"]

    # Apply results to article
    article["category"] = category
    article["companies"] = json.dumps(entities["companies"]) if entities["companies"] else "[]"
    article["sector"] = entities.get("sector") or category
    article["country"] = entities["countries"][0] if entities["countries"] else "India"

    return article


def classify_articles(articles: list[dict]) -> list[dict]:
    """Classify a batch of articles.

    Args:
        articles: List of article dicts from the cleaning agent.

    Returns:
        The same list with classification fields added to each article.
    """
    if not articles:
        return articles

    logger.info("[Classification] Classifying %d articles...", len(articles))

    category_counts: dict[str, int] = {}

    for article in articles:
        classify_article(article)
        cat = article.get("category", "General")
        category_counts[cat] = category_counts.get(cat, 0) + 1

    # Log distribution
    logger.info("[Classification] Category distribution:")
    for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        logger.info("  %-20s %d", cat, count)

    return articles
