import streamlit as st
import pandas as pd
from scrapper import scrape_all

st.set_page_config(page_title="Stock Market News Aggregator", layout="wide")

st.title("📈 Stock Market News Aggregator")
st.markdown("Aggregates headlines from **Moneycontrol** and **Economic Times**.")

if st.button("Scrape Latest News"):
    with st.spinner("Scraping news articles..."):
        df = scrape_all()
        st.success(f"Scraped {len(df)} articles!")
        st.dataframe(df[['source', 'headline', 'summary', 'link', 'timestamp']])
else:
    st.info("Click the button above to scrape the latest news.")

if st.checkbox("Show saved CSV"):
    df = pd.read_csv("headlines.csv")
    st.dataframe(df[['source', 'headline', 'summary', 'link', 'timestamp']])
