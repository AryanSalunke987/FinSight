import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

def scrape_moneycontrol():
    url = "https://www.moneycontrol.com/news/business/markets/"
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'html.parser')

    articles = []
    for item in soup.select('.clearfix'):
        headline = item.find('h2')
        link = item.find('a')
        summary = item.find('p')
        if headline and link and summary:
            articles.append({
                'source': 'Moneycontrol',
                'headline': headline.text.strip(),
                'summary': summary.text.strip(),
                'link': link['href'],
                'timestamp': datetime.now()
            })
    return articles

def scrape_economic_times():
    url = "https://economictimes.indiatimes.com/markets"
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'html.parser')

    articles = []
    for item in soup.select('.eachStory'):
        headline = item.find('h3')
        summary = item.find('p')
        link = item.find('a')
        if headline and summary and link:
            articles.append({
                'source': 'Economic Times',
                'headline': headline.text.strip(),
                'summary': summary.text.strip(),
                'link': "https://economictimes.indiatimes.com" + link['href'],
                'timestamp': datetime.now()
            })
    return articles

def scrape_all():
    all_articles = scrape_moneycontrol() + scrape_economic_times()
    df = pd.DataFrame(all_articles)
    df.to_csv("headlines.csv", index=False)
    return df
