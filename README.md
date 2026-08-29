# MODI3 — NSE/SEBI/RSS News & Filing Alerts

Pulls financial news (RSS), NSE corporate announcements, and SEBI press
releases (`fetch_rss.py`, `fetch_nse_announcements.py`, `fetch_sebi.py`),
matches each item against a watchlist + macro/regulatory keyword list
(`matcher.py`, `config.py`), and sends a filtered Telegram alert for anything
that matches (`news_alert.py`) — not a firehose of every item fetched.

MODI7 reuses this same fetch/match approach (with its own copy of these
files) but adds fundamentals, a red-flag category, and a persistent SQLite
history — see [MODI7's README](https://github.com/saiqulmodi/MODI7#readme)
for that richer version.

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

## Running

```bash
python news_alert.py
```

Or register `run_news_alert.bat` as a Windows Task Scheduler job (the
project's own convention runs it every 15 minutes). Already-alerted items
are tracked in `news_alerted_state.json` (gitignored, regenerates locally)
so reruns don't resend the same alert.
