# Scrapers package
from backend.services.scrapers.moneycontrol import MoneycontrolScraper
from backend.services.scrapers.economictimes import EconomicTimesScraper
from backend.services.scrapers.livemint import LiveMintScraper
from backend.services.scrapers.businessstandard import BusinessStandardScraper
from backend.services.scrapers.reuters import ReutersScraper
from backend.services.scrapers.cnbctv18 import CNBCTV18Scraper

# Registry of all available scrapers — add new scrapers here
SCRAPER_REGISTRY = [
    MoneycontrolScraper,
    EconomicTimesScraper,
    LiveMintScraper,
    BusinessStandardScraper,
    ReutersScraper,
    CNBCTV18Scraper,
]
