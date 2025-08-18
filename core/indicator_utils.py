# core/indicator_utils.py
from binance.client import Client
import os
import pandas as pd

client = Client(api_key=os.getenv("BINANCE_API_KEY"), api_secret=os.getenv("BINANCE_API_SECRET"))

def fetch_recent_candles(symbol, interval="5m", limit=100):
    try:
        klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
        df = pd.DataFrame(klines, columns=[
            "timestamp","open","high","low","close","volume",
            "close_time","quote_asset_volume","num_trades",
            "taker_buy_base","taker_buy_quote","ignore"
        ])
        return df[["open","high","low","close"]].astype(float)
    except Exception as e:
        print(f"❌ fetch_recent_candles error: {e}")
        return pd.DataFrame(columns=["open","high","low","close"]).astype(float)

def calculate_atr(df: pd.DataFrame, period: int = 14) -> float:
    try:
        if df is None or df.empty:
            return 0.0
        d = df.copy()
        d["H-L"] = d["high"] - d["low"]
        d["H-C"] = (d["high"] - d["close"].shift()).abs()
        d["L-C"] = (d["low"]  - d["close"].shift()).abs()
        d["TR"]  = d[["H-L","H-C","L-C"]].max(axis=1)
        d["ATR"] = d["TR"].rolling(window=period).mean()
        atr_val = float(d["ATR"].iloc[-1])
        if pd.isna(atr_val) or atr_val <= 0:
            return 0.0
        return round(atr_val, 5)
    except Exception as e:
        print(f"❌ ATR calculation error: {e}")
        return 0.0
