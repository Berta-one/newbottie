import pandas as pd
import xgboost as xgb
import joblib

def train_xgb(data_path='sample_data/historical_data.csv'):
    df = pd.read_csv(data_path)
    features = ['rsi', 'macd', 'atr']
    target = 'label'

    df = df.dropna()
    X = df[features]
    y = df[target]

    model = xgb.XGBClassifier()
    model.fit(X, y)

    joblib.dump(model, 'models/xgb_model.pkl')
    print("XGBoost model trained and saved to models/xgb_model.pkl")
