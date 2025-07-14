import pandas as pd
import ta

def build_features(df):
    # Core indicators
    df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], window=14).average_true_range()
    df['adx'] = ta.trend.ADXIndicator(df['high'], df['low'], df['close'], window=14).adx()
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    df['macd'] = ta.trend.MACD(df['close']).macd_diff()

    # EMA ratio (fast vs slow)
    ema_fast = ta.trend.EMAIndicator(df['close'], window=12).ema_indicator()
    ema_slow = ta.trend.EMAIndicator(df['close'], window=26).ema_indicator()
    df['ema_ratio'] = ema_fast / ema_slow

    # Volatility (stddev of returns)
    df['volatility'] = df['close'].pct_change().rolling(window=14).std()

    # Clean up: fill NaN
    df = df.fillna(method='bfill').fillna(0)

    return df[['atr', 'adx', 'rsi', 'macd', 'ema_ratio', 'volatility']]
