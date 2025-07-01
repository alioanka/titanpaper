# data/price_feed.py

import requests

def get_latest_candle(symbol, interval="1m"):
    """
    Fetches the most recent closed candle for a given symbol and interval.
    """
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 2  # Get last 2 to ensure last one is closed
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        data = response.json()

        if len(data) < 2:
            return None

        # Use the last fully closed candle
        kline = data[-2]
        candle = {
            "timestamp": int(kline[0]),
            "open": float(kline[1]),
            "high": float(kline[2]),
            "low": float(kline[3]),
            "close": float(kline[4]),
            "volume": float(kline[5])
        }
        return candle

    except Exception as e:
        print(f"❌ Error fetching price for {symbol}: {e}")
        return None
