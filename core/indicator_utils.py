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


# core/indicator_utils.py

def calculate_atr(df, period=21):
    """
    Calculate the Average True Range (ATR) with smoothing and NaN protection.
    """
    if df is None or len(df) < period:
        print("⚠️ Not enough candles to calculate ATR.")
        return 0.0

    try:
        df = df.copy()  # avoid modifying original
        df["H-L"] = df["high"] - df["low"]
        df["H-C"] = abs(df["high"] - df["close"].shift())
        df["L-C"] = abs(df["low"] - df["close"].shift())
        df["TR"] = df[["H-L", "H-C", "L-C"]].max(axis=1)
        df["ATR"] = df["TR"].rolling(window=period).mean()

        atr_val = df["ATR"].iloc[-1]
        if pd.isna(atr_val) or atr_val <= 0:
            print("⚠️ Invalid ATR result — returning 0.0")
            return 0.0

        return round(atr_val, 5)
    except Exception as e:
        print(f"❌ ATR calculation error: {e}")
        return 0.0


