# MODI3 — NSE/SEBI/RSS News & Filing Alerts + Volume Spike Screener

Pulls financial news (RSS), NSE corporate announcements, and SEBI press
releases (`fetch_rss.py`, `fetch_nse_announcements.py`, `fetch_sebi.py`),
matches each item against a watchlist + macro/regulatory keyword list
(`matcher.py`, `config.py`), and sends a filtered Telegram alert for anything
that matches (`news_alert.py`) — not a firehose of every item fetched.

MODI7 reuses this same fetch/match approach (with its own copy of these
files) but adds fundamentals, a red-flag category, and a persistent SQLite
history — see [MODI7's README](https://github.com/saiqulmodi/MODI7#readme)
for that richer version.

Also runs a separate volume-spike screener (`volume_alert.py`), same
criterion as MODI1: flags any watchlist symbol trading at 2x or more of its
own 50-day average volume, or 1.5x or more for NIFTY 50 / NIFTY Financial
Services constituents (`NIFTY_SYMBOLS` in `intraday_watchlist.py`).

## Setup

### `send_telegram.py`

Not committed to this repo — gitignored because it holds a live bot token.
Recreate it locally:

```python
import requests

BOT_TOKEN = "your-bot-token-here"
CHAT_ID = "your-chat-id-here"

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    response = requests.post(url, data=payload)
    if response.status_code != 200:
        print(f"Telegram send failed: {response.text}")
    return response.status_code == 200
```

Get a bot token from [@BotFather](https://t.me/BotFather) on Telegram, and
your chat ID by messaging your bot once and checking
`https://api.telegram.org/bot<TOKEN>/getUpdates`.

### Volume screener data source (`fetch_volume.py`)

Works out of the box with [yfinance](https://pypi.org/project/yfinance/) —
no credentials needed. Angel One's SmartAPI is an optional fallback for any
symbol yfinance can't resolve; set these environment variables to enable it
(leave unset to skip Angel entirely):

```
ANGEL_API_KEY
ANGEL_CLIENT_CODE
ANGEL_PASSWORD
ANGEL_TOTP_SECRET
```

## Running

```bash
python news_alert.py
python volume_alert.py
```

Or register `run_news_alert.bat` / `run_volume_alert.bat` as Windows Task
Scheduler jobs: `MODI3_NewsAlert` runs every 15 minutes 24/7 (news/filings
can land any time), `MODI3_VolumeAlert` runs every 15 minutes only during
NSE market hours, 9:15 AM-3:45 PM, Monday-Friday (volume data outside
trading hours/days is stale anyway). Already-alerted items/symbols are
tracked in
`news_alerted_state.json` and `volume_alerted_state.json` respectively
(both gitignored, regenerate locally) so reruns don't resend the same
alert — the volume state resets each calendar day so a symbol can alert
again on a fresh spike tomorrow.
