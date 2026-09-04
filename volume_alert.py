"""
MODI3 volume-spike screener: flags stocks trading at an unusual multiple of
their own 50-day average volume. Same criterion as MODI1's volume alert --
NIFTY 50 + NIFTY Financial Services constituents (NIFTY_SYMBOLS) need only
1.5x, every other symbol on the watchlist needs 2x or more -- ported here so
MODI3 catches volume spikes independently of its news/filing alerts.

Dedup is per calendar day: once a symbol has alerted today it won't alert
again today even if it stays above threshold on a later run. This is meant
to run every 15 min during market hours via Task Scheduler, same convention
as news_alert.py/run_news_alert.bat.
"""

import json
import os
import sys
from datetime import date

# Same fix as news_alert.py: avoid a non-UTF-8 stdout codepage crash when
# output is redirected to a log file.
sys.stdout.reconfigure(encoding="utf-8")

from intraday_watchlist import INTRADAY_SYMBOLS, NIFTY_SYMBOLS
from fetch_volume import fetch_volumes
from send_telegram import send_telegram_message

STATE_FILE = "volume_alerted_state.json"
NIFTY_THRESHOLD = 1.5
DEFAULT_THRESHOLD = 2.0
MAX_MESSAGE_CHARS = 3500  # Telegram hard-caps messages at 4096 chars


def load_state():
    today = date.today().isoformat()
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
        if state.get("date") == today:
            return state
    return {"date": today, "alerted": []}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def run():
    print(f"\n===== VOLUME RUN: {date.today().isoformat()} =====")
    state = load_state()
    alerted = set(state["alerted"])

    symbols = list(INTRADAY_SYMBOLS)
    volumes = fetch_volumes(symbols)
    print(f"Got volume data for {len(volumes)}/{len(symbols)} symbols.")

    new_alerts = []
    for symbol in symbols:
        if symbol in alerted or symbol not in volumes:
            continue
        current_volume, avg_volume = volumes[symbol]
        if avg_volume <= 0:
            continue
        multiple = current_volume / avg_volume
        is_nifty = symbol in NIFTY_SYMBOLS
        threshold = NIFTY_THRESHOLD if is_nifty else DEFAULT_THRESHOLD
        if multiple >= threshold:
            alerted.add(symbol)
            tag = " (Nifty)" if is_nifty else ""
            new_alerts.append(
                f"[MODI3] \U0001F4CA VOLUME SPIKE: <b>{symbol}</b>{tag}\n"
                f"{multiple:.2f}x its 50-day avg volume (threshold {threshold}x)"
            )

    if new_alerts:
        chunks, current_chunk, current_len = [], [], 0
        for alert_text in new_alerts:
            if current_len + len(alert_text) + 2 > MAX_MESSAGE_CHARS and current_chunk:
                chunks.append(current_chunk)
                current_chunk, current_len = [], 0
            current_chunk.append(alert_text)
            current_len += len(alert_text) + 2
        if current_chunk:
            chunks.append(current_chunk)

        total_sent_ok = True
        for chunk in chunks:
            if not send_telegram_message("\n\n".join(chunk)):
                total_sent_ok = False
        print(f"Sent {len(new_alerts)} volume alert(s) in {len(chunks)} message(s). Telegram sent: {total_sent_ok}")
    else:
        print("No volume-spike alerts this run.")

    state["alerted"] = list(alerted)
    save_state(state)


if __name__ == "__main__":
    run()
