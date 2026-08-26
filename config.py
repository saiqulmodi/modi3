"""
Shared configuration for MODI3: sources, keywords, and the watchlist used to
decide which news/filings/regulatory items are actually alert-worthy.
"""

import pandas as pd
from intraday_watchlist import INTRADAY_SYMBOLS

RSS_FEEDS = {
    "Economic Times Markets": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "Business Standard Markets": "https://www.business-standard.com/rss/markets-106.rss",
    "CNBC World Markets": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "CNBC Top News": "https://www.cnbc.com/id/10001147/device/rss/rss.html",
    "Bloomberg Markets": "https://www.bloomberg.com/feeds/markets/news.rss",
    "Google News (global markets/Fed/geopolitical)": (
        "https://news.google.com/rss/search?q=global+markets+OR+federal+reserve"
        "+OR+geopolitical+when:1d&hl=en-US&gl=US&ceid=US:en"
    ),
    "Investing.com Commodities": "https://www.investing.com/rss/commodities.rss",
    "Google News (commodities)": (
        "https://news.google.com/rss/search?q=crude+oil+OR+gold+price+OR+silver+price"
        "+OR+commodities+when:1d&hl=en-US&gl=US&ceid=US:en"
    ),
}

NSE_ANNOUNCEMENTS_URL = "https://www.nseindia.com/api/corporate-announcements?index=equities"
SEBI_PRESS_RELEASES_URL = "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1&ssid=7&smid=0"

# Macro/regulatory terms worth alerting on regardless of company mentioned.
# Includes both India-specific and global market-moving terms, since the
# global feeds (CNBC/Bloomberg/Google News) rarely mention Indian tickers
# directly -- their relevance comes through these keywords instead.
MACRO_KEYWORDS = [
    "RBI", "repo rate", "SEBI circular", "SEBI order", "GDP", "inflation",
    "CPI", "WPI", "GST", "union budget", "monetary policy", "interest rate",
    "fiscal deficit", "credit policy", "FII", "DII", "current account deficit",
    "rating downgrade", "rating upgrade", "moody's", "s&p", "fitch",
    "federal reserve", "fed rate", "rate hike", "rate cut", "tariff",
    "sanctions", "trade war", "oil price", "crude oil", "opec", "recession",
    "geopolitical", "china", "war", "ceasefire", "central bank",
    "gold price", "silver price", "natural gas", "copper", "commodity prices",
]

# Corporate-announcement categories worth alerting on for ANY company, not
# just the 428-stock watchlist -- order wins and results updates are broad
# market interest, and NSE's corporate-announcements feed covers ~2000+
# listed companies, most of which aren't on WATCHLIST_SYMBOLS at all.
ANNOUNCEMENT_CATEGORY_KEYWORDS = [
    "financial results", "award of order", "receipt of order",
    "bags order", "wins order", "l1 bidder", "lowest bidder",
    "order worth", "contract win", "order from",
]

WATCHLIST_SYMBOLS = set(INTRADAY_SYMBOLS)


def load_symbol_to_name():
    """Maps ticker symbol -> full company name for NSE equities in the watchlist,
    so news mentioning a company by name (not just ticker) can still match."""
    scrips = pd.read_csv("nse_scrips.csv", low_memory=False)
    equities = scrips[(scrips["exchangename"] == "NSE") & (scrips["optiontype"] == "EQ")]
    mapping = {}
    for symbol in WATCHLIST_SYMBOLS:
        match = equities[equities["scripshortname"] == symbol]
        if not match.empty:
            mapping[symbol] = match.iloc[0]["scripfullname"]
    return mapping


SYMBOL_TO_NAME = load_symbol_to_name()
