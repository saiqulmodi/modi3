"""
Decides whether a news/filing/circular item is alert-worthy: does it
mention a watchlist company (by ticker or full name) or a macro/regulatory
keyword.
"""

import re
from config import WATCHLIST_SYMBOLS, SYMBOL_TO_NAME, MACRO_KEYWORDS


def find_matches(text):
    """Returns a list of matched terms (symbols/company names/keywords), empty if none."""
    matches = []

    for symbol in WATCHLIST_SYMBOLS:
        if re.search(rf"\b{re.escape(symbol)}\b", text):
            matches.append(symbol)
            continue
        company_name = SYMBOL_TO_NAME.get(symbol)
        if company_name and company_name.lower() in text.lower():
            matches.append(symbol)

    for keyword in MACRO_KEYWORDS:
        if re.search(rf"\b{re.escape(keyword.lower())}\b", text.lower()):
            matches.append(keyword)

    return matches
