"""
Inspect saved HTML dumps to find the exact DOM structure for each site.
Shows how article headlines and links are connected.
"""
import os
from bs4 import BeautifulSoup


def show_h2_structure(name: str, html_path: str, base_url: str, link_filter: str):
    print(f"\n{'='*65}")
    print(f"  {name}")
    print(f"{'='*65}")
    with open(html_path, encoding="utf-8", errors="replace") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    found = 0
    for h2 in soup.find_all("h2"):
        txt = h2.get_text(strip=True)
        if len(txt) < 20:
            continue

        # Check link inside h2
        a_in = h2.find("a", href=True)
        if a_in:
            href = a_in["href"]
            if not href.startswith("http"):
                href = base_url + href
            print(f"  [h2 > a] {txt[:65]}")
            print(f"           {href[:80]}")
            found += 1
            if found >= 5:
                break
            continue

        # Check parent
        parent = h2.parent
        if parent:
            a_par = parent.find("a", href=True)
            if a_par:
                href = a_par["href"]
                if not href.startswith("http"):
                    href = base_url + href
                print(f"  [h2 ^ a] {txt[:65]}")
                print(f"           {href[:80]}")
                found += 1
                if found >= 5:
                    break
                continue

            # Grand-parent
            gp = parent.parent
            if gp:
                a_gp = gp.find("a", href=True)
                if a_gp:
                    href = a_gp["href"]
                    if not href.startswith("http"):
                        href = base_url + href
                    print(f"  [h2^^ a] {txt[:65]}")
                    print(f"           {href[:80]}")
                    found += 1
                    if found >= 5:
                        break

    if found == 0:
        print("  No h2+link pairs found")

    # Also show article structure
    print(f"\n  article tags: {len(soup.find_all('article'))}")
    for article in list(soup.find_all("article"))[:3]:
        a = article.find("a", href=True)
        h = article.find(["h2", "h3", "h4"])
        if a and h:
            href = a["href"]
            if not href.startswith("http"):
                href = base_url + href
            print(f"  [article] {h.get_text(strip=True)[:60]}")
            print(f"            {href[:80]}")


show_h2_structure(
    "Moneycontrol",
    "debug_html/moneycontrol.html",
    "https://www.moneycontrol.com",
    "/news/",
)

show_h2_structure(
    "LiveMint",
    "debug_html/livemint.html",
    "https://www.livemint.com",
    "/market",
)

# Inspect .newsBlock on LiveMint
print("\n\n  --- LiveMint .newsBlock ---")
with open("debug_html/livemint.html", encoding="utf-8", errors="replace") as f:
    soup = BeautifulSoup(f.read(), "html.parser")
for block in list(soup.select(".newsBlock"))[:5]:
    h = block.find(["h2", "h3", "h4"])
    a = block.find("a", href=True)
    print(f"  newsBlock: h={bool(h)} a={bool(a)}")
    if h:
        print(f"    headline: {h.get_text(strip=True)[:60]}")
    if a:
        print(f"    href: {a['href'][:70]}")

# Inspect CNBCTV18 article tags
print("\n\n  --- CNBC TV18 article tags ---")
with open("debug_html/cnbctv18.html", encoding="utf-8", errors="replace") as f:
    soup = BeautifulSoup(f.read(), "html.parser")
for article in list(soup.find_all("article"))[:5]:
    h = article.find(["h2", "h3", "h4"])
    a = article.find("a", href=True)
    print(f"  article: h={bool(h)} a={bool(a)}")
    if h:
        print(f"    headline: {h.get_text(strip=True)[:60]}")
    if a:
        print(f"    href: {a['href'][:70]}")
