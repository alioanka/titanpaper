import pandas as pd
import ta

def build_features(df):
    df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], window=14).average_true_range()
    df['trend_strength'] = ta.trend.ADXIndicator(df['high'], df['low'], df['close'], window=14).adx()
    df['volatility'] = df['close'].pct_change().rolling(window=14).std()
    return df[['atr', 'trend_strength', 'volatility']]
