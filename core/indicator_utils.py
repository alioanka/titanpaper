# core/indicator_utils.py
import os
import pandas as pd

try:
    from binance.client import Client
except Exception:
    Client = None  # allow import even if lib missing (handled below)

_client = None

def _strip_env(s: str) -> str:
    if s is None:
        return ""
    # Remove surrounding spaces and Windows CRs
    return s.strip().replace("\r", "").replace("\n", "")

def _get_client():
    """
    Lazy, safe Binance Client constructor:
    - Strips CR/LF/whitespace from keys.
    - If keys absent/invalid or library missing, returns a no-op public client (if possible).
    """
    global _client
    if _client is not None:
        return _client

    if Client is None:
        raise RuntimeError("python-binance not installed. Please `pip install python-binance`.")

    key = _strip_env(os.getenv("BINANCE_API_KEY"))
    secret = _strip_env(os.getenv("BINANCE_API_SECRET"))

    try:
        if key and secret:
            _client = Client(api_key=key, api_secret=secret)
        else:
            # Public-only client for market data (klines don’t need auth)
            _client = Client()
    except Exception as e:
        # As a last resort, try an unauthenticated client for public endpoints
        try:
            _client = Client()
        except Exception as e2:
            raise RuntimeError(f"Failed to initialize Binance client: {e} | {e2}")

    return _client

def fetch_recent_candles(symbol, interval="5m", limit=100):
    """
    Returns a DataFrame with columns ['open','high','low','close'] as floats.
    Uses public klines endpoint; auth not required.
    """
    try:
        client = _get_client()
        klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
        df = pd.DataFrame(klines, columns=[
            "timestamp","open","high","low","close","volume",
            "close_time","quote_asset_volume","num_trades",
            "taker_buy_base","taker_buy_quote","ignore"
        ])
        if df.empty:
            return pd.DataFrame(columns=["open","high","low","close"]).astype(float)
        return df[["open","high","low","close"]].astype(float)
    except Exception as e:
        print(f"❌ fetch_recent_candles error [{symbol}]: {e}")
        return pd.DataFrame(columns=["open","high","low","close"]).astype(float)

def calculate_atr(df: pd.DataFrame, period: int = 14) -> float:
    """
    Simple ATR (SMA of True Range). Returns 0.0 if insufficient rows or invalid.
    """
    try:
        if df is None or df.empty:
            return 0.0
        d = df.copy()
        d["H-L"] = d["high"] - d["low"]
        d["H-C"] = (d["high"] - d["close"].shift()).abs()
        d["L-C"] = (d["low"]  - d["close"].shift()).abs()
        d["TR"]  = d[["H-L","H-C","L-C"]].max(axis=1)
        d["ATR"] = d["TR"].rolling(window=period).mean()
        val = float(d["ATR"].iloc[-1])
        if pd.isna(val) or val <= 0:
            return 0.0
        return round(val, 5)
    except Exception as e:
        print(f"❌ ATR calculation error: {e}")
        return 0.0
