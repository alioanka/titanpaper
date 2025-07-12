import pandas as pd
import ta

def build_features(df):
    df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], window=14).average_true_range()
    df['adx'] = ta.trend.ADXIndicator(df['high'], df['low'], df['close'], window=14).adx()
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    df['macd'] = ta.trend.MACD(df['close']).macd_diff()
    df['volatility'] = df['close'].pct_change().rolling(window=14).std()
    return df[['atr', 'adx', 'rsi', 'macd', 'volatility']]
