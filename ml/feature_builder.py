import pandas as pd
import ta

def build_features(df):
    df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], window=14).average_true_range()
    df['adx'] = ta.trend.ADXIndicator(df['high'], df['low'], df['close'], window=14).adx()
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    df['macd'] = ta.trend.MACD(df['close']).macd_diff()
    ema_fast = ta.trend.EMAIndicator(df['close'], window=12).ema_indicator()
    ema_slow = ta.trend.EMAIndicator(df['close'], window=26).ema_indicator()
    df['ema_ratio'] = ema_fast / ema_slow
    df['volatility'] = df['close'].pct_change().rolling(window=14).std()
    df = df.bfill().fillna(0)
    return df[['atr', 'adx', 'rsi', 'macd', 'ema_ratio', 'volatility']]
