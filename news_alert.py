"""
MODI3: pulls financial news (RSS), company filings (NSE corporate
announcements), and regulatory circulars (SEBI), then alerts via Telegram
only on items that mention a watchlist company or a macro/regulatory
keyword -- so it's a filtered signal, not a firehose.

Tracks already-alerted items in news_alerted_state.json so re-running
doesn't re-alert on the same item. Dedup is by both link/id AND normalized
title, since some sources (Google News in particular) can return a
different link for the same story on each fetch, which would otherwise
slip past link-only dedup and repeat the same alert.

State is stored as an ordered dict (insertion order = chronological order),
not a set -- a plain set has no defined iteration order, so trimming it
down to the size cap could randomly drop recently-seen items instead of
the oldest ones, letting something slip back out of "seen" and get
re-alerted. Running 24/7 now instead of just market hours, the state fills
up ~4x faster, so this actually matters.
"""

import hashlib
import json
import os
import re
import sys
from datetime import datetime

# Same fix as MODI1's motilal_data.py: when output is redirected to a log
# file, Windows defaults stdout to a non-UTF-8 codepage, which crashes on
# non-ASCII characters that show up often in news titles.
sys.stdout.reconfigure(encoding="utf-8")

from fetch_rss import fetch_rss_items
from fetch_nse_announcements import fetch_nse_announcements
from fetch_sebi import fetch_sebi_press_releases
from matcher import find_matches
from send_telegram import send_telegram_message

STATE_FILE = "news_alerted_state.json"
MAX_STATE_IDS = 20000  # running 24/7 now (~4x more runs/day), sized up accordingly


def load_state():
    """Returns an insertion-ordered dict (key -> True) of already-seen keys."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return dict.fromkeys(json.load(f), True)
    return {}


def save_state(alerted_ids):
    # Keeps the MOST RECENTLY inserted keys, since dicts preserve insertion
    # order -- unlike a set, this reliably trims the oldest entries first.
    trimmed = list(alerted_ids.keys())[-MAX_STATE_IDS:]
    with open(STATE_FILE, "w") as f:
        json.dump(trimmed, f)


def title_key(title):
    normalized = re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()
    return "title:" + hashlib.md5(normalized.encode()).hexdigest()


def run():
    print(f"\n===== RUN: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} =====")
    alerted_ids = load_state()

    all_items = []
    all_items.extend(fetch_rss_items())
    all_items.extend(fetch_nse_announcements())
    all_items.extend(fetch_sebi_press_releases())
    print(f"Fetched {len(all_items)} items across all sources.")

    new_alerts = []
    for item in all_items:
        item_id = "id:" + str(item["id"])
        t_key = title_key(item["title"])
        if item_id in alerted_ids or t_key in alerted_ids:
            continue

        matches = find_matches(item["text"])
        if matches:
            alerted_ids[item_id] = True
            alerted_ids[t_key] = True
            match_str = ", ".join(sorted(set(matches)))
            new_alerts.append(
                f"[MODI3] \U0001F4F0 <b>{item['source']}</b>\n{item['title']}\n"
                f"Matched: {match_str}\n{item['link']}"
            )
        else:
            # Still record it as seen so a later run doesn't re-check it forever.
            alerted_ids[item_id] = True
            alerted_ids[t_key] = True

    if new_alerts:
        # Telegram hard-caps messages at 4096 chars; chunk by actual length
        # rather than a fixed item count, since match volume/title length
        # varies a lot run to run.
        MAX_MESSAGE_CHARS = 3500
        total_sent_ok = True
        chunks = []
        current_chunk = []
        current_len = 0
        for alert_text in new_alerts:
            if len(alert_text) > MAX_MESSAGE_CHARS:
                alert_text = alert_text[:MAX_MESSAGE_CHARS] + "... [truncated]"
            if current_len + len(alert_text) + 2 > MAX_MESSAGE_CHARS and current_chunk:
                chunks.append(current_chunk)
                current_chunk = []
                current_len = 0
            current_chunk.append(alert_text)
            current_len += len(alert_text) + 2
        if current_chunk:
            chunks.append(current_chunk)

        for chunk in chunks:
            message = "\n\n".join(chunk)
            sent = send_telegram_message(message)
            if not sent:
                total_sent_ok = False
        print(f"Sent {len(new_alerts)} new alert(s) in {len(chunks)} message(s). Telegram sent: {total_sent_ok}")
    else:
        print("No new alert-worthy items this run.")

    save_state(alerted_ids)


if __name__ == "__main__":
    run()
