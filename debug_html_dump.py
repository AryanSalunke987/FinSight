"""Dump raw HTML from each site to files for inspection."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests, random

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
]

SITES = {
    "moneycontrol": "https://www.moneycontrol.com/news/business/markets/",
    "economictimes": "https://economictimes.indiatimes.com/markets",
    "livemint": "https://www.livemint.com/market",
    "cnbctv18": "https://www.cnbctv18.com/market/",
}

os.makedirs("debug_html", exist_ok=True)

for name, url in SITES.items():
    try:
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        r = requests.get(url, headers=headers, timeout=15)
        html = r.text
        with open(f"debug_html/{name}.html", "w", encoding="utf-8", errors="replace") as f:
            f.write(html)

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        h2s = soup.find_all("h2")
        h3s = soup.find_all("h3")
        articles = soup.find_all("article")
        print(f"{name}: {len(html)} bytes | h2={len(h2s)} h3={len(h3s)} article={len(articles)}")
        # Show first 3 h2 texts
        for h in h2s[:3]:
            txt = h.get_text(strip=True)
            print(f"  h2: {txt[:80]}")
    except Exception as e:
        print(f"{name}: ERROR {e}")
