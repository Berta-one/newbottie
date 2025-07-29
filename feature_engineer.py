
import pandas as pd

def engineer_features(df):
    df['return_1h'] = df['close'].pct_change(periods=1)
    df['return_24h'] = df['close'].pct_change(periods=24)
    df['volatility'] = df['close'].rolling(window=24).std()
    df['rsi'] = df['close'].rolling(window=14).mean()
    df['atr'] = df['high'] - df['low']
    df = df.dropna()
    return df
