"""
Inspect live HTML from each site to find working selectors.
Run: python inspect_html.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests
from bs4 import BeautifulSoup
import random

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
]

SITES = {
    "Moneycontrol": "https://www.moneycontrol.com/news/business/markets/",
    "Economic Times": "https://economictimes.indiatimes.com/markets",
    "LiveMint": "https://www.livemint.com/market",
    "CNBC TV18": "https://www.cnbctv18.com/market/",
}

def fetch(url):
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()
    return BeautifulSoup(r.content, "html.parser")

for name, url in SITES.items():
    print(f"\n{'='*60}")
    print(f"  {name}  ({url})")
    print(f"{'='*60}")
    try:
        soup = fetch(url)
        # Count tags
        all_a = soup.find_all("a", href=True)
        all_h2 = soup.find_all("h2")
        all_h3 = soup.find_all("h3")
        all_articles = soup.find_all("article")
        print(f"  <a> tags: {len(all_a)}  <h2>: {len(all_h2)}  <h3>: {len(all_h3)}  <article>: {len(all_articles)}")
        
        # Show first few h2/h3 texts
        print("  First 5 <h2> texts:")
        for tag in list(all_h2)[:5]:
            print(f"    - {tag.get_text(strip=True)[:80]}")
        print("  First 5 <h3> texts:")
        for tag in list(all_h3)[:5]:
            print(f"    - {tag.get_text(strip=True)[:80]}")

        # Show first 5 meaningful anchor texts
        print("  First 5 meaningful anchor hrefs:")
        count = 0
        for a in all_a:
            href = a["href"]
            text = a.get_text(strip=True)
            if len(text) > 30 and href.startswith("http"):
                print(f"    - [{text[:60]}] -> {href[:70]}")
                count += 1
                if count >= 5:
                    break
        
        # Show all unique class names on <div> and <li> for selector discovery
        class_counter = {}
        for tag in soup.find_all(["div", "li", "article", "section"]):
            for cls in tag.get("class", []):
                class_counter[cls] = class_counter.get(cls, 0) + 1
        
        top_classes = sorted(class_counter.items(), key=lambda x: -x[1])[:20]
        print("  Top 20 class names:")
        for cls, count in top_classes:
            print(f"    [{count:3d}] .{cls}")

    except Exception as e:
        print(f"  ERROR: {e}")
