"""
Fetches current-day volume and 50-day average volume per symbol for
volume_alert.py. yfinance is the primary source (no credentials needed,
works out of the box). Angel One's SmartAPI is an optional fallback for
symbols yfinance couldn't resolve, used only when ANGEL_API_KEY /
ANGEL_CLIENT_CODE / ANGEL_PASSWORD / ANGEL_TOTP_SECRET are all set in the
environment -- untested against a live Angel account since no credentials
were available while writing this; it degrades to "no fallback" silently
if login fails or the env vars aren't set.
"""

import os
import time
from datetime import datetime, timedelta

import yfinance as yf

AVG_WINDOW = 50
LOOKBACK_PERIOD = "80d"  # enough trading days to get 50 completed daily bars

_angel_client = None
_angel_token_map = None


def fetch_volumes_yfinance(symbols):
    """Returns {symbol: (current_volume, avg_volume_50d)} for symbols
    yfinance could resolve; symbols it couldn't are absent from the result."""
    results = {}
    chunk_size = 100  # a single request for 400+ tickers is unreliable
    for i in range(0, len(symbols), chunk_size):
        chunk = symbols[i:i + chunk_size]
        tickers = [s + ".NS" for s in chunk]
        try:
            data = yf.download(
                tickers=tickers,
                period=LOOKBACK_PERIOD,
                interval="1d",
                group_by="ticker",
                threads=True,
                progress=False,
                auto_adjust=False,
            )
        except Exception as e:
            print(f"yfinance batch fetch failed for a chunk: {e}")
            continue

        for symbol, ticker in zip(chunk, tickers):
            try:
                # group_by="ticker" always puts the ticker as the top MultiIndex
                # level, even for a single-ticker request -- there's no flat-
                # columns case to special-case here.
                vol = data[ticker]["Volume"].dropna()
                if len(vol) < 2:
                    continue
                current_volume = float(vol.iloc[-1])
                history = vol.iloc[:-1].tail(AVG_WINDOW)
                if history.empty:
                    continue
                results[symbol] = (current_volume, float(history.mean()))
            except Exception:
                continue
    return results


def _get_angel_client():
    global _angel_client
    if _angel_client is not None:
        return _angel_client

    api_key = os.environ.get("ANGEL_API_KEY")
    client_code = os.environ.get("ANGEL_CLIENT_CODE")
    password = os.environ.get("ANGEL_PASSWORD")
    totp_secret = os.environ.get("ANGEL_TOTP_SECRET")
    if not all([api_key, client_code, password, totp_secret]):
        return None

    try:
        from SmartApi import SmartConnect
        import pyotp

        client = SmartConnect(api_key=api_key)
        client.generateSession(client_code, password, pyotp.TOTP(totp_secret).now())
        _angel_client = client
    except Exception as e:
        print(f"Angel One login failed, skipping Angel fallback: {e}")
        _angel_client = None
    return _angel_client


def _get_angel_token_map():
    global _angel_token_map
    if _angel_token_map is not None:
        return _angel_token_map

    import requests

    url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        token_map = {}
        for row in resp.json():
            symbol = row.get("symbol", "")
            if row.get("exch_seg") == "NSE" and symbol.endswith("-EQ"):
                token_map[symbol[:-3]] = row["token"]
        _angel_token_map = token_map
    except Exception as e:
        print(f"Failed to load Angel scrip master: {e}")
        _angel_token_map = {}
    return _angel_token_map


def fetch_volumes_angel(symbols):
    """Best-effort fallback via Angel One SmartAPI. Returns {} entirely if
    Angel credentials aren't configured or login fails."""
    client = _get_angel_client()
    if client is None:
        return {}

    token_map = _get_angel_token_map()
    to_date = datetime.now()
    from_date = to_date - timedelta(days=110)

    results = {}
    for symbol in symbols:
        token = token_map.get(symbol)
        if not token:
            continue
        try:
            params = {
                "exchange": "NSE",
                "symboltoken": token,
                "interval": "ONE_DAY",
                "fromdate": from_date.strftime("%Y-%m-%d %H:%M"),
                "todate": to_date.strftime("%Y-%m-%d %H:%M"),
            }
            candles = client.getCandleData(params).get("data") or []
            if len(candles) < 2:
                continue
            volumes = [row[5] for row in candles]  # [timestamp, o, h, l, c, volume]
            current_volume = float(volumes[-1])
            history = volumes[:-1][-AVG_WINDOW:]
            if not history:
                continue
            results[symbol] = (current_volume, sum(history) / len(history))
            time.sleep(0.35)  # stay under Angel's per-second rate limit
        except Exception:
            continue
    return results


def fetch_volumes(symbols):
    """Returns {symbol: (current_volume, avg_volume_50d)}, trying yfinance
    first and falling back to Angel One for whatever it couldn't resolve."""
    results = fetch_volumes_yfinance(symbols)
    missing = [s for s in symbols if s not in results]
    if missing:
        results.update(fetch_volumes_angel(missing))
    return results
