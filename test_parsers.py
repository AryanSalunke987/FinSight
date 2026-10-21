"""
Test scrapers against saved HTML dumps (offline test).
This verifies the parsers work regardless of network/encoding issues.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bs4 import BeautifulSoup
from backend.services.scrapers.moneycontrol import MoneycontrolScraper
from backend.services.scrapers.livemint import LiveMintScraper
from backend.services.scrapers.cnbctv18 import CNBCTV18Scraper
from backend.services.scrapers.economictimes import EconomicTimesScraper

tests = [
    ("Moneycontrol", MoneycontrolScraper(), "debug_html/moneycontrol.html"),
    ("LiveMint", LiveMintScraper(), "debug_html/livemint.html"),
    ("CNBC TV18", CNBCTV18Scraper(), "debug_html/cnbctv18.html"),
    ("Economic Times", EconomicTimesScraper(), "debug_html/economictimes.html"),
]

total = 0
all_pass = True
for name, scraper, path in tests:
    if not os.path.exists(path):
        print(f"[SKIP] {name:<22} - no HTML dump")
        continue
    with open(path, encoding="utf-8", errors="replace") as f:
        html = f.read()
    soup = BeautifulSoup(html, "html.parser")
    articles = scraper.parse(soup)
    count = len(articles)
    total += count
    status = "[OK]  " if count > 0 else "[WARN]"
    if count == 0:
        all_pass = False
    print(f"{status} {name:<22}  {count:3d} articles")
    for a in articles[:2]:
        hl = a['headline'].encode('ascii', errors='replace').decode()
        url = a['url'][:70]
        print(f"        {hl[:65]}")
        print(f"        {url}")

print()
print(f"Total: {total} articles")
print("Result:", "PASS" if all_pass else "SOME SCRAPERS RETURNED 0")
