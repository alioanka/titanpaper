from binance.client import Client
import os
import pandas as pd

client = Client(api_key=os.getenv("BINANCE_API_KEY"), api_secret=os.getenv("BINANCE_API_SECRET"))

def fetch_recent_candles(symbol, interval="5m", limit=100):
    try:
        klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
        df = pd.DataFrame(klines, columns=[
            "timestamp", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "num_trades",
            "taker_buy_base", "taker_buy_quote", "ignore"
        ])
        df = df[["high", "low", "close"]].astype(float)
        return df
    except Exception as e:
        print(f"❌ Failed to fetch historical candles for {symbol}: {e}")
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


