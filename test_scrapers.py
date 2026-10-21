"""Quick scraper test — verifies each scraper returns articles."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.services.scrapers.moneycontrol import MoneycontrolScraper
from backend.services.scrapers.economictimes import EconomicTimesScraper
from backend.services.scrapers.livemint import LiveMintScraper
from backend.services.scrapers.cnbctv18 import CNBCTV18Scraper

scrapers = [
    MoneycontrolScraper(),
    EconomicTimesScraper(),
    LiveMintScraper(),
    CNBCTV18Scraper(),
]

total = 0
for s in scrapers:
    try:
        articles = s.scrape()
        count = len(articles)
        total += count
        status = "[OK]" if count > 0 else "[WARN]"
        print(f"{status}  {s.source_name:<22}  {count:3d} articles")
        if count > 0:
            print(f"        Sample: {articles[0]['headline'][:70]}")
    except Exception as e:
        print(f"[FAIL] {s.source_name:<22}  ERROR: {e}")

print()
print(f"Total articles collected: {total}")
