"""
Diagnose why live scrape returns 0 even though offline parse works.
Fetches live pages using the EXACT same method as BaseScraper and
dumps the HTML + parser results.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests, random
from bs4 import BeautifulSoup
from backend.services.scrapers.base_scraper import BaseScraper

# Replicate BaseScraper._fetch exactly
UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
]

def fetch_like_scraper(url):
    session = requests.Session()
    headers = {
        "User-Agent": random.choice(UA_LIST),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
    }
    session.headers.update(headers)
    r = session.get(url, timeout=20, allow_redirects=True)
    return r

for name, url, scraper_class in [
    ("Moneycontrol", "https://www.moneycontrol.com/news/business/markets/",
     "backend.services.scrapers.moneycontrol.MoneycontrolScraper"),
    ("LiveMint", "https://www.livemint.com/market",
     "backend.services.scrapers.livemint.LiveMintScraper"),
    ("CNBC TV18", "https://www.cnbctv18.com/market/",
     "backend.services.scrapers.cnbctv18.CNBCTV18Scraper"),
]:
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")
    try:
        r = fetch_like_scraper(url)
        print(f"  Status: {r.status_code}  Content-Type: {r.headers.get('Content-Type','?')[:50]}")
        print(f"  Response size: {len(r.content)} bytes")
        
        soup = BeautifulSoup(r.content, "html.parser")
        h2s = soup.find_all("h2")
        h3s = soup.find_all("h3")
        articles = soup.find_all("article")
        nb = soup.select(".newsBlock")
        print(f"  Tags: h2={len(h2s)} h3={len(h3s)} article={len(articles)} .newsBlock={len(nb)}")
        
        # Save for comparison
        out_path = f"debug_html/{name.lower().replace(' ','_')}_live.html"
        with open(out_path, "wb") as f:
            f.write(r.content)
        print(f"  Saved to: {out_path}")
        
        # Test the parser
        import importlib
        mod_name, cls_name = scraper_class.rsplit(".", 1)
        mod = importlib.import_module(mod_name)
        cls = getattr(mod, cls_name)
        scraper = cls()
        parsed = scraper.parse(soup)
        print(f"  Parser result: {len(parsed)} articles")
        for a in parsed[:2]:
            hl = a['headline'].encode('ascii', errors='replace').decode()
            print(f"    - {hl[:70]}")
    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback; traceback.print_exc()
