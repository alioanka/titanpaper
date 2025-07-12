import os
from binance.client import Client
from dotenv import load_dotenv

load_dotenv()


def get_latest_candle(symbol, interval="5m"):
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    client = Client(api_key, api_secret)

    candles = client.get_klines(symbol=symbol, interval=interval, limit=1)
    if candles:
        c = candles[0]
        return {
            'open': float(c[1]),
            'high': float(c[2]),
            'low': float(c[3]),
            'close': float(c[4]),
            'volume': float(c[5]),
            'volatility': abs(float(c[2]) - float(c[3])) / float(c[4])
        }
    return None

