"""
Shared configuration for MODI3: sources, keywords, and the watchlist used to
decide which news/filings/regulatory items are actually alert-worthy.

MODI3 is scoped to INDIAN LOCAL coverage only (Indian financial press,
NSE corporate announcements, SEBI releases) -- global markets/Fed/
geopolitical/commodities coverage is MODI7's job exclusively (its
RSS_FEEDS carries the global sources this file used to also carry, which
was causing the same global story -- e.g. a Fed-rate Google News item --
to get alerted separately by both projects).
"""

import pandas as pd
from intraday_watchlist import INTRADAY_SYMBOLS

RSS_FEEDS = {
    "Economic Times Markets": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "Business Standard Markets": "https://www.business-standard.com/rss/markets-106.rss",
}

NSE_ANNOUNCEMENTS_URL = "https://www.nseindia.com/api/corporate-announcements?index=equities"
SEBI_PRESS_RELEASES_URL = "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1&ssid=7&smid=0"

# Macro/regulatory terms worth alerting on regardless of company mentioned.
# Includes both India-specific terms and globally-framed ones (federal
# reserve, geopolitical, etc.) that still matter when they show up in
# India-focused reporting's own coverage of a global event -- MODI7 carries
# the raw global-wire version of the same story separately.
MACRO_KEYWORDS = [
    "RBI", "repo rate", "SEBI circular", "SEBI order", "GDP", "inflation",
    "CPI", "WPI", "GST", "union budget", "monetary policy", "interest rate",
    "fiscal deficit", "credit policy", "FII", "DII", "current account deficit",
    "rating downgrade", "rating upgrade", "moody's", "s&p", "fitch",
    "federal reserve", "fed rate", "rate hike", "rate cut", "tariff",
    "sanctions", "trade war", "recession",
    "geopolitical", "china", "war", "ceasefire", "central bank",
    "silver price", "natural gas", "copper", "commodity prices",
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

# Terms that make an item worth flagging as a potential governance/legal/
# financial-distress red flag. Substring-matched (word-boundary) case-
# insensitively against title+text, same as ANNOUNCEMENT_CATEGORY_KEYWORDS.
# This is a keyword net, not a verified classifier -- a match means "worth
# a human look," not "confirmed problem." Ported from MODI7 (2026-09-04):
# this only ever meaningfully fires against NSE/SEBI corporate filings, and
# MODI3 is where that coverage lives now that MODI7 is global-only.
RED_FLAG_KEYWORDS = [
    "resignation of director", "director resigns", "auditor resign",
    "resignation of auditor", "forensic audit", "sebi bars", "sebi bans",
    "show cause notice",
    # Bare "insider trading" false-positives on the boilerplate "Trading
    # Window closure pursuant to SEBI (Prohibition of Insider Trading)
    # Regulations" filing every company makes routinely -- these more
    # specific phrases only match an actual reported violation/action.
    "insider trading violation", "insider trading case", "insider trading probe",
    "penalty for insider trading", "charged with insider trading",
    "cbi raid", "ed raid",
    "enforcement directorate", "income tax raid", "search and seizure",
    "insolvency", "ibc proceedings", "npa", "default on", "debt restructuring",
    "one time settlement", "winding up", "liquidation", "fraud",
    "misappropriation", "pledge of shares", "invocation of pledge",
    "promoter selling", "promoter sold", "promoter stake sale", "bulk deal",
    "block deal", "credit rating downgrade", "rating downgraded", "litigation",
    "court case", "lawsuit filed", "class action", "penalty imposed",
    "fine imposed", "regulatory action", "qualified opinion", "going concern",
    "rating watch negative", "outlook revised to negative",
    # Promoter-specific legal exposure -- distinct from the generic
    # litigation/court-case terms above, which can be about the company
    # itself (a customer/vendor dispute) rather than the promoters personally.
    "promoter arrested", "fir against promoter", "chargesheet against promoter",
    "cbi case against promoter", "ed summons promoter", "sebi debars promoter",
    "sebi bars promoter", "case against promoter",
    # Institutional exits -- the selling-side counterpart to the MF/FII
    # buying terms in ANNOUNCEMENT_CATEGORY_KEYWORDS.
    "mutual fund sells", "mutual fund reduces stake", "mf sells",
    "mf reduces stake", "fii sells stake", "dii sells stake",
    "institutional investor exits",
    # Governance/dilution red flags.
    "related party transaction", "voluntary delisting", "delisting of shares",
    # Divestment/disposal -- the selling-side counterpart to the property/
    # land/business acquisition terms in ANNOUNCEMENT_CATEGORY_KEYWORDS.
    "sells land", "disposal of property", "divests property", "divests stake in",
    "sale of business", "sells subsidiary",
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
