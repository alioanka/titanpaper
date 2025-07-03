# core/indicator_utils.py

import requests
import pandas as pd

def fetch_recent_candles(symbol, interval="1m", limit=20):
    """
    Fetch recent candles for indicator calculations (e.g. ATR).
    """
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }

    try:
        res = requests.get(url, params=params, timeout=5)
        data = res.json()

        df = pd.DataFrame(data, columns=[
            "timestamp", "open", "high", "low", "close", "volume",
            "_", "_", "_", "_", "_", "_"
        ])
        df["open"] = df["open"].astype(float)
        df["high"] = df["high"].astype(float)
        df["low"] = df["low"].astype(float)
        df["close"] = df["close"].astype(float)

        return df

    except Exception as e:
        print(f"❌ Failed to fetch recent candles for {symbol}: {e}")
        return None


def calculate_atr(df, period=14):

    if len(df) < period:
        print("⚠️ Not enough data to calculate ATR.")
        return 0.0
    """
    Calculate ATR (Average True Range) for a given dataframe.
    """
    df["H-L"] = df["high"] - df["low"]
    df["H-C"] = abs(df["high"] - df["close"].shift())
    df["L-C"] = abs(df["low"] - df["close"].shift())
    df["TR"] = df[["H-L", "H-C", "L-C"]].max(axis=1)
    df["ATR"] = df["TR"].rolling(window=period).mean()
    return df["ATR"].iloc[-1]
