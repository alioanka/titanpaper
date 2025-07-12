from binance.client import Client
import pandas as pd


def get_historical_data(symbol, interval, lookback, api_key, api_secret):
    client = Client(api_key, api_secret)
    klines = client.get_historical_klines(symbol, interval, lookback)
    df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_vol', 'trades', 'tb_base_vol', 'tb_quote_vol', 'ignore'])
    df['open'] = pd.to_numeric(df['open'])
    df['high'] = pd.to_numeric(df['high'])
    df['low'] = pd.to_numeric(df['low'])
    df['close'] = pd.to_numeric(df['close'])
    return df
